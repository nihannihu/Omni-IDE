"""
Phase 6 Sprint 6 — Performance Baseline Tests
==============================================
Measures and records performance metrics for the Intelligence Layer:
  - DAG execution latency
  - Memory load time
  - Insights scan duration
  - Event throughput
"""
import os
import sys
import json
import time
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from planner import PlannerEngine
from memory import ProjectMemory
from insights_engine import InsightsEngine

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'reports')


def measure_dag_latency():
    """Measure DAG execution and stream latency."""
    planner = PlannerEngine()
    graph = planner.load_dummy_graph("complex")

    start = time.perf_counter()
    result = planner.execute_graph(graph, {"task": "benchmark"})
    dag_exec_ms = (time.perf_counter() - start) * 1000

    graph.reset_states()
    start = time.perf_counter()
    events = list(planner.execute_graph_stream(graph, {"task": "benchmark"}))
    dag_stream_ms = (time.perf_counter() - start) * 1000

    return {
        "dag_execute_ms": round(dag_exec_ms, 3),
        "dag_stream_ms": round(dag_stream_ms, 3),
        "events_emitted": len(events),
        "events_per_second": round(len(events) / (dag_stream_ms / 1000), 1) if dag_stream_ms > 0 else 0
    }


def measure_memory_latency():
    """Measure memory load and retrieval time."""
    test_dir = Path("perf_test_mem")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    mem = ProjectMemory(str(test_dir))

    # Load (creates empty file)
    start = time.perf_counter()
    mem.load_memory()
    load_ms = (time.perf_counter() - start) * 1000

    # Add items for retrieval test
    for i in range(20):
        mem.add_knowledge_item({
            "id": f"ki-{i}", "type": "note",
            "title": f"Architecture rule {i}",
            "summary": f"This is test knowledge item number {i} about staging and diff patterns.",
            "created_at": "2026-02-21T10:00:00Z",
            "tags": ["test"], "relevance_hint": ["staging", "diff", "pattern"]
        })

    # Retrieval
    start = time.perf_counter()
    items = mem.get_relevant_memory("staging diff pattern", top_k=5)
    retrieval_ms = (time.perf_counter() - start) * 1000

    # Formatting
    start = time.perf_counter()
    text = mem.format_memory_for_prompt(items)
    format_ms = (time.perf_counter() - start) * 1000

    shutil.rmtree(test_dir)

    return {
        "memory_load_ms": round(load_ms, 3),
        "memory_retrieval_ms": round(retrieval_ms, 3),
        "memory_format_ms": round(format_ms, 3),
        "items_retrieved": len(items)
    }


def measure_insights_latency():
    """Measure insights scan latency on a realistic workspace."""
    test_dir = Path("perf_test_insights")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    # Create 50 varied files
    for i in range(50):
        content = f"# TODO: Fix item {i}\n" + "\n".join([f"x_{j} = {j}" for j in range(30)])
        (test_dir / f"module_{i}.py").write_text(content, encoding='utf-8')

    engine = InsightsEngine(str(test_dir))
    engine._debounce_seconds = 0

    start = time.perf_counter()
    insights = engine.run_scan()
    scan_ms = (time.perf_counter() - start) * 1000

    shutil.rmtree(test_dir)

    return {
        "insights_scan_ms": round(scan_ms, 3),
        "insights_count": len(insights),
        "files_scanned": 50
    }


def write_report(metrics: dict):
    """Write performance baseline to JSON report."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "performance_baseline.json")

    report = {
        "phase": "Phase 6 Intelligence Layer",
        "sprint": "Sprint 6 — Performance Baseline",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "metrics": metrics,
        "thresholds": {
            "dag_execute_max_ms": 100,
            "memory_load_max_ms": 50,
            "memory_retrieval_max_ms": 10,
            "insights_scan_max_ms": 2000
        }
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)

    return report_path


if __name__ == "__main__":
    print("=" * 60)
    print(" ⚡ PHASE 6 SPRINT 6: PERFORMANCE BASELINE")
    print("=" * 60)

    all_metrics = {}

    print("\n  📊 Measuring DAG execution latency...")
    dag_metrics = measure_dag_latency()
    all_metrics["dag"] = dag_metrics
    print(f"     Execute: {dag_metrics['dag_execute_ms']}ms")
    print(f"     Stream:  {dag_metrics['dag_stream_ms']}ms")
    print(f"     Events:  {dag_metrics['events_emitted']} ({dag_metrics['events_per_second']}/sec)")

    print("\n  📊 Measuring Memory latency...")
    mem_metrics = measure_memory_latency()
    all_metrics["memory"] = mem_metrics
    print(f"     Load:      {mem_metrics['memory_load_ms']}ms")
    print(f"     Retrieval: {mem_metrics['memory_retrieval_ms']}ms")
    print(f"     Format:    {mem_metrics['memory_format_ms']}ms")

    print("\n  📊 Measuring Insights scan latency...")
    ins_metrics = measure_insights_latency()
    all_metrics["insights"] = ins_metrics
    print(f"     Scan:     {ins_metrics['insights_scan_ms']}ms")
    print(f"     Insights: {ins_metrics['insights_count']} found")

    report_path = write_report(all_metrics)

    # Threshold validation
    print("\n  🎯 Threshold Check:")
    checks = [
        ("DAG Execute < 100ms", dag_metrics["dag_execute_ms"] < 100),
        ("Memory Load < 50ms", mem_metrics["memory_load_ms"] < 50),
        ("Memory Retrieval < 10ms", mem_metrics["memory_retrieval_ms"] < 10),
        ("Insights Scan < 2000ms", ins_metrics["insights_scan_ms"] < 2000),
    ]
    all_pass = True
    for label, ok in checks:
        status = "✅" if ok else "❌"
        print(f"     {status} {label}")
        if not ok:
            all_pass = False

    print(f"\n  📁 Report written to: {report_path}")
    print("\n" + "=" * 60)
    if all_pass:
        print(" 🏁 PERFORMANCE BASELINE: ALL THRESHOLDS MET")
    else:
        print(" ⚠️ PERFORMANCE BASELINE: SOME THRESHOLDS EXCEEDED")
    print("=" * 60)
