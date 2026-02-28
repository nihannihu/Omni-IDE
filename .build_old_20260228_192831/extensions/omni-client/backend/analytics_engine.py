import json
import os
import datetime
from typing import Dict, Any, List

ANALYTICS_FILE = ".omni_analytics.json"
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

class AnalyticsEngine:
    def __init__(self, file_path=ANALYTICS_FILE):
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self):
        """Creates the file if it doesn't exist, rotates if > 10MB"""
        if not os.path.exists(self.file_path):
            self.reset_analytics()
        else:
            if os.path.getsize(self.file_path) > MAX_FILE_SIZE_BYTES:
                backup = f"{self.file_path}.bak"
                if os.path.exists(backup):
                    os.remove(backup)
                os.rename(self.file_path, backup)
                self.reset_analytics()

    def reset_analytics(self) -> dict:
        """Clears local analytics and returns the empty schema."""
        empty_schema = {
            "events": [],
            "aggregates": {
                "template_runs": {},
                "planner_executions": {},
                "insight_acceptance": {}
            }
        }
        with open(self.file_path, 'w') as f:
            json.dump(empty_schema, f, indent=2)
        return empty_schema

    def log_event(self, event_type: str, payload: dict):
        """Non-blocking deterministic write."""
        self._ensure_file()
        try:
            with open(self.file_path, 'r+') as f:
                data = json.load(f)
                
                event = {
                    "type": event_type,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "payload": payload
                }
                data["events"].append(event)
                
                # Rewind and overwrite safely
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
        except Exception:
            # Fallback to recreate if corrupted
            self.reset_analytics()
            self.log_event(event_type, payload)

    def _get_data(self) -> dict:
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception:
            return self.reset_analytics()

    # --- Aggregation Queries ---

    def get_usage_summary(self) -> dict:
        data = self._get_data()
        events = data.get("events", [])
        
        # Calculate rates dynamically from the raw event log
        workflows_total = 0
        workflows_success = 0
        
        templates_run = 0
        templates_unique = set()

        patches_total = 0
        patches_accepted = 0

        insights_total = 0
        insights_accepted = 0

        for e in events:
            t = e.get("type")
            p = e.get("payload", {})
            
            if t == "dag_completed":
                workflows_total += 1
                workflows_success += 1
            elif t == "dag_failed":
                workflows_total += 1
            
            elif t == "template_run":
                templates_run += 1
                if "template_id" in p:
                    templates_unique.add(p["template_id"])
                    
            elif t == "patch_applied":
                patches_total += 1
                patches_accepted += 1
            elif t == "patch_rejected":
                patches_total += 1
                
            elif t == "insight_trigger": # Generated insight
               insights_total += p.get("insight_count", 0)
            elif t == "insight_accepted":
                insights_accepted += 1

        workflow_success_rate = (workflows_success / workflows_total) if workflows_total > 0 else 1.0
        # Assume 10+ runs per session is 100% adoption target for metric purposes
        template_adoption_rate = min(templates_run / 10.0, 1.0) if templates_run > 0 else 0.0
        patch_acceptance_rate = (patches_accepted / patches_total) if patches_total > 0 else 1.0
        insight_acceptance_rate = (insights_accepted / insights_total) if insights_total > 0 else 0.0

        health_score = (
            (0.4 * workflow_success_rate) +
            (0.2 * template_adoption_rate) +
            (0.2 * patch_acceptance_rate) +
            (0.2 * insight_acceptance_rate)
        )

        return {
            "health_score": round(health_score, 2),
            "workflow_success_rate": round(workflow_success_rate, 2),
            "template_adoption_rate": round(template_adoption_rate, 2),
            "patch_acceptance_rate": round(patch_acceptance_rate, 2),
            "insight_acceptance_rate": round(insight_acceptance_rate, 2),
            "total_events": len(events)
        }

    def get_failure_rates(self) -> list:
        data = self._get_data()
        failures = [e for e in data.get("events", []) if e.get("type") == "dag_failed"]
        return failures[-50:] # Return last 50 failures for the UI

    def get_feature_adoption(self) -> dict:
        data = self._get_data()
        template_counts = {}
        for e in data.get("events", []):
            if e.get("type") == "template_run":
                tid = e.get("payload", {}).get("template_id", "unknown")
                template_counts[tid] = template_counts.get(tid, 0) + 1
                
        return {
            "most_used_template": max(template_counts, key=template_counts.get) if template_counts else "None",
            "template_breakdown": template_counts
        }

analytics_engine = AnalyticsEngine()
