import json
import time
import datetime
from typing import Dict, Any, List, Optional
from planner import TaskGraph, TaskNode, PlannerEngine
from analytics_engine import analytics_engine

TEMPLATES_FILE = ".omni_templates.json"
ANALYTICS_FILE = ".omni_analytics.json"

class TemplateRunner:
    """
    Loads declarative DAG templates and executes them via the Planner Engine,
    supporting parameter injection and local telemetry.
    """
    def __init__(self):
        self.templates = self._load_templates()
        self.planner = PlannerEngine()

    def _load_templates(self) -> List[Dict[str, Any]]:
        try:
            with open(TEMPLATES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def get_all(self) -> List[Dict[str, Any]]:
        return self.templates

    def get(self, template_id: str) -> Optional[Dict[str, Any]]:
        for t in self.templates:
            if t["id"] == template_id:
                return t
        return None

    def log_telemetry(self, template_id: str, duration_ms: float, status: str):
        analytics_engine.log_event("template_run", {
            "template_id": template_id,
            "duration_ms": duration_ms,
            "status": status
        })

    def execute(self, template_id: str, params: Dict[str, Any], emit_callback=None):
        template = self.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Validate params
        for p in template.get("params", []):
            if p.get("required") and p["name"] not in params:
                raise ValueError(f"Missing required parameter: {p['name']}")

        # Build Graph
        graph_def = template.get("graph", {})
        if not graph_def or "nodes" not in graph_def:
            raise ValueError("Template has no valid graph definition")

        # Determine entry node (nodes with no incoming edges)
        entry_nodes = set(n["id"] for n in graph_def["nodes"])
        for edge in graph_def.get("edges", []):
            if len(edge) == 2 and edge[1] in entry_nodes:
                entry_nodes.remove(edge[1])
        
        entry_node = list(entry_nodes)[0] if entry_nodes else graph_def["nodes"][0]["id"]
        graph = TaskGraph(entry_node=entry_node)

        # Build nodes
        for n_def in graph_def["nodes"]:
            payload = params.copy()
            graph.add_node(TaskNode(node_id=n_def["id"], node_type=n_def["type"], payload=payload))

        # Build edges
        for edge in graph_def.get("edges", []):
            if len(edge) == 2:
                graph.add_edge(edge[0], edge[1])

        template_context = {
            "template_id": template["id"],
            "template_name": template["name"],
            "params": params
        }

        start_time = time.time()
        status = "completed"
        
        try:
            # Execute synchronously, but pump events to the API endpoint's emitter callback
            for event in self.planner.execute_graph_stream(graph, context=params, template_context=template_context):
                if emit_callback:
                    emit_callback(event)
                
                # Sniff for failures to mark telemetry
                if isinstance(event, dict) and event.get("type") == "dag_update":
                    for n in event.get("nodes", []):
                        if n.get("status") == "FAILED":
                            status = "failed"
        except Exception as e:
            status = "failed"
            raise e
        finally:
            duration = (time.time() - start_time) * 1000
            self.log_telemetry(template_id, duration, status)

template_runner = TemplateRunner()
