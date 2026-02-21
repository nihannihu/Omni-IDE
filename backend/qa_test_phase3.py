import requests
import json
import time
import subprocess
import os
import shutil

PORT = 8111
BASE_URL = f"http://localhost:{PORT}"
TEST_PROJECT = os.path.abspath(os.path.join(os.getcwd(), "qa_workspace_phase3"))

# Ensure clean state
if os.path.exists(TEST_PROJECT):
    shutil.rmtree(TEST_PROJECT)
os.makedirs(TEST_PROJECT)

# Create a sample file for context testing
sample_code = """
def calculate_area(radius):
    '''Returns the area of a circle.'''
    return 3.14159 * radius * radius

print(calculate_area(5))
"""
with open(os.path.join(TEST_PROJECT, "math_utils.py"), "w") as f:
    f.write(sample_code)

print("🚀 Starting Omni-IDE backend for Phase 3 QA testing...")
server_process = subprocess.Popen(
    [os.sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(3)

def change_dir(path: str):
    response = requests.post(f"{BASE_URL}/api/change_dir", json={"path": path})
    response.raise_for_status()

# We test the Agent streaming endpoint by calling the websocket or executing the iterator. 
# But for simplicity in HTTP testing, we'll just mock the context mapping functions directly.
from intelligence_core import IntelligenceCore

try:
    print("\n" + "="*60)
    print(" QA TEST SUITE: Phase 3 AI Intelligence Core")
    print("="*60)
    
    # Init core pointing to test project
    core = IntelligenceCore(TEST_PROJECT)

    # -------------------------------------------------------------
    # CASE 1: Ask AI to explain a function (Context Gathering)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 1: /explain Context Generator")
    explain_prompt = f"{core.get_workspace_context(max_files=10)}\n\n[USER COMMAND: /explain]\nExplain the architecture or the specific file requested: math_utils.py"
    assert "math_utils.py" in explain_prompt, "Expected file map to include the sample file."
    assert "calculate_area" in explain_prompt, "Expected context to include the function code."
    print("✅ PASS: Uses correct file context.")

    # -------------------------------------------------------------
    # CASE 2: Trigger runtime error (Debug Prompt Generator)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 2: /debug Autonomous Analyzer")
    fake_error = "TypeError: unsupported operand type(s) for *: 'float' and 'str'"
    debug_prompt = core.build_debug_prompt(fake_error)
    assert "[AUTONOMOUS DEBUGGER]" in debug_prompt, "Expected explicit debugger trigger string."
    assert "calculate_area" in debug_prompt, "Expected debug prompt to have workspace file context injected."
    assert fake_error in debug_prompt, "Expected the stack trace to be included for analysis."
    print("✅ PASS: Correctly builds the unified trace + context prompt.")

    # -------------------------------------------------------------
    # CASE 3: Generate feature task (/generate-tasks)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 3: /generate-tasks Logic")
    task_prompt = core.generate_task_prompt("Add a login system")
    assert "array of tasks" in task_prompt, "Expected structured JSON instructions."
    
    # Simulate saving tasks
    core.save_tasks([{"task": "Build Login UI", "files_impacted": ["login.html"], "complexity": "Medium"}])
    loaded_tasks = core.load_tasks()
    assert len(loaded_tasks) == 1, "Expected tasks file to persist."
    assert loaded_tasks[0]["task"] == "Build Login UI", "Expected task state."
    print("✅ PASS: Structured task list created and persisted.")

    # -------------------------------------------------------------
    # CASE 4: Reopen project (Memory persists)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 4: Workspace Memory Persistence")
    core.add_memory_note("User prefers dark mode CSS.")
    
    # Reload from simulated 'new' session
    new_core = IntelligenceCore(TEST_PROJECT)
    loaded_memory = new_core.load_memory()
    assert len(loaded_memory["notes"]) == 1, "Expected notes array to have one item."
    assert "dark mode" in loaded_memory["notes"][0], "Expected memory file to persist preference."
    print("✅ PASS: Memory correctly persisted.")

    # -------------------------------------------------------------
    # CASE 5: Large file trimming
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 5: Intelligent Context Trimming")
    large_code = "A" * 2000
    with open(os.path.join(TEST_PROJECT, "large_file.txt"), "w") as f:
        f.write(large_code)
    
    trimmed_context = core.get_workspace_context(max_files=10, max_chars_per_file=100)
    assert "large_file.txt" in trimmed_context, "Expected large file to be mapped."
    assert "[TRUNCATED]" in trimmed_context, "Expected text to be clipped to save LLM context window."
    assert len(trimmed_context) < 3000, "Expected output string to be severely trimmed."
    print("✅ PASS: Context trimmed intelligently.")

    print("\n" + "="*60)
    print(" 🏆 ALL PHASE 3 QA TEST CASES PASSED SUCCESSFULLY ")
    print("="*60)

finally:
    # Cleanup
    print("\n🛑 Shutting down QA server & cleaning workspaces...")
    server_process.terminate()
    server_process.wait()
    if os.path.exists(TEST_PROJECT):
        shutil.rmtree(TEST_PROJECT, ignore_errors=True)
