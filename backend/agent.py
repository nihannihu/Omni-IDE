import logging
import re
import os
import sys
from threading import Thread, Lock as ThreadLock
from dotenv import load_dotenv
load_dotenv(override=True)  # ALWAYS load fresh key from .env

# Lightweight Agent Framework
from smolagents import CodeAgent, Tool, InferenceClientModel, ChatMessage, MessageRole, ChatMessageStreamDelta, ActionStep, ToolCall, ToolOutput, FinalAnswerStep
from smolagents.models import get_clean_message_list
import smolagents.utils as smolagents_utils

# API Client for Vision & Chat
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()
hf_token = os.getenv("HUGGINGFACE_API_KEY")

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# SECURITY SANDBOX & FILE SYSTEM WRAPPERS
# ------------------------------------------------------------------

# This is set by main.py when the user changes directory
WORKING_DIRECTORY = None

def get_desktop_path():
    from pathlib import Path
    return Path(r"C:\Users\nihan\Desktop")

def get_base_path():
    """Returns WORKING_DIRECTORY. Raises error if no folder is open."""
    from pathlib import Path
    if WORKING_DIRECTORY:
        return Path(WORKING_DIRECTORY)
    raise ValueError("No folder is open. Please open a folder first using the Open Folder button.")

def safe_write(filename: str, content: str) -> str:
    """Safely writes content to a file. Phase 4.5: Intercepts writes for Diff Staging."""
    base = get_base_path()
    filename = filename.lstrip("/").lstrip("\\")
    filepath = (base / filename).resolve()
    
    if not str(filepath).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Path Traversal): {filename}")
        
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Phase 5 Diff Staging Hook
    from diff_staging_layer import DiffStagingLayer
    layer = DiffStagingLayer(str(base))
    patch_result = layer.create_patch(str(filepath), content)
    
    if "error" in patch_result:
        logger.error(f"[ROLLBACK] Patch proposal failed: {patch_result['error']}")
        return f"ERROR: {patch_result['error']}"
        
    if patch_result.get("status") == "unchanged":
        logger.info(f"safe_write: {filename} was unchanged.")
        return str(filepath)
        
    # If the file exists and is being heavily modified, stage it.
    if patch_result.get("action") == "modify":
        session_id = patch_result.get("session_id")
        logger.warning(f"[STAGING] {filename} modification intercepted. Session ID: {session_id}")
        # For agent loop feedback, tell it the write succeeded but is Pending Approval
        return f"File '{filename}' staged for user approval. Session ID: {session_id}"
        
    # If it's a completely new file creation, write it instantly to not slow down scaffolding
    filepath.write_text(content, encoding='utf-8')
    logger.info(f"safe_write: Created entirely new file {filepath}")
    return str(filepath)

def safe_open(filepath_str, mode='r', **kwargs):
    """Safe wrapper for open() rooted to WORKING_DIRECTORY."""
    from pathlib import Path
    import builtins
    base = get_base_path()
    filepath = Path(filepath_str)
    
    if not filepath.is_absolute():
        filepath = base / filepath
    filepath = filepath.resolve()
    
    if any(m in mode for m in ('w', 'a', 'x')) and not str(filepath).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Write Outside Sandbox): {filepath}")
        
    if any(m in mode for m in ('w', 'a', 'x')):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
    return builtins.open(str(filepath), mode, **kwargs)

def safe_mkdir(path_str, *args, **kwargs):
    """Safe wrapper for directory creation rooted to WORKING_DIRECTORY."""
    from pathlib import Path
    base = get_base_path()
    path = Path(path_str)
    
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    
    if not str(path).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (mkdir Outside Sandbox): {path}")
    
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

def safe_delete(filename):
    """Delete a file from the working directory (sandboxed)."""
    from pathlib import Path
    import os
    base = get_base_path()
    path = Path(filename)
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    
    if not str(path).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Delete Outside Sandbox): {path}")
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if path.is_file():
        os.remove(path)
        logger.info(f"Deleted file: {path}")
        return f"Deleted: {filename}"
    elif path.is_dir():
        import shutil
        shutil.rmtree(path)
        logger.info(f"Deleted directory: {path}")
        return f"Deleted directory: {filename}"
    else:
        raise ValueError(f"Cannot delete: {path}")

