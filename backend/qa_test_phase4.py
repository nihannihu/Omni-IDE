import os
import json
import time
import shutil

TEST_PROJECT = os.path.abspath(os.path.join(os.getcwd(), "qa_workspace_phase4"))

# Ensure clean state
if os.path.exists(TEST_PROJECT):
    shutil.rmtree(TEST_PROJECT)
os.makedirs(TEST_PROJECT)

# Create a sample file for context testing
sample_code = """
def authenticate_user(username, password):
    if username == "admin" and password == "1234":
        return True
    return False
"""
with open(os.path.join(TEST_PROJECT, "auth.py"), "w") as f:
    f.write(sample_code)

from intelligence_core import IntelligenceCore
from agent_orchestrator import AgentOrchestrator

try:
    print("\n" + "="*60)
    print(" QA TEST SUITE: Phase 4 Multi-Agent Orchestration")
    print("="*60)
    
    core = IntelligenceCore(TEST_PROJECT)
    orchestrator = AgentOrchestrator(core)

    # -------------------------------------------------------------
    # CASE 1: /plan feature request (Structured Tasks JSON)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 1: Planner Agent (/plan)")
    def mock_planner_llm(prompt: str) -> str:
        return '''```json
{
  "goal": "Build robust auth",
  "tasks": [
    {"title": "Hash passwords", "description": "Use bcrypt", "files": ["auth.py"], "priority": 1}
  ],
  "risks": ["SQL Injection"],
  "estimated_complexity": "medium"
}
```'''
    agent_name, text = orchestrator.route_and_execute("/plan", "Improve auth security", mock_planner_llm)
    assert agent_name == "PlannerAgent", "Routed to wrong agent."
    assert "Architecture Plan: Build robust auth" in text, "Planner text formatting failed."
    assert "Complexity:** MEDIUM" in text, f"Complexity formatting failed. Got: {text}"
    assert "Hash passwords" in text, "Task formatting failed."
    print("✅ PASS: Planner Agent routed and JSON formatted successfully.")

    # -------------------------------------------------------------
    # CASE 2: runtime crash (/debug)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 2: Debug Agent (/debug)")
    def mock_debug_llm(prompt: str) -> str:
        return "I found the bug! You are using plain text passwords.\n\n```python\nsafe_write('auth.py', 'code')\n```"
    agent_name, text = orchestrator.route_and_execute("/debug", "TypeError on auth", mock_debug_llm)
    assert agent_name == "DebugAgent", "Routed to wrong agent."
    assert "I found the bug!" in text, "Debug text mapping failed."
    print("✅ PASS: Debug Agent routed and raw text output successfully.")

    # -------------------------------------------------------------
    # CASE 3: /review file (Score + Suggestions)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 3: Review Agent (/review)")
    def mock_review_llm(prompt: str) -> str:
        return '''{
  "summary": "Insecure auth mechanism.",
  "issues": ["Plain text password check."],
  "suggestions": ["Use a secure hashing algorithm.", "Compare in constant time."],
  "score": 30
}'''
    agent_name, text = orchestrator.route_and_execute("/review", "auth.py", mock_review_llm)
    assert agent_name == "ReviewAgent", "Routed to wrong agent."
    assert "Code Review (Score: 30/100)" in text, "Review text formatting failed."
    assert "⚠️ Plain text password check." in text, "Issue formatting failed."
    print("✅ PASS: Review Agent routed and JSON formatted successfully.")

    # -------------------------------------------------------------
    # CASE 4: Malformed LLM Output (Validation Fallback)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 4: Validation Fallback (Malformed Output)")
    def mock_bad_llm(prompt: str) -> str:
        return "Hey there! I didn't output JSON. Here are my thoughts: Bla bla bla."
    # The /review command expects JSON schema
    agent_name, text = orchestrator.route_and_execute("/review", "auth.py", mock_bad_llm)
    assert "⚙️ *ReviewAgent Response (Unstructured):*" in text, "Validation fallback didn't trigger correctly."
    assert "Bla bla bla." in text, "Raw text was not preserved."
    print("✅ PASS: Orchestrator gracefully degraded to raw text when JSON failed.")

    # -------------------------------------------------------------
    # CASE 5: Repeated runs (Memory Persists)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 5: Agent Memory Persistence")
    # Both the planner and review agent were run successfully before.
    memory = core.load_memory()
    assert "planner_runs" in memory and len(memory["planner_runs"]) == 1, "Planner memory missing."
    assert memory["planner_runs"][0]["estimated_complexity"] == "medium", "Planner state corrupted."
    assert "reviews" in memory and len(memory["reviews"]) == 1, "Review memory missing."
    assert memory["reviews"][0]["score"] == 30, "Review state corrupted."
    assert "debug_sessions" in memory and len(memory["debug_sessions"]) == 1, "Debug memory missing."
    print("✅ PASS: Orchestrator successfully hydrated agent results to persistent memory.")

    # -------------------------------------------------------------
    # CASE 6: Multiple Commands Quickly (Routing)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 6: Rapid Command Routing")
    assert orchestrator.route_and_execute("/plan", "Test", mock_planner_llm)[0] == "PlannerAgent"
    assert orchestrator.route_and_execute("/debug", "Test", mock_debug_llm)[0] == "DebugAgent"
    assert orchestrator.route_and_execute("/review", "Test", mock_review_llm)[0] == "ReviewAgent"
    invalid_route = orchestrator.route_and_execute("/fake", "Test", mock_review_llm)
    assert invalid_route[0] == "Router", "Expected Router drop for invalid intent."
    assert "No agent mapping found" in invalid_route[1], "Expected explicit error."
    print("✅ PASS: Routing accurately detected multiple intents rapidly.")

    print("\n" + "="*60)
    print(" 🏆 ALL PHASE 4 QA TEST CASES PASSED SUCCESSFULLY ")
    print("="*60)

finally:
    # Cleanup
    print("\n🛑 Shutting down QA script & cleaning workspaces...")
    if os.path.exists(TEST_PROJECT):
        shutil.rmtree(TEST_PROJECT, ignore_errors=True)
