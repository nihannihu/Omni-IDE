import json
import logging
import time
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Callable
from intelligence_core import IntelligenceCore

logger = logging.getLogger(__name__)

# =====================================================================
# ABSTRACT BASE AGENT
# =====================================================================
class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def build_prompt(self, user_task: str, context: str) -> str:
        """Construct the specialized prompt for this agent."""
        pass

    @abstractmethod
    def parse_response(self, text: str) -> Tuple[bool, Any]:
        """Parse and validate the LLM's raw response string."""
        pass

    def run(self, user_task: str, context: str, llm_runner: Callable[[str], str]) -> Any:
        prompt = self.build_prompt(user_task, context)
        
        start_time = time.time()
        raw_response = llm_runner(prompt)
        duration = (time.time() - start_time) * 1000
        
        logger.info(f"[AGENT: {self.name}] LLM Roundtrip: {duration:.1f}ms")
        
        is_valid, parsed_data = self.parse_response(raw_response)
        if not is_valid:
            logger.warning(f"[VALIDATION FAILED - {self.name}] Falling back to raw text.")
            return {"error": "Validation failed", "raw_fallback": raw_response}
            
        return parsed_data

# =====================================================================
# SPECIALIZED AGENTS
# =====================================================================
class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("PlannerAgent")

    def build_prompt(self, user_task: str, context: str) -> str:
        return f"""
[WORKSPACE CONTEXT]
{context}

[PLANNER AGENT INSTRUCTIONS]
You are the Lead Architect. Break down the following high-level feature request into structured implementation steps.
Request: "{user_task}"

You MUST output ONLY valid JSON matching this exact schema:
{{
  "goal": "Brief summary",
  "tasks": [
    {{"title": "Task name", "description": "Details", "files": ["app.py"], "priority": 1}}
  ],
  "risks": ["Risk 1"],
  "estimated_complexity": "low|medium|high"
}}
"""

    def parse_response(self, text: str) -> Tuple[bool, Any]:
        try:
            # Extract JSON if wrapped in markdown
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
            json_str = match.group(1) if match else text
            data = json.loads(json_str)
            
            # Very basic schema validation
            if all(k in data for k in ("goal", "tasks", "risks", "estimated_complexity")):
                return True, data
            return False, text
        except Exception as e:
            return False, text

class DebugAgent(BaseAgent):
    def __init__(self):
        super().__init__("DebugAgent")

    def build_prompt(self, user_task: str, context: str) -> str:
        return f"""
[WORKSPACE CONTEXT]
{context}

[DEBUG AGENT INSTRUCTIONS]
You are a Staff Debugging Engineer. The user encountered an error or needs deep technical debugging.
Issue: "{user_task}"

Analyze the stack trace/issue above alongside the workspace context.
Provide:
1. Root cause summary.
2. Step-by-step fix.
3. Call the `safe_write` tool to patch the file if you are highly confident.
"""

    def parse_response(self, text: str) -> Tuple[bool, Any]:
        # Debug agent returns natural language with tool calls, no strict JSON validation required.
        return True, {"raw_response": text}

class ReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReviewAgent")

    def build_prompt(self, user_task: str, context: str) -> str:
        return f"""
[WORKSPACE CONTEXT]
{context}

[CODE REVIEW AGENT INSTRUCTIONS]
You are a Principal Code Reviewer evaluating the target file/concept.
Target: "{user_task}"

You MUST output ONLY valid JSON matching this exact schema:
{{
  "summary": "Brief analysis",
  "issues": ["Issue 1"],
  "suggestions": ["Suggestion 1"],
  "score": 85
}}
"""

    def parse_response(self, text: str) -> Tuple[bool, Any]:
        try:
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
            json_str = match.group(1) if match else text
            data = json.loads(json_str)
            if all(k in data for k in ("summary", "issues", "suggestions", "score")):
                return True, data
            return False, text
        except Exception:
            return False, text

