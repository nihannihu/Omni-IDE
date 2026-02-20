"""Quick verification of the 3 UX fixes."""
import requests

BASE = "http://localhost:8000"
tests = []

def test(name, ok, detail=""):
    tests.append((name, ok))
    print(f"  {'✅' if ok else '❌'} [{('PASS' if ok else 'FAIL')}] {name} — {detail}")

print("=" * 55)
print("  UX Polish Verification Tests")
print("=" * 55)

# Test 1: No-Folder Guard
print("\n🛑 Issue 2: No-Folder Guard")
r = requests.post(f"{BASE}/chat", json={"text": "hello"})
d = r.json()
reply = d.get("reply", "") or d.get("response", "")
test("Chat returns guard", "Workspace" in reply or "Open Folder" in reply, reply[:60])

# Test 2: Gatekeeper alive
print("\n🔐 Issue 3: Gatekeeper Intact")
r = requests.get(f"{BASE}/api/check-auth")
test("check-auth responds", r.status_code == 200, str(r.json()))

r = requests.post(f"{BASE}/api/save-key", json={"key": "bad_key"})
test("Invalid key rejected", r.status_code == 400, f"HTTP {r.status_code}")

# Summary
p = sum(1 for _, ok in tests if ok)
f = len(tests) - p
print(f"\n{'='*55}")
print(f"  TOTAL:  {p} PASS  |  {f} FAIL")
print(f"  VERDICT: {'🟢 ALL CLEAR' if f == 0 else '🔴 FIX NEEDED'}")
print("=" * 55)
