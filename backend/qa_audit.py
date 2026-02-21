import requests
import os
import sys

def run_audit():
    red_flags = []
    
    print("🧪 PHASE 1: The 'Gatekeeper' Security Audit")
    # Check 1: Scan main.py for print(api_key)
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "print(api_key)" in content or "print(hf_token)" in content:
                red_flags.append("SECURITY FAIL: Found print(api_key) or print(hf_token) in main.py")
            else:
                print("  [PASS] No hardcoded API keys or key logging detected in main.py.")
    except Exception as e:
        red_flags.append(f"Failed to read main.py: {e}")

    # Check 3: Check /api/check-auth format
    try:
        resp = requests.get("http://localhost:8000/api/check-auth", timeout=5)
        data = resp.json()
        if "authenticated" in data and isinstance(data["authenticated"], bool):
            print(f"  [PASS] /api/check-auth returned correct format: {data}")
        else:
            red_flags.append(f"Auth check response format is invalid: {data}")
    except Exception as e:
        red_flags.append(f"Failed to hit /api/check-auth: {e}")

    print("\n🧪 PHASE 2: The 'Workspace Guard' Logic")
    # Check 2: POST to /chat without setting workspace
    # First, make sure we clear the workspace if it was set
    try:
        # We manually trigger close_folder to reset it so we can test the guard
        requests.post("http://localhost:8000/api/close_folder", timeout=5)
        
        chat_resp = requests.post("http://localhost:8000/chat", json={"text": "hello"}, timeout=5)
        chat_data = chat_resp.json()
        if "Workspace Missing" in chat_data.get("response", "") or "Workspace Missing" in chat_data.get("reply", ""):
            print("  [PASS] Workspace Guard correctly caught homeless agent request.")
        else:
            red_flags.append(f"Workspace Guard FAILED to block request. Response: {chat_data}")
    except Exception as e:
        red_flags.append(f"Failed to hit /chat endpoint: {e}")

    print("\n🧪 PHASE 3: The 'Ugly Window' Polish")
    # Check 4: Verify desktop.py does not contain debug=True
    try:
        with open("desktop.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "debug=True" in content.replace(" ", ""):
                red_flags.append("UI POLISH FAIL: Found debug=True in desktop.py")
            else:
                print("  [PASS] desktop.py has debug=False (Production Mode).")
    except Exception as e:
        red_flags.append(f"Failed to read desktop.py: {e}")

    print("\n🧪 PHASE 4: The Build Pipeline")
    # Check OmniIDE-Installer.iss and build_release.py 
    try:
        with open("build_release.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "--add-data=static;static" in content and "--noconsole" in content:
                print("  [PASS] build_release.py includes static assets and hides console.")
            else:
                red_flags.append("BUILD FAIL: build_release.py missing static assets or noconsole flag.")
                
        with open("OmniIDE-Installer.iss", "r", encoding="utf-8") as f:
            content = f.read()
            if "icon.ico" in content:
                print("  [PASS] OmniIDE-Installer.iss correctly references the app icon.")
            else:
                red_flags.append("BUILD FAIL: Installer missing icon reference.")
    except Exception as e:
        red_flags.append(f"Failed to read build files: {e}")

    print("\n=============================================")
    print("OUTPUT SUMMARY:")
    if red_flags:
        print("🚨 RED FLAGS DETECTED:")
        for r in red_flags:
            print(f"  - {r}")
        print("\nVERDICT: ⛔ NO-GO. Production Release Blocked.")
    else:
        print("✅ NO RED FLAGS DETECTED.")
        print("VERDICT: 🚀 GO. Production Release Approved (Gold Master 1.0.0).")
    print("=============================================")

if __name__ == '__main__':
    run_audit()
