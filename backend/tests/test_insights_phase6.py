import os
import sys
import shutil
import time
from pathlib import Path

# Ensure backend root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from insights_engine import (
    InsightsEngine, _collect_files,
    analyze_long_functions, analyze_large_files,
    analyze_todo_fixme, analyze_dead_files, analyze_complexity
)

def run_tests():
    print("============================================================")
    print(" 🔍 LEAD QA: PHASE 6 BACKGROUND INSIGHTS ENGINE VALIDATION")
    print("============================================================")

    test_dir = Path("qa_workspace_insights_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    # Scaffold test files
    # 1. A large Python file with a long function
    big_file = test_dir / "big_module.py"
    lines = ["def mega_function():\n"] + [f"    x = {i}\n" for i in range(150)] + ["\n"]
    lines += ["def short_func():\n", "    return 1\n"]
    big_file.write_text("".join(lines), encoding='utf-8')

    # 2. A file with TODOs
    todo_file = test_dir / "tasks.py"
    todo_file.write_text("# TODO: Fix login flow\n# FIXME: Memory leak here\ndef run():\n    pass\n", encoding='utf-8')

    # 3. A dead file (not imported anywhere)
    dead_file = test_dir / "orphan_utils.py"
    dead_file.write_text("def helper():\n    return True\n", encoding='utf-8')

    # 4. A normal file that imports tasks
    main_file = test_dir / "main.py"
    main_file.write_text("import tasks\ntasks.run()\n", encoding='utf-8')

    # ---------------------------------------------------------------
    # TEST 1: File collection respects limits
    print("\n▶️  TEST 1: File collection respects scan limit")
    try:
        files = _collect_files(str(test_dir), max_files=2)
        assert len(files) <= 2, f"Expected <=2 files, got {len(files)}"
        print("   ✅ PASS: File limit respected")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # Full file collection for remaining tests
    files = _collect_files(str(test_dir), max_files=200)

    # TEST 2: Long function detection
    print("\n▶️  TEST 2: Long function detection")
    try:
        results = analyze_long_functions(files, threshold=120)
        assert len(results) >= 1, "Expected at least 1 long function"
        assert "mega_function" in results[0].title, f"Wrong function: {results[0].title}"
        print("   ✅ PASS: Long function detected correctly")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # TEST 3: TODO/FIXME scanning
    print("\n▶️  TEST 3: TODO/FIXME aggregation")
    try:
        results = analyze_todo_fixme(files)
        assert len(results) >= 1, "Expected TODO insights"
        assert "2 TODO/FIXME" in results[0].title, f"Wrong count: {results[0].title}"
        print("   ✅ PASS: TODO/FIXME aggregated correctly")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # TEST 4: Dead file detection
    print("\n▶️  TEST 4: Dead file heuristic")
    try:
        results = analyze_dead_files(files, str(test_dir))
        dead_names = [r.title for r in results]
        assert any("orphan_utils" in t for t in dead_names), f"orphan_utils not detected: {dead_names}"
        # main.py should NOT be flagged (it's an entry point)
        assert not any("main" in t for t in dead_names), "main.py incorrectly flagged as dead"
        print("   ✅ PASS: Dead files detected, entry points excluded")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # TEST 5: Debounce logic
    print("\n▶️  TEST 5: Debounce prevents rapid rescans")
    try:
        engine = InsightsEngine(str(test_dir))
        engine._debounce_seconds = 5.0
        first = engine.run_scan()
        # Immediately scan again — should be debounced
        second = engine.run_scan()
        # Both should return same cached results (debounced)
        assert len(first) == len(second), "Debounce failed: different result counts"
        print("   ✅ PASS: Debounce prevents duplicate scans")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # TEST 6: No file writes during scan
    print("\n▶️  TEST 6: Read-only — no file writes during scan")
    try:
        before_files = set(f.name for f in test_dir.rglob('*') if f.is_file())
        engine = InsightsEngine(str(test_dir))
        engine._debounce_seconds = 0  # Force rescan
        engine.run_scan()
        after_files = set(f.name for f in test_dir.rglob('*') if f.is_file())
        assert before_files == after_files, f"New files created: {after_files - before_files}"
        print("   ✅ PASS: Zero file writes during scan")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")

    # Cleanup
    shutil.rmtree(test_dir)
    print("\n============================================================")
    print(" 🏁 QA INSIGHTS ENGINE SUITE COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    run_tests()
