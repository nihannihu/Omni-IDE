import os
import json
import logging
from dotenv import load_dotenv
from intent_router import IntentRouter

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_tests():
    print("============================================================")
    print(" 🧠 LEAD QA: PHASE 6 INTENT ROUTER MVP VALIDATION")
    print("============================================================")
    
    # Check API key before running
    if not os.getenv("HUGGINGFACE_API_KEY"):
        print("❌ FATAL: HUGGINGFACE_API_KEY is missing from environment.")
        return

    router = IntentRouter(confidence_threshold=0.8)
    
    tests = [
        {
            "id": 1,
            "name": "TEST 1: Simple Prompt (Direct Execution)",
            "query": "Change the background color of the login button in style.css to bright red.",
            "expected_path": "Direct Execution"
        },
        {
            "id": 2,
            "name": "TEST 2: Complex Prompt (Task Graph Planner)",
            "query": "Create a completely new user authentication flow. Generate a login.html, a register.html, and write the backend JWT validation logic in auth.py.",
            "expected_path": "Task Graph Planner"
        },
        {
            "id": 3,
            "name": "TEST 3: Ambiguous Prompt (Clarification Needed)",
            "query": "just do it now.",
            "expected_path": "Clarification Needed"
        }
    ]
    
    passed = 0
    
    for t in tests:
        print(f"\n▶️  {t['name']}")
        print(f"   Query: \"{t['query']}\"")
        
        result = router.route_intent(t['query'])
        path = result.get("execution_path")
        reason = result.get("reason")
        
        print(f"   Routed Path: {path}")
        print(f"   Reasoning:   {reason}")
        
        if path == t['expected_path']:
            print("   ✅ PASS")
            passed += 1
        else:
            print(f"   ❌ FAIL (Expected: {t['expected_path']})")
            print(f"      Raw Data: {json.dumps(result.get('raw_data'), indent=2)}")

    print("\n============================================================")
    if passed == len(tests):
        print(" 🏁 QA ROUTER SUITE COMPLETE: ALL PASSED")
    else:
        print(f" ⚠️ QA ROUTER SUITE FAILED: {passed}/{len(tests)} PASSED")
    print("============================================================")

if __name__ == "__main__":
    run_tests()
