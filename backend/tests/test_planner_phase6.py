import pytest
from planner import PlannerEngine, TaskGraph, TaskNode, InvalidGraphError

def test_graph_validation_cyclic():
    graph = TaskGraph(entry_node="A")
    graph.add_node(TaskNode("A", "analysis"))
    graph.add_node(TaskNode("B", "code"))
    graph.add_node(TaskNode("C", "review"))
    
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("C", "A")  # Cycle

    with pytest.raises(InvalidGraphError):
        graph.validate_acyclic()

def test_sequential_execution():
    planner = PlannerEngine()
    graph = planner.load_dummy_graph("complex_code")
    
    result = planner.execute_graph(graph, {"test": "context"})
    
    assert result["failed"] is False
    assert result["completed_nodes"] == 3
    assert result["final_state"]["analyze_request"] == "COMPLETED"
    assert result["final_state"]["generate_code"] == "COMPLETED"
    assert result["final_state"]["review_changes"] == "COMPLETED"

def test_failure_halt():
    planner = PlannerEngine()
    graph = TaskGraph(entry_node="A")
    graph.add_node(TaskNode("A", "analysis"))
    
    # Intentionally trigger failure by giving a missing handler type
    graph.add_node(TaskNode("B", "unknown_type"))
    graph.add_node(TaskNode("C", "review"))

    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    
    result = planner.execute_graph(graph, {})
    
    assert result["failed"] is True
    assert result["completed_nodes"] == 1
    assert result["final_state"]["A"] == "COMPLETED"
    assert result["final_state"]["B"] == "FAILED"
    assert result["final_state"]["C"] == "PENDING"

def test_result_summary():
    planner = PlannerEngine()
    graph = planner.load_dummy_graph("test")
    result = planner.execute_graph(graph, {})
    
    assert "completed_nodes" in result
    assert "failed" in result
    assert "final_state" in result
