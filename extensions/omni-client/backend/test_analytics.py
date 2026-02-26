import pytest
import os
import json
import time
from fastapi.testclient import TestClient
from main import app
from analytics_engine import AnalyticsEngine

TEST_ANALYTICS_FILE = ".test_analytics_loop.json"

@pytest.fixture
def engine():
    # Force a clean test file
    if os.path.exists(TEST_ANALYTICS_FILE):
        os.remove(TEST_ANALYTICS_FILE)
    
    eng = AnalyticsEngine(file_path=TEST_ANALYTICS_FILE)
    yield eng
    
    if os.path.exists(TEST_ANALYTICS_FILE):
        os.remove(TEST_ANALYTICS_FILE)

@pytest.fixture
def client(monkeypatch):
    # Mock the singleton in main.py
    eng = AnalyticsEngine(file_path=TEST_ANALYTICS_FILE)
    import main
    monkeypatch.setattr(main, "analytics_engine", eng)
    yield TestClient(app)

def test_event_logging(engine):
    """A1 — Event Logging: Trigger workflow → event recorded."""
    engine.log_event("test_event", {"val": 1})
    data = engine._get_data()
    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == "test_event"

def test_aggregation_accuracy(engine):
    """A2 — Aggregation Accuracy: Summary counts match."""
    # Seed events
    engine.log_event("dag_completed", {})
    engine.log_event("dag_completed", {})
    engine.log_event("dag_failed", {}) # 2/3 success = 0.67
    
    engine.log_event("template_run", {"template_id": "tpl1"})
    engine.log_event("template_run", {"template_id": "tpl1"})
    
    summary = engine.get_usage_summary()
    assert summary["workflow_success_rate"] == 0.67
    assert summary["total_events"] == 5

def test_health_score_calculation(engine):
    """Verify health score formula."""
    # 100% success on all fronts
    engine.log_event("dag_completed", {})
    engine.log_event("template_run", {"template_id": "t1"})
    # Seed 10 template runs for 1.0 adoption
    for _ in range(10): engine.log_event("template_run", {"template_id": "t1"})
    engine.log_event("patch_applied", {})
    engine.log_event("insight_trigger", {"insight_count": 1})
    engine.log_event("insight_accepted", {})
    
    summary = engine.get_usage_summary()
    # health_score = (0.4 * 1.0) + (0.2 * 1.0) + (0.2 * 1.0) + (0.2 * 1.0) = 1.0
    assert summary["health_score"] == 1.0

def test_api_endpoints(client):
    """A4 — API Contract."""
    # Seed one event
    client.get("/api/analytics/summary") # Triggers log if needed or just reads
    
    resp = client.get("/api/analytics/summary")
    assert resp.status_code == 200
    assert "health_score" in resp.json()
    
    resp = client.get("/api/analytics/workflows")
    assert resp.status_code == 200
    assert "most_used_template" in resp.json()

def test_file_rotation(monkeypatch):
    """E2 — Large Event Volume: Rotation triggers correctly."""
    # Mock MAX_FILE_SIZE_BYTES to something tiny
    import analytics_engine
    monkeypatch.setattr(analytics_engine, "MAX_FILE_SIZE_BYTES", 100) # 100 bytes
    
    test_file = ".test_rotate.json"
    if os.path.exists(test_file): os.remove(test_file)
    
    eng = AnalyticsEngine(file_path=test_file)
    # Log enough to exceed 100 bytes
    for _ in range(10):
        eng.log_event("long_event_name_to_fill_space", {"data": "some string content"})
    
    assert os.path.exists(f"{test_file}.bak")
    
    if os.path.exists(test_file): os.remove(test_file)
    if os.path.exists(f"{test_file}.bak"): os.remove(f"{test_file}.bak")
