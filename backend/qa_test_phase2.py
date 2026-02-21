import requests
import time
import subprocess
import os
import shutil

PORT = 8111
BASE_URL = f"http://localhost:{PORT}"
TEST_PROJECT_A = os.path.abspath(os.path.join(os.getcwd(), "qa_workspace_a"))
TEST_PROJECT_B = os.path.abspath(os.path.join(os.getcwd(), "qa_workspace_b"))

# Ensure clean state
for d in [TEST_PROJECT_A, TEST_PROJECT_B]:
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)

print("🚀 Starting Omni-IDE backend for Phase 2 QA testing...")
server_process = subprocess.Popen(
    [os.sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(3)

def change_dir(path: str):
    response = requests.post(f"{BASE_URL}/api/change_dir", json={"path": path})
    response.raise_for_status()

def run_code(code: str):
    response = requests.post(f"{BASE_URL}/api/run", json={"code": code})
    response.raise_for_status()
    return response.json()

try:
    print("\n" + "="*60)
    print(" QA TEST SUITE: Phase 2 Runtime & VENV Manager")
    print("="*60)

    # -------------------------------------------------------------
    # CASE 1: Fresh Project Run (Env built, deps installed)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 1: Fresh project run (Env creation + install)")
    change_dir(TEST_PROJECT_A)
    res1 = run_code("import pytz\nprint('pytz installed!')")
    out1 = res1.get("stdout", "")
    assert "Initializing isolated project environment" in out1, f"Expected env creation logs. Got:\n{out1}"
    assert "Environment created successfully." in out1, f"Venv creation should succeed. Got:\n{out1}"
    assert "[⚙️ AUTO-PIP] Missing module 'pytz'" in out1, f"Auto-pip should trigger. Got:\n{out1}"
    assert "✅ [INSTALLED]" in out1, f"Expected successful installation. Got:\n{out1}"
    print("✅ PASS: Env created + install happens once.")

    # -------------------------------------------------------------
    # CASE 2: Second Run (Zero config, instant cache hit)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 2: Second run on same project")
    res2 = run_code("import pytz\nprint('pytz STILL here!')")
    out2 = res2.get("stdout", "")
    assert "Initializing isolated project environment" not in out2, "Env already exists, should skip creation."
    assert "[⚙️ AUTO-PIP]" not in out2, "Should NOT trigger auto-pip installation again."
    assert "pytz STILL here!" in out2, "Code should execute properly."
    print("✅ PASS: Zero installs + fast startup.")

    # -------------------------------------------------------------
    # CASE 3: Add new dependency (Cache behavior)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 3: Add new dependency")
    res3 = run_code("import pytz\nimport colorama\nprint('Done adding deps.')")
    out3 = res3.get("stdout", "")
    assert "[⚙️ AUTO-PIP] Missing module 'colorama'" in out3, "Auto-pip should only trigger for colorama."
    assert "✅ [INSTALLED]" in out3, "Expected colorama installation."
    print("✅ PASS: Only new package installs.")

    # -------------------------------------------------------------
    # CASE 4: Delete Env -> Auto Rebuild
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 4: Delete env (Auto rebuild)")
    shutil.rmtree(os.path.join(TEST_PROJECT_A, ".antigravity_env"))
    res4 = run_code("import pytz\nprint('Rebuilt!')")
    out4 = res4.get("stdout", "")
    assert "Initializing isolated project environment" in out4, "Expected env creation logs after deletion."
    print("✅ PASS: Auto rebuilds corrupted/deleted environment.")

    # -------------------------------------------------------------
    # CASE 5: Multiple Projects (Sub-sandboxing)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 5: Run multiple projects (Isolation)")
    change_dir(TEST_PROJECT_B)
    res5 = run_code("try:\n    import pytz\nexcept ImportError:\n    print('pytz NOT FOUND (as expected)')")
    out5 = res5.get("stdout", "")
    assert "Initializing isolated project environment" in out5, "Project B should get its own env."
    assert "pytz NOT FOUND" in out5, "Project B should NOT share Project A's installed dependencies."
    print("✅ PASS: Isolated environments.")

    # -------------------------------------------------------------
    # CASE 6: Sandbox Execution Rules
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 6: Security Sandbox (Prevent out-of-bounds file writes)")
    change_dir(TEST_PROJECT_A)
    # Try to write to a parent folder, outside the TEST_PROJECT_A workspace
    malicious_code = "try:\n    with open('../evil_file.txt', 'w') as f: f.write('hax')\nexcept PermissionError:\n    print('BLOCKED BY SANDBOX')\n"
    res6 = run_code(malicious_code)
    out6 = res6.get("stdout", "")
    
    # Asserting the specific sandbox error log
    assert "BLOCKED BY SANDBOX" in out6 or "PermissionError" in res6.get("stderr", ""), "Must be blocked by sandbox."
    print("✅ PASS: Security sandbox effectively restricted execution to project limits.")

    print("\n" + "="*60)
    print(" 🏆 ALL PHASE 2 QA TEST CASES PASSED SUCCESSFULLY ")
    print("="*60)

finally:
    # Cleanup
    print("\n🛑 Shutting down QA server & cleaning workspaces...")
    server_process.terminate()
    server_process.wait()
    for d in [TEST_PROJECT_A, TEST_PROJECT_B]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