# =====================================================================
# AGENT ORCHESTRATOR
# =====================================================================
class AgentOrchestrator:
    def __init__(self, core: IntelligenceCore):
        self.core = core
        self.agents = {
            "/plan": PlannerAgent(),
            "/debug": DebugAgent(),
            "/review": ReviewAgent(),
        }

    def _update_agent_memory(self, agent_name: str, run_data: Any):
        """Append the structured outputs of agents to the extended memory state."""
        mem = self.core.load_memory()
        
        # Ensure memory arrays exist
        if "planner_runs" not in mem: mem["planner_runs"] = []
        if "debug_sessions" not in mem: mem["debug_sessions"] = []
        if "reviews" not in mem: mem["reviews"] = []
        
        if agent_name == "PlannerAgent":
            mem["planner_runs"].append(run_data)
            mem["planner_runs"] = mem["planner_runs"][-5:]
        elif agent_name == "DebugAgent":
             # Only save summaries for debug to save space
             summary = str(run_data)[:200] + "..." if len(str(run_data)) > 200 else str(run_data)
             mem["debug_sessions"].append(summary)
             mem["debug_sessions"] = mem["debug_sessions"][-5:]
        elif agent_name == "ReviewAgent":
             mem["reviews"].append(run_data)
             mem["reviews"] = mem["reviews"][-5:]
             
        self.core.save_memory(mem)

    def route_and_execute(self, command: str, user_task: str, llm_runner: Callable[[str], str]) -> Tuple[str, str]:
        """
        Routes the intent to the specialized agent. 
        Returns (agent_name, final_response_text_to_yield).
        """
        agent = self.agents.get(command)
        if not agent:
            return "Router", f"No agent mapping found for command: {command}"

        start_time = time.time()
        logger.info(f"[ROUTER] -> {agent.name} Activated.")
        
        # 1. Assemble tight Context limit for agents (12k chars target)
        context = self.core.get_workspace_context(max_files=10, max_chars_per_file=1200)
        logger.info(f"[PROMPT SIZE] {len(context)} chars")

        # 2. Run the agent natively
        result_data = agent.run(user_task, context, llm_runner)

        # 3. Handle output formatting and memory updates
        final_text = ""
        if isinstance(result_data, dict):
            if "error" in result_data:
                # Validation Fallback
                logger.warning(f"[VALIDATION FALLBACK] Formatting failed natively. Emitting Raw NL.")
                final_text = f"⚙️ *{agent.name} Response (Unstructured):*\n\n{result_data.get('raw_fallback', '')}"
            elif agent.name == "DebugAgent":
                self._update_agent_memory(agent.name, result_data)
                final_text = str(result_data.get("raw_response", ""))
            else:
                # Successfully parsed JSON structured output
                self._update_agent_memory(agent.name, result_data)
                
                if agent.name == "PlannerAgent":
                    final_text = f"### 🗺️ Architecture Plan: {result_data.get('goal')}\n"
                    final_text += f"**Complexity:** {result_data.get('estimated_complexity', 'N/A').upper()}\n\n"
                    final_text += "**Tasks:**\n"
                    for t in result_data.get('tasks', []):
                        final_text += f"- **[{t.get('priority', 1)}] {t.get('title', 'Task')}**: {t.get('description', '')} (Files: {', '.join(t.get('files', []))})\n"
                    final_text += "\n**Risks:**\n"
                    for r in result_data.get('risks', []):
                        final_text += f"- {r}\n"
                        
                elif agent.name == "ReviewAgent":
                    score = result_data.get('score', 'N/A')
                    final_text = f"### 🕵️ Code Review (Score: {score}/100)\n"
                    final_text += f"{result_data.get('summary', '')}\n\n**Issues Detected:**\n"
                    for i in result_data.get('issues', []):
                        final_text += f"- ⚠️ {i}\n"
                    final_text += "\n**Suggestions:**\n"
                    for s in result_data.get('suggestions', []):
                        final_text += f"- 💡 {s}\n"

        else:
            final_text = str(result_data)

        total_exec = (time.time() - start_time) * 1000
        logger.info(f"[EXECUTION TIME - {agent.name}] {total_exec:.1f}ms")

        # Log completion banner for terminal observation
        banner = f"\n[AGENT ORCHESTRATOR]\n→ {agent.name} Activated\n→ Context Size: {len(context)} chars\n→ Response Parsed Successfully\n"
        print(banner)

        return agent.name, final_text
