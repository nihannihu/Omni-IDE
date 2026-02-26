import pytest
import json
from explainability import ExplainabilityEmitter

def test_explainability_event_schema_validation():
    """1. Event schema validation - Ensure payload correctly formatted."""
    payload = ExplainabilityEmitter.emit(
        source="router",
        reason_code="intent_classification",
        summary="Test summary",
        context={"conf": 0.9}
    )
    
    assert payload["__copilot_event__"] is True
    assert payload["type"] == "explainability_event"
    assert payload["source"] == "router"
    
    inner = payload["payload"]
    assert inner["type"] == "explainability_event"
    assert "timestamp" in inner
    assert inner["source"] == "router"
    assert inner["reason_code"] == "intent_classification"
    assert inner["summary"] == "Test summary"
    assert inner["context"]["conf"] == 0.9

def test_explainability_summary_truncation():
    """Ensure summary is truncated to 140 characters."""
    long_summary = "A" * 200
    payload = ExplainabilityEmitter.emit(
        source="planner",
        reason_code="dag_selection",
        summary=long_summary
    )
    assert len(payload["payload"]["summary"]) == 140

def test_json_serializability():
    """Ensure events are JSON serializable to send through WebSocket."""
    payload = ExplainabilityEmitter.emit(
        source="insights",
        reason_code="insight_trigger",
        summary="Background scan",
        context={"count": 5}
    )
    json_str = json.dumps(payload)
    assert "explainability_event" in json_str
    assert "insights" in json_str
