import pytest
import os
import json
from fastapi.testclient import TestClient
from main import app
from feedback_store import FeedbackStore

# Use a temporary file for testing to avoid polluting actual data
TEST_FEEDBACK_FILE = ".test_feedback.json"

@pytest.fixture
def feedback_store():
    store = FeedbackStore(filepath=TEST_FEEDBACK_FILE)
    yield store
    if os.path.exists(TEST_FEEDBACK_FILE):
        os.remove(TEST_FEEDBACK_FILE)

@pytest.fixture
def client(feedback_store):
    # Override the store globally imported in main.py for the test duration
    import main
    original_store = main.feedback_store
    main.feedback_store = feedback_store
    yield TestClient(app)
    main.feedback_store = original_store

def test_submit_upvote(client, feedback_store):
    """1. Submit 👍 feedback -> record saved"""
    response = client.post("/api/feedback", json={
        "event_id": "test_event_1",
        "module": "router",
        "rating": "up",
        "context": {"intent": "test"}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    data = feedback_store._read_all()
    assert len(data) == 1
    assert data[0]["event_id"] == "test_event_1"
    assert data[0]["rating"] == "up"
    assert data[0]["module"] == "router"

def test_submit_downvote_with_comment(client, feedback_store):
    """2. Submit 👎 with comment -> comment persisted"""
    response = client.post("/api/feedback", json={
        "event_id": "test_event_2",
        "module": "planner",
        "rating": "down",
        "comment": "Did not use the right tool."
    })
    
    assert response.status_code == 200
    data = feedback_store._read_all()
    assert len(data) == 1
    assert data[0]["comment"] == "Did not use the right tool."
    assert data[0]["rating"] == "down"

def test_invalid_schema_rejected(client):
    """Edge Case: Invalid schema rejected"""
    response = client.post("/api/feedback", json={
        "event_id": "test_event_3",
        "module": "invalid_module", # Should fail
        "rating": "up"
    })
    assert response.status_code == 400

    response2 = client.post("/api/feedback", json={
        "event_id": "test_event_4",
        "module": "planner",
        "rating": "neutral" # Should fail
    })
    assert response2.status_code == 400

def test_feedback_stats_aggregates(client, feedback_store):
    """4. Multiple modules produce separate stats"""
    client.post("/api/feedback", json={"event_id": "1", "module": "router", "rating": "up"})
    client.post("/api/feedback", json={"event_id": "2", "module": "router", "rating": "up"})
    client.post("/api/feedback", json={"event_id": "3", "module": "router", "rating": "down"})
    client.post("/api/feedback", json={"event_id": "4", "module": "planner", "rating": "up"})
    
    global_stats = feedback_store.get_feedback_stats()
    assert global_stats["total_feedback_count"] == 4
    assert global_stats["approval_rate"] == 0.75
    assert global_stats["rejection_rate"] == 0.25
    
    router_stats = feedback_store.get_module_score("router")
    assert router_stats["total_feedback_count"] == 3
    assert router_stats["approval_rate"] == 0.67 # 2/3
