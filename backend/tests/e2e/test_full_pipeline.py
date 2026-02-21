"""
Phase 6 Sprint 6 — E2E Full Pipeline Integration Tests
=======================================================
Validates the complete Intelligence Layer execution flow:
  Router → Planner → Memory → Timeline Events → Insights
"""
import os
import sys
import json
import shutil
import time
from pathlib import Path

# Ensure backend root on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from planner import PlannerEngine, TaskGraph, TaskNode, InvalidGraphError
from memory import ProjectMemory
from insights_engine import InsightsEngine


def test_scenario_a_simple_flow():
    """Scenario A: Simple Intent → Direct Execution → Memory + Insights."""
    print("\n" + "="*60)
    print(" SCENARIO A: Simple Intent Flow (Direct Execution)")
    print("="*60)
    passed = 0
    total = 4

    # A1: Memory loads without crash
    print("\n  A1: Memory loads cleanly")
    test_dir = Path("e2e_test_workspace_a")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    try:
        mem = ProjectMemory(str(test_dir))
        data = mem.load_memory()
        assert data["version"] == 1
        assert isinstance(data["knowledge_items"], list)
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # A2: Memory injection returns empty string for blank memory
    print("  A2: Memory safe_read returns empty for blank memory")
    try:
        context = mem.safe_memory_read("test query")
        assert context == "", f"Expected empty, got: '{context}'"
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # A3: Insights engine scans without crash on minimal workspace
    print("  A3: Insights engine runs on minimal workspace")
    try:
        (test_dir / "app.py").write_text("def main():\n    pass\n", encoding='utf-8')
        engine = InsightsEngine(str(test_dir))
        results = engine.run_scan()
        assert isinstance(results, list)
        print(f"     ✅ PASS ({len(results)} insights)")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # A4: Insights text formatting works
    print("  A4: Insights text formatter does not crash")
    try:
        text = engine.format_insights_text()
        assert isinstance(text, str)
        assert len(text) > 0
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    shutil.rmtree(test_dir)
    print(f"\n  SCENARIO A RESULT: {passed}/{total} PASSED")
    return passed, total


def test_scenario_b_complex_dag():
    """Scenario B: Complex DAG Execution → Timeline → Aggregation."""
    print("\n" + "="*60)
    print(" SCENARIO B: Complex DAG Execution Pipeline")
    print("="*60)
    passed = 0
    total = 5

    planner = PlannerEngine()
    graph = planner.load_dummy_graph("complex_code")

    # B1: Graph loads with correct node count
    print("\n  B1: Graph loads with correct structure")
    try:
        assert len(graph.nodes) == 3
        assert graph.entry_node == "analyze_request"
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # B2: Acyclic validation passes
    print("  B2: Acyclic validation passes")
    try:
        assert graph.validate_acyclic() is True
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # B3: Sequential execution completes all nodes
    print("  B3: Sequential execution completes all nodes")
    try:
        result = planner.execute_graph(graph, {"task": "test"})
        assert result["failed"] is False
        assert result["completed_nodes"] == 3
        for nid, status in result["final_state"].items():
            assert status == "COMPLETED", f"Node {nid} is {status}"
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # B4: Stream emits correct event count
    print("  B4: Stream emits correct event count")
    try:
        graph.reset_states()
        events = list(planner.execute_graph_stream(graph, {"task": "test"}))
        # Expected: 1 initial + 2 per node (RUNNING + COMPLETED) = 7
        assert len(events) == 7, f"Expected 7 events, got {len(events)}"
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # B5: Final event has progress == 1.0
    print("  B5: Final event progress = 1.0")
    try:
        last_event = events[-1]
        assert last_event["progress"] == 1.0, f"Final progress: {last_event['progress']}"
        assert last_event["type"] == "dag_update"
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    print(f"\n  SCENARIO B RESULT: {passed}/{total} PASSED")
    return passed, total


def test_scenario_c_cross_module_logging():
    """Scenario C: Module integration and schema consistency."""
    print("\n" + "="*60)
    print(" SCENARIO C: Cross-Module Integration & Schema Checks")
    print("="*60)
    passed = 0
    total = 4

    # C1: dag_update event schema matches frontend contract
    print("\n  C1: dag_update event schema matches frontend contract")
    try:
        planner = PlannerEngine()
        graph = planner.load_dummy_graph("test")
        events = list(planner.execute_graph_stream(graph, {}))
        required_keys = {"type", "graph_id", "nodes", "current_node", "progress"}
        for evt in events:
            assert required_keys.issubset(evt.keys()), f"Missing keys: {required_keys - evt.keys()}"
            assert isinstance(evt["nodes"], list)
            for node in evt["nodes"]:
                assert "id" in node and "status" in node
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # C2: Insight event schema is valid
    print("  C2: Insight event schema is valid")
    try:
        test_dir = Path("e2e_test_workspace_c")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()
        (test_dir / "big.py").write_text("# TODO: fix this\ndef x():\n    pass\n", encoding='utf-8')
        engine = InsightsEngine(str(test_dir))
        insights = engine.run_scan()
        required_insight_keys = {"id", "type", "severity", "title", "description", "file", "created_at"}
        for ins in insights:
            assert required_insight_keys.issubset(ins.keys()), f"Missing: {required_insight_keys - ins.keys()}"
            assert ins["severity"] in ("low", "medium", "high")
        shutil.rmtree(test_dir)
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # C3: Memory schema is valid
    print("  C3: Memory JSON schema is valid")
    try:
        test_dir = Path("e2e_test_workspace_c3")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()
        mem = ProjectMemory(str(test_dir))
        mem.load_memory()
        raw = json.loads((test_dir / ".antigravity_memory.json").read_text(encoding='utf-8'))
        assert "version" in raw
        assert "knowledge_items" in raw
        assert isinstance(raw["knowledge_items"], list)
        shutil.rmtree(test_dir)
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    # C4: TaskNode state enum consistency
    print("  C4: TaskNode state enum consistency")
    try:
        valid_states = {"PENDING", "RUNNING", "COMPLETED", "FAILED"}
        node = TaskNode("test", "analysis")
        assert node.status in valid_states
        node.status = "RUNNING"
        assert node.status in valid_states
        node.status = "COMPLETED"
        assert node.status in valid_states
        print("     ✅ PASS")
        passed += 1
    except Exception as e:
        print(f"     ❌ FAIL: {e}")

    print(f"\n  SCENARIO C RESULT: {passed}/{total} PASSED")
    return passed, total


if __name__ == "__main__":
    print("=" * 60)
    print(" 🧪 PHASE 6 SPRINT 6: FULL E2E PIPELINE VALIDATION")
    print("=" * 60)

    results = []
    results.append(test_scenario_a_simple_flow())
    results.append(test_scenario_b_complex_dag())
    results.append(test_scenario_c_cross_module_logging())

    total_p = sum(r[0] for r in results)
    total_t = sum(r[1] for r in results)

    print("\n" + "=" * 60)
    if total_p == total_t:
        print(f" 🏁 E2E PIPELINE: ALL PASSED ({total_p}/{total_t})")
    else:
        print(f" ⚠️ E2E PIPELINE: {total_p}/{total_t} PASSED")
    print("=" * 60)