def open_in_browser(filepath_str):
    """Opens a file in the default web browser (Desktop rooted)."""
    import webbrowser as wb
    from pathlib import Path
    desktop = get_desktop_path()
    filepath = Path(filepath_str)
    
    if not filepath.is_absolute():
        filepath = desktop / filepath
    filepath = filepath.resolve()
    
    wb.open(filepath.as_uri())
    return str(filepath)

def create_web_page(folder_name: str, page_type: str = "landing", title: str = "My Page", theme: str = "dark") -> str:
    """
    Generates professional HTML/CSS templates for standard pages.
    """
    folder_path = safe_mkdir(folder_name)
    from pathlib import Path
    folder = Path(folder_path)
    
    bg = "#0f0f1a" if theme == "dark" else "#f0f2f5"
    text = "#e0e0e0" if theme == "dark" else "#333333"
    accent = "#6c63ff"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ background: {bg}; color: {text}; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .container {{ text-align: center; padding: 40px; border: 1px solid {accent}; border-radius: 10px; }}
        h1 {{ color: {accent}; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>Generated by Omni-Agent Studio ({page_type})</p>
    </div>
</body>
</html>"""

    (folder / "index.html").write_text(html_content, encoding='utf-8')
    return open_in_browser(str(folder / "index.html"))

# ------------------------------------------------------------------
# VISION TOOL (SERVERLESS)
# ------------------------------------------------------------------

class VisionTool(Tool):
    name = "analyze_screen"
    description = "Analyze the latest screen frame to answer a question. Use this tool when the user asks you to 'see', 'look', or describe what is on the screen."
    inputs = {
        "question": {
            "type": "string",
            "description": "The question to ask about the screen content (e.g., 'What do you see?', 'Read the error')."
        }
    }
    output_type = "string"

    def __init__(self, get_image_func, **kwargs):
        super().__init__(**kwargs)
        self.get_image_func = get_image_func
        # Use Hugging Face Inference API for Vision
        self.client = InferenceClient(token=os.getenv("HUGGINGFACE_API_KEY"))

    def forward(self, question: str) -> str:
        try:
            image_data = self.get_image_func()
            if not image_data:
                return "No screen frame available. Ask the user to verify screen sharing is on."
            
            # Clean base64 string
            if "," in image_data:
                 image_data = image_data.split(",")[1]
            
            logger.info(f"VisionTool: Analyzing screen with question: '{question}' (Cloud Vision)")
            
            # Use Qwen2.5-VL-7B-Instruct or Llama-3.2-11B-Vision
            # Trying Qwen/Qwen2.5-VL-7B-Instruct first as it matches our Coder model family
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                        {"type": "text", "text": question}
                    ]
                }
            ]
            
            response = self.client.chat_completion(
                model="Qwen/Qwen2.5-VL-7B-Instruct",
                messages=messages,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            logger.info(f"VisionTool Result: {result[:50]}...")
            return f"Screen Insight: {result}"
            
        except Exception as e:
            logger.error(f"VisionTool Error: {e}")
            return f"Error analyzing screen: {str(e)}"

# ------------------------------------------------------------------
# OMNI AGENT (CLOUD BRAIN)
# ------------------------------------------------------------------

class OmniAgent:
    def __init__(self):
        logger.info("Initializing Cloud Brain (Qwen2.5-Coder-32B)...")
        
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            logger.error("CRITICAL: HUGGINGFACE_API_KEY missing!")
        
        # Vision Caching
        self.image_lock = ThreadLock()
        self.latest_image = None
        
        def get_latest_image():
            with self.image_lock:
                return self.latest_image
        
        self.vision_tool = VisionTool(get_latest_image)
        
        # PROMPT: Ultra-Aggressive Direct Execution Engine
        SYSTEM_PROMPT = r"""
You are a Senior Full-Stack Developer and AI Coding Engine, created by Nihan Nihu.
CRITICAL RULE: You are a File Creation Engine.
When generating code, you MUST immediately write it to the disk using pathlib.

CORRECT PATTERN:
from pathlib import Path
Path('index.html').write_text('...content...', encoding='utf-8')

INCORRECT PATTERN (DO NOT DO THIS):
html_content = '...content...' # This is useless! Write it to disk!

If asked "Who created you?", answer "I was created by Nihan Nihu."

=== ABSOLUTE RULES (VIOLATION = FAILURE) ===

RULE 1 - FILE CREATION (when user says "create", "make", "build"):
  - Call `safe_write(filename, content)` DIRECTLY with the full file content.
  - DO NOT assign to variables. DO NOT show in markdown blocks.
  - After writing: `final_answer("DONE: filename1.html, filename2.css")`

RULE 2 - FILE EDITING (when user says "edit", "modify", "add", "change", "update", "fix"):
  THIS IS THE MOST IMPORTANT RULE. To EDIT an existing file you MUST:
  Step 1: READ the existing file content:
    `existing = safe_open("filename.html", "r").read()`
  Step 2: MODIFY the content (add/change/remove what the user requested)
  Step 3: WRITE the modified content back:
    `safe_write("filename.html", modified_content)`
  Step 4: `final_answer("DONE: filename.html")`
  
  WARNING: You MUST include ALL the original content plus your changes.
  If you only write new content, you will DELETE the original file content!

RULE 3 - RESPONSE FORMAT (MANDATORY):
  - ALWAYS end with: `final_answer("DONE: file1.ext, file2.ext")`
  - List ALL files you created or modified.
  - NEVER say just "Done!" — you MUST include the filenames after "DONE:"

RULE 4 - TOOLS AVAILABLE:
  - `safe_write(filename, content)` - Create or overwrite a file
  - `safe_open(path, mode)` - Open/read a file (mode="r" for reading)
  - `safe_delete(filename)` - Delete a file or directory
  - `safe_mkdir(dirname)` - Create a directory
  - `analyze_screen(question)` - See the user's screen

RULE 5 - FILE DELETION (when user says "delete", "remove"):
  - Call `safe_delete(filename)` for each file to delete.
  - After deleting: `final_answer("DELETED: filename1.html, filename2.css")`

=== CORRECT EXAMPLES ===

EXAMPLE 1 - CREATE new files:
User: "Create a login page"
```python
safe_write("login.html", '''<!DOCTYPE html>
<html><head><title>Login</title><link rel="stylesheet" href="style.css"></head>
<body><div class="container"><h1>Login</h1>
<form><input type="email" placeholder="Email"><input type="password" placeholder="Password">
<button type="submit">Sign In</button></form></div></body></html>''')

safe_write("style.css", '''body { background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: sans-serif; }
.container { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 40px; border-radius: 16px; }
button { padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; }''')

final_answer("DONE: login.html, style.css")
```

EXAMPLE 2 - EDIT an existing file:
User: "Edit login.html, add a Register button and make buttons blue"
```python
# Step 1: READ existing content
existing_html = safe_open("login.html", "r").read()

# Step 2: MODIFY - replace the closing </form> with new button + closing tag
modified_html = existing_html.replace(
    '</form>',
    '<button type="button" class="register-btn">Register</button>\n</form>'
)

# Step 3: WRITE back
safe_write("login.html", modified_html)

# Also update CSS
existing_css = safe_open("style.css", "r").read()
modified_css = existing_css + '''
.register-btn { padding: 12px; background: #2196F3; color: white; border: none; border-radius: 8px; cursor: pointer; margin-top: 10px; width: 100%; }
button { background: #2196F3 !important; }'''
safe_write("style.css", modified_css)

final_answer("DONE: login.html, style.css")
```

=== WRONG (NEVER DO THIS) ===
```python
html = '''<!DOCTYPE html>...'''  # WRONG! Do not assign to variables!
print(content)                    # WRONG! Do not print content!
final_answer("Done!")             # WRONG! Must include filenames: "DONE: file.html"
```
"""
        try:
            # Using a more widely available model for free-tier resilience
            # CRITICAL: We MUST explicitly limit max_tokens. smolagents defaults 
            # to a massive token request that instantly forces HuggingFace to route
            # to the paid Inference Providers tier (giving a 402 Error).
            self.model = InferenceClientModel(
                model_id="Qwen/Qwen2.5-Coder-32B-Instruct", 
                token=api_key,
                max_tokens=1500
            )
            
            # CRITICAL: Do NOT pass tools=[self.vision_tool] here!
            # HuggingFace Free Tier instantly throws a 402 Payment Required error if ANY
            # native 'tools' schema is sent in the API payload. 
            # We inject the Vision tool directly into the Python executor environment below.
            self.agent = CodeAgent(
                tools=[], 
                model=self.model, 
                add_base_tools=True,
                max_steps=10, 
                verbosity_level=logging.INFO,
                instructions=SYSTEM_PROMPT,
                additional_authorized_imports=["datetime", "math", "random", "time", "json", "re"],
                stream_outputs=True,
                executor_kwargs={
                    "additional_functions": {
                        "safe_write": safe_write,
                        "safe_open": safe_open,
                        "safe_delete": safe_delete,
                        "safe_mkdir": safe_mkdir,
                        "open_in_browser": open_in_browser,
                        "create_web_page": create_web_page,
                        "VisionTool": VisionTool
                    }
                }
            )
            logger.info("Cloud Brain initialized successfully.")
            
        except Exception as e:
            if "402" in str(e):
                logger.error("HuggingFace Inference API quota exhausted (402).")
            else:
                logger.error(f"Failed to initialize AI Agent: {e}")
            raise e

    def update_vision_context(self, base64_image: str):
        with self.image_lock:
            # logger.debug("Updated latest screen frame")
            self.latest_image = base64_image

    def execute_stream(self, task: str):
        """Execute a task context-aware and yield ONLY the clean final answer to the frontend."""
        logger.info(f"Agent task received: {task}")
        final_answer = None
        
        # --- PHASE 3: INTELLIGENCE CORE WIRING ---
        from intelligence_core import IntelligenceCore
        core = IntelligenceCore(WORKING_DIRECTORY)
        context_prompt = ""
        
        if WORKING_DIRECTORY:
            # Multi-Agent Orchestrator Handling (Phase 4)
            from agent_orchestrator import AgentOrchestrator
            orchestrator = AgentOrchestrator(core)
            cmd_prefix = task.split(" ")[0]
            
            # --- LLM Runner Definition (Bridge for simple/complex tasks) ---
            def llm_runner(prompt: str) -> str:
                res = None
                try:
                    # Re-use the existing `smolagents` loop so `DebugAgent` can still use `safe_write` hooks
                    for step in self.agent.run(prompt, stream=True):
                        if type(step).__name__ == "ActionStep" and step.is_final_answer and step.action_output is not None:
                            res = str(step.action_output)
                        elif type(step).__name__ == "FinalAnswerStep":
                            res = str(step.output)
                    return res or ""
                except Exception as e:
                    logger.error(f"[LLM RUNNER ERR] {e}")
                    return ""

            # --- PHASE 6: INTENT ROUTING MVP ---
            from intent_router import IntentRouter
            router = IntentRouter(confidence_threshold=0.8)
            
            # Skip routing for explicit slash commands to preserve legacy UX
            if not task.startswith("/"):
                yield f"🧠 *Intelligence Layer: Routing Intent...*\n\n"
                
                try:
                    routing_result = router.route_intent(task)
                except Exception as route_err:
                    logger.error(f"IntentRouter crashed: {route_err}")
                    routing_result = {"execution_path": "Direct Execution", "reason": f"Router error: {route_err}"}
                
                exec_path = routing_result.get("execution_path")
                
                # Phase 7 Sprint 1: Emit Intent to Copilot Store via WebSocket
                yield {
                    "__copilot_event__": True,
                    "source": "router",
                    "type": "intent",
                    "payload": {
                        "label": exec_path,
                        "confidence": routing_result.get("confidence", 0.0),
                        "explanation": routing_result.get("reason", "No explanation provided.")
                    }
                }
                
                # Phase 7 Sprint 2: Emit Explainability reasoning
                from explainability import ExplainabilityEmitter
                yield ExplainabilityEmitter.emit(
                    source="router",
                    reason_code="intent_classification",
                    summary=f"Classified as '{exec_path}' based on request structure.",
                    context={"confidence": routing_result.get("confidence", 0.0), "intent": exec_path}
                )
                
                # Templates are used ONLY as a silent fallback when LLM is unavailable.
                # The LLM path runs first via the normal Planner/Direct flow below.
                
                if exec_path == "Clarification Needed":
                    yield f"🤔 *I'm not exactly sure what to execute.* (Ambiguous Intent)\nReason: {routing_result.get('reason')}\n\nCould you clarify your request?"
                    return
                elif exec_path == "Task Graph Planner":
                    from planner import PlannerEngine
                    planner = PlannerEngine()
                    yield f"🧭 *High Complexity Detected. Engaging Task Graph Planner...*\n\n"
                    
                    try:
                        graph = planner.load_dummy_graph("complex", user_request=task)
                        yield f"🗺️ *Graph built: {len(graph.nodes)} node(s). Executing sequentially...*\n\n"
                        
                        context_ext = {
                            "task": task, 
                            "workspace": core.get_workspace_context(max_files=5),
                            "runner": llm_runner
                        }
                        
                        # Phase 6 Sprint 4: Stream dag_update events for Timeline UI
                        completed_count = 0
                        has_failed = False
                        for dag_event in planner.execute_graph_stream(graph, context_ext):
                            # Yield the dag_event dict directly — WebSocket handler will detect and forward
                            yield {"__dag_event__": True, **dag_event}
                            # Track final state
                            all_done = all(n["status"] == "COMPLETED" for n in dag_event.get("nodes", []))
                            any_fail = any(n["status"] == "FAILED" for n in dag_event.get("nodes", []))
                            if all_done:
                                completed_count = len(dag_event.get("nodes", []))
                            if any_fail:
                                has_failed = True
                        
                        if has_failed:
                            yield f"❌ **Task Graph Execution Halted.**\nCheck the Timeline panel for details."
                        else:
                            yield f"✅ **Task Graph Execution Complete.**\nSuccessfully processed {completed_count} chained objectives."
                    except Exception as pe:
                        logger.error(f"Planner Error: {pe}")
                        pe_str = str(pe)
                        if "402" in pe_str or "Payment" in pe_str or "Credit" in pe_str:
                            # --- GRACEFUL FALLBACK: Use Instant Generation templates ---
                            from offline_engine import execute_offline
                            fallback_result = execute_offline(task, safe_write)
                            if fallback_result:
                                yield f"⚡ *Generating code...*\n\n"
                                yield fallback_result
                                core.add_memory_note(f"User Request: {task[:100]}")
                            else:
                                yield f"⚠️ **AI Credits Depleted.**\nYour HuggingFace API key has run out of credits.\n\n💡 **How to fix:** Update your API key in the IDE settings with one that has active credits, or subscribe to HuggingFace PRO."
                        else:
                            yield f"❌ **Planner Engine Failed.**\nError: {pe}"
                    return
            
            # --- Phase 4 Fallback / Direct Execution ---
            if cmd_prefix in orchestrator.agents:
                user_task = task.replace(cmd_prefix, "").strip()
                agent_name = orchestrator.agents[cmd_prefix].name
                
                # Let user know the agent is thinking (streaming UX)
                yield f"⚙️ *{agent_name} is analyzing the workspace...*\n\n"
                
                returned_agent, final_text = orchestrator.route_and_execute(cmd_prefix, user_task, llm_runner)
                yield final_text
                return

            # Legacy Phase 3 Command Palette Handling
            if task.startswith("/explain"):
                context_prompt = f"{core.get_workspace_context(max_files=10)}\n\n[USER COMMAND: /explain]\nExplain the architecture or the specific file requested: {task.replace('/explain', '').strip()}"
            elif task.startswith("/refactor"):
                context_prompt = f"{core.get_workspace_context(max_files=10)}\n\n[USER COMMAND: /refactor]\nSuggest refactoring improvements for: {task.replace('/refactor', '').strip()}"
            elif task.startswith("/generate-tasks"):
                context_prompt = core.generate_task_prompt(task.replace('/generate-tasks', '').strip())
            elif task.startswith("/health"):
                context_prompt = core.build_health_prompt()
            elif task.startswith("/insights"):
                # Phase 6: Background Insights — Manual Trigger
                from insights_engine import InsightsEngine
                engine = InsightsEngine(WORKING_DIRECTORY)
                insights = engine.run_scan()
                
                # Phase 7 Sprint 1: Emit Insights to Copilot UI
                yield {
                    "__copilot_event__": True,
                    "source": "insights",
                    "type": "update",
                    "payload": {
                        "insights": insights
                    }
                }
                
                # Phase 7 Sprint 2: Emit Explainability reasoning
                from explainability import ExplainabilityEmitter
                yield ExplainabilityEmitter.emit(
                    source="insights",
                    reason_code="insight_trigger",
                    summary=f"Background scan completed. Found {len(insights)} insights.",
                    context={"insight_count": len(insights)}
                )
                
                yield engine.format_insights_text()
                return
            else:
                # Standard Contextual Chat
                
                # --- PHASE 6: PROJECT MEMORY MVP ---
                try:
                    from memory import ProjectMemory
                    pmemory = ProjectMemory(WORKING_DIRECTORY)
                    memory_context = pmemory.safe_memory_read(task)
                except Exception as e:
                    logger.error(f"Project Memory injection failed: {e}")
                    memory_context = ""
                    
                proj_memory_block = f"### PROJECT MEMORY ###\n{memory_context}\n" if memory_context else ""
                
                memory = core.load_memory()
                recent_notes = "\n".join(memory.get("notes", []))
                context_prompt = f"""
{proj_memory_block}
[WORKSPACE MEMORY]
{recent_notes}

{core.get_workspace_context(max_files=15, max_chars_per_file=1000)}

[USER PROMPT]
{task}
"""
            # Save interaction to memory
            core.add_memory_note(f"User Request: {task[:100]}")
            
            task_to_run = context_prompt
        else:
            task_to_run = task
            
        logger.info(f"Context-Aware Task Length: {len(task_to_run)} chars")
        
        try:
            for step in self.agent.run(task_to_run, stream=True):
                # Log internals for debugging (NOT sent to frontend)
                if isinstance(step, ToolCall):
                    logger.info(f"  Tool: {step.name}")
                elif isinstance(step, ActionStep):
                    if step.error:
                        logger.error(f"  Step Error: {step.error}")
                    if hasattr(step, "observations") and step.observations:
                        logger.info(f"  Observation: {step.observations[:200]}...")
                    if step.is_final_answer and step.action_output is not None:
                        final_answer = str(step.action_output)
                elif isinstance(step, FinalAnswerStep):
                    final_answer = str(step.output)
                elif isinstance(step, ToolOutput):
                    logger.info(f"  Tool Output: {str(step.observation)[:200]}...")
                # ChatMessageStreamDelta is just intermediate thinking - skip

            if final_answer:
                yield final_answer
            else:
                yield "Task completed."
                
        except GeneratorExit:
            logger.info("Client disconnected.")
            return
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            err_str = str(e)
            if "402" in err_str or "Payment Required" in err_str or "Credit balance" in err_str:
                # --- GRACEFUL FALLBACK: Use Instant Generation templates ---
                from offline_engine import execute_offline
                fallback_result = execute_offline(task, safe_write)
                if fallback_result:
                    yield f"⚡ *Generating code...*\n\n"
                    yield fallback_result
                else:
                    yield f"⚠️ **AI Credits Depleted.**\nYour HuggingFace API key has run out of credits.\n\n💡 **How to fix:** Go to [huggingface.co/settings/billing](https://huggingface.co/settings/billing) to add credits, or update your API key in the IDE settings."
            else:
                yield f"Error: {e}"

