import requests
import time
import subprocess
import os

PORT = 8111
BASE_URL = f"http://localhost:{PORT}"

print("🚀 Starting Omni-IDE backend for QA Auto-Pip testing...")
server_process = subprocess.Popen(
    [os.sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Wait for server to boot
time.sleep(3)

def run_code(code: str):
    response = requests.post(f"{BASE_URL}/api/run", json={"code": code})
    response.raise_for_status()
    return response.json()

try:
    print("\n" + "="*50)
    print(" QA TEST SUITE: Cross-Platform Dependency Manager ")
    print("="*50)

    # -------------------------------------------------------------
    # CASE 1: Standard Library (No install attempts)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 1: Script with only standard library")
    res1 = run_code("import math\nprint('Math pi:', math.pi)")
    out1 = res1.get("stdout", "")
    assert "[⚙️ AUTO-PIP]" not in out1, f"Expected no auto-pip, got:\n{out1}"
    assert "Math pi: 3.14" in out1, "Expected script execution to succeed."
    print("✅ PASS: No install attempts triggered.")

    # -------------------------------------------------------------
    # CASE 2: Unsupported OS Module (termios on Windows)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 2: Script importing termios on Windows")
    res2 = run_code("import termios\nprint('This should trace back but not install')")
    out2 = res2.get("stdout", "")
    assert "[⚙️ AUTO-PIP] Missing module 'termios' detected!" in out2, "Expected auto-pip to intercept termios"
    assert "⏭️ [SKIPPED: PLATFORM]" in out2, "Expected platform skip message."
    assert "not supported on Windows" in out2, "Expected clear warning."
    assert "✅ [INSTALLED]" not in out2, "Expected NO install success message."
    print("✅ PASS: Skipped install + warning + prevented pipeline failure.")

    # -------------------------------------------------------------
    # Ensure pytz is uninstalled so Case 3 and 4 work
    # -------------------------------------------------------------
    print("\n(Pre-Test Setup: Uninstalling a target package to guarantee install trigger...)")
    subprocess.run([os.sys.executable, "-m", "pip", "uninstall", "-y", "pytz"], capture_output=True)

    # -------------------------------------------------------------
    # CASE 3: Safe Auto-Install
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 3: Script importing a standard PyPI package (pytz)")
    res3 = run_code("import pytz\nprint('pytz loaded!')")
    out3 = res3.get("stdout", "")
    assert "[⚙️ AUTO-PIP] Missing module 'pytz' detected!" in out3, f"Auto-pip should trigger. Got:\n{out3}"
    assert "✅ [INSTALLED] Successfully installed" in out3, f"Expected successful installation. Got:\n{out3}"
    print("✅ PASS: Auto install succeeds.")

    # -------------------------------------------------------------
    # CASE 4: Mixed Imports (pytz installs, fcntl skips)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 4: Mixed imports (pytz + fcntl)")
    subprocess.run([os.sys.executable, "-m", "pip", "uninstall", "-y", "pyjokes"], capture_output=True)
    res4 = run_code("import fcntl\nimport pyjokes\nprint('Done.')")
    out4 = res4.get("stdout", "")
    assert "[⚙️ AUTO-PIP] Missing module 'fcntl'" in out4, f"Auto-pip should intercept fcntl. Got:\n{out4}"
    assert "⏭️ [SKIPPED: PLATFORM]" in out4, "fcntl should skip."
    print("✅ PASS: Mixed imports correctly routed.")

    # -------------------------------------------------------------
    # CASE 5: Re-run Same Script (Already installed)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 5: Re-run same script (pytz)")
    res5 = run_code("import pytz\nprint('It works now.')")
    out5 = res5.get("stdout", "")
    assert "[⚙️ AUTO-PIP]" not in out5, "Should not trigger auto-pip if already installed."
    assert "It works now." in out5, "Script should execute properly."
    print("✅ PASS: No repeated install attempts.")

    print("\n" + "="*50)
    print(" 🏆 ALL 5 QA TEST CASES PASSED SUCCESSFULLY ")
    print("="*50)

finally:
    # Cleanup
    print("\n🛑 Shutting down QA server...")
    server_process.terminate()
    server_process.wait()
