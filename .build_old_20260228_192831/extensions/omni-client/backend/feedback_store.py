import json
import os
import uuid
import datetime
from typing import Dict, Any, List, Optional, Literal
from analytics_engine import analytics_engine

FEEDBACK_FILE = ".omni_feedback.json"

class FeedbackStore:
    """
    Lightweight, local file-based store for Omni-IDE AI feedback.
    Appends new feedback and provides basic analytics queries without blocking.
    """
    
    def __init__(self, filepath: str = FEEDBACK_FILE):
        self.filepath = filepath
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)
                
    def _read_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
            
    def _write_all(self, data: List[Dict[str, Any]]):
        # We rewrite the whole list as it's an MVP. 
        # In a real system, you'd use a line-delimited JSON or DB to avoid loading everything.
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def add_feedback(
        self,
        event_id: str,
        module: Literal["router", "planner", "insight", "copilot"],
        rating: Literal["up", "down"],
        comment: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record a new feedback rating.
        """
        record = {
            "id": str(uuid.uuid4()),
            "event_id": event_id,
            "module": module,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "context": context or {}
        }
        
        data = self._read_all()
        data.append(record)
        self._write_all(data)
        
        # Analytics Hook
        analytics_engine.log_event("feedback_submitted", {
            "module": module,
            "rating": rating,
            "has_comment": bool(comment)
        })
        
        return record

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Compute global aggregates."""
        data = self._read_all()
        if not data:
            return {"total_feedback_count": 0, "approval_rate": 0.0, "rejection_rate": 0.0}
            
        total = len(data)
        upvotes = sum(1 for x in data if x.get("rating") == "up")
        downvotes = sum(1 for x in data if x.get("rating") == "down")
        
        return {
            "total_feedback_count": total,
            "approval_rate": round(upvotes / total, 2),
            "rejection_rate": round(downvotes / total, 2)
        }

    def get_module_score(self, module: str) -> Dict[str, Any]:
        """Compute aggregates for a specific module."""
        data = self._read_all()
        module_data = [x for x in data if x.get("module") == module]
        if not module_data:
            return {"total_feedback_count": 0, "approval_rate": 0.0, "rejection_rate": 0.0}
            
        total = len(module_data)
        upvotes = sum(1 for x in module_data if x.get("rating") == "up")
        downvotes = sum(1 for x in module_data if x.get("rating") == "down")
        
        return {
            "total_feedback_count": total,
            "approval_rate": round(upvotes / total, 2),
            "rejection_rate": round(downvotes / total, 2)
        }

    def get_recent_feedback(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch chronological list of the most recent feedback."""
        data = self._read_all()
        # Sort by timestamp descending
        data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return data[:limit]

# Singleton instance for the backend
feedback_store = FeedbackStore()
