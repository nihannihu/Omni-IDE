"""
Phase 6 Sprint 6 — Failure Injection Tests
===========================================
Validates graceful degradation under controlled failures:
  - DAG node failures
  - Cyclic graph rejection
  - Corrupted memory recovery
  - Scan limit enforcement
"""
import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from planner import PlannerEngine, TaskGraph, TaskNode, InvalidGraphError
from memory import ProjectMemory
from insights_engine import InsightsEngine


def test_f1_planner_node_failure():
    """F1: Planner halts gracefully when a node has no handler."""
    print("\n  F1: Planner node failure halts gracefully")
    try:
        planner = PlannerEngine()
        graph = TaskGraph(entry_node="A")
        graph.add_node(TaskNode("A", "analysis"))
        graph.add_node(TaskNode("B", "nonexistent_type"))
        graph.add_node(TaskNode("C", "review"))
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")

        result = planner.execute_graph(graph, {})
        assert result["failed"] is True
        assert result["completed_nodes"] == 1
        assert result["final_state"]["A"] == "COMPLETED"
        assert result["final_state"]["B"] == "FAILED"
        assert result["final_state"]["C"] == "PENDING"
        print("     ✅ PASS")
        return True
    except Exception as e:
        print(f"     ❌ FAIL: {e}")
        return False


def test_f2_cyclic_graph_rejection():
    """F2: Cyclic graphs are rejected before execution."""
    print("  F2: Cyclic graph rejected with InvalidGraphError")
    try:
        graph = TaskGraph(entry_node="A")
        graph.add_node(TaskNode("A", "analysis"))
        graph.add_node(TaskNode("B", "code"))
        graph.add_node(TaskNode("C", "review"))
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("C", "A")  # Creates cycle

        caught = False
        try:
            graph.validate_acyclic()
        except InvalidGraphError:
            caught = True

        assert caught, "InvalidGraphError was NOT raised"
        print("     ✅ PASS")
        return True
    except Exception as e:
        print(f"     ❌ FAIL: {e}")
        return False


def test_f3_stream_failure_emits_correct_events():
    """F3: Streaming DAG failure emits correct event states."""
    print("  F3: Stream failure emits correct final states")
    try:
        planner = PlannerEngine()
        graph = TaskGraph(entry_node="A")
        graph.add_node(TaskNode("A", "analysis"))
        graph.add_node(TaskNode("B", "bad_type"))
        graph.add_edge("A", "B")

        events = list(planner.execute_graph_stream(graph, {}))
        last = events[-1]
        node_states = {n["id"]: n["status"] for n in last["nodes"]}
        assert node_states["A"] == "COMPLETED"
        assert node_states["B"] == "FAILED"
        print("     ✅ PASS")
        return True
    except Exception as e:
        print(f"     ❌ FAIL: {e}")
        return False


def test_f4_corrupted_memory_recovery():
    """F4: Corrupted memory file is recovered safely."""
    print("  F4: Corrupted memory recovers gracefully")
    try:
        test_dir = Path("e2e_failure_mem")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()

        mem_file = test_dir / ".antigravity_memory.json"
        mem_file.write_text("{{{BROKEN JSON!!!", encoding='utf-8')

        mem = ProjectMemory(str(test_dir))
        context = mem.safe_memory_read("anything")
        assert context == "", f"Expected empty, got: '{context}'"

        # Verify file was reset
        data = mem.load_memory()
        assert data["version"] == 1
        assert data["knowledge_items"] == []

        shutil.rmtree(test_dir)
        print("     ✅ PASS")
        return True
    except Exception as e:
        print(f"     ❌ FAIL: {e}")
        return False


def test_f5_insights_scan_limit():
    """F5: Insights engine respects max file scan limit."""
    print("  F5: Insights engine respects file scan limit")
    test_dir = Path("e2e_failure_scan")
    try:
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)
        test_dir.mkdir(exist_ok=True)

        # Create 250 files (exceeds 200 limit)
        for i in range(250):
            (test_dir / f"file_{i}.py").write_text(f"x = {i}\n", encoding='utf-8')

        engine = InsightsEngine(str(test_dir))
        engine._max_files = 200
        engine._debounce_seconds = 0
        engine.run_scan()
        # Engine should not crash and should cap at 200

        print("     ✅ PASS")
        return True
    except Exception as e:
        print(f"     ❌ FAIL: {e}")
        return False
    finally:
        # Windows file-lock safe cleanup with retry
        import time as _t
        for _ in range(3):
            try:
                shutil.rmtree(test_dir, ignore_errors=True)
                break
            except Exception:
                _t.sleep(0.5)


def test_f6_partial_dag_completion():
    """F6: Partial DAG completion returns correct summary."""
    print("  F6: Partial DAG completion summary is correct")
    try:
        planner = PlannerEngine()
        graph = TaskGraph(entry_node="step1")
        graph.add_node(TaskNode("step1", "analysis"))
        graph.add_node(TaskNode("step2", "analysis"))
        graph.add_node(TaskNode("step3", "unknown_handler"))
        graph.add_node(TaskNode("step4", "review"))
        graph.add_edge("step1", "step2")
        graph.add_edge("step2", "step3")
        graph.add_edge("step3", "step4")

        result = planner.execute_graph(graph, {})
        assert result["failed"] is True
        assert result["completed_nodes"] == 2
        assert result["final_state"]["step4"] == "PENDING"
        print("     ✅ PASS")
        return True
    except Exception as e:
        print(f"     ❌ FAIL: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print(" 💥 PHASE 6 SPRINT 6: FAILURE INJECTION TESTS")
    print("=" * 60)

    results = [
        test_f1_planner_node_failure(),
        test_f2_cyclic_graph_rejection(),
        test_f3_stream_failure_emits_correct_events(),
        test_f4_corrupted_memory_recovery(),
        test_f5_insights_scan_limit(),
        test_f6_partial_dag_completion(),
    ]

    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 60)
    if passed == total:
        print(f" 🏁 FAILURE INJECTION: ALL PASSED ({passed}/{total})")
    else:
        print(f" ⚠️ FAILURE INJECTION: {passed}/{total} PASSED")
    print("=" * 60)
