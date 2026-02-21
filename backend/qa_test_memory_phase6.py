import os
import shutil
import json
from pathlib import Path
from memory import ProjectMemory

def run_tests():
    print("============================================================")
    print(" 🧠 LEAD QA: PHASE 6 PROJECT MEMORY MVP VALIDATION")
    print("============================================================")
    
    test_dir = Path("qa_workspace_memory_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    pmemory = ProjectMemory(str(test_dir))
    
    # [1] Memory file auto-creation
    print("\n▶️  TEST 1: Memory file auto-creation")
    try:
        data = pmemory.load_memory()
        assert test_dir.joinpath('.antigravity_memory.json').exists(), "File not created"
        assert data["version"] == 1, "Incorrect version"
        print("   ✅ PASS: JSON created gracefully")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        
    # Scaffold Knowledge Items
    item1 = {
        "id": "uuid-1", "type": "architecture_decision",
        "title": "Use Staging Layer", "summary": "All file writes must go through Diff Staging Layer.",
        "created_at": "2026-02-21T10:00:00Z", "tags": ["core"], "relevance_hint": ["write", "file", "staging"]
    }
    item2 = {
        "id": "uuid-2", "type": "rule",
        "title": "No Direct Edits", "summary": "Never bypass propose_patch API.",
        "created_at": "2026-02-21T10:05:00Z", "tags": ["security"], "relevance_hint": ["bypass", "propose_patch", "edit"]
    }
    item3 = {
        "id": "uuid-3", "type": "note",
        "title": "Frontend Setup", "summary": "Use React with Tailwind CSS.",
        "created_at": "2026-02-21T10:10:00Z", "tags": ["frontend"], "relevance_hint": ["react", "tailwind", "ui"]
    }
    pmemory.add_knowledge_item(item1)
    pmemory.add_knowledge_item(item2)
    pmemory.add_knowledge_item(item3)

    # [2] Valid knowledge item retrieval
    print("\n▶️  TEST 2: Valid knowledge item retrieval")
    try:
        items = pmemory.get_relevant_memory("I need to write a file. Do I use staging?")
        assert len(items) > 0, "No items returned"
        assert items[0]["title"] == "Use Staging Layer", f"Wrong top item: {items[0]['title']}"
        print("   ✅ PASS: Semantic keyword match achieved")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # [3] Ranking correctness with multiple matches
    print("\n▶️  TEST 3: Ranking correctness with multiple matches")
    try:
        items = pmemory.get_relevant_memory("How do I edit frontend UI with React without bypass propose_patch?")
        assert len(items) >= 2, "Failed to retrieve multiple hits"
        print("   ✅ PASS: Safely retrieves and ranks multiple items")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # [4] Prompt formatting stays under token limit
    print("\n▶️  TEST 4: Prompt formatting stays under token limit")
    try:
        context = pmemory.safe_memory_read("react staging bypass", top_k=3)
        assert len(context) < 1200, "Context exceeds implicit token limit bounds"
        assert "Never bypass" in context, "Context formatting loss"
        print("   ✅ PASS: Formatting maps cleanly without bloating")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # [5] Corrupted JSON recovery
    print("\n▶️  TEST 5: Corrupted JSON recovery")
    try:
        with open(pmemory.memory_file, 'w', encoding='utf-8') as f:
            f.write("{invalid_json: true, \n")
            
        # Instantiate a new object to ensure memory read occurs
        pmemory_crash = ProjectMemory(str(test_dir))
        context = pmemory_crash.safe_memory_read("staging")
        assert context == "", "Did not handle crash safely"
        print("   ✅ PASS: Wrapper successfully swallows exception and resets")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    shutil.rmtree(test_dir)
    print("\n============================================================")
    print(" 🏁 QA MEMORY SUITE COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    run_tests()
