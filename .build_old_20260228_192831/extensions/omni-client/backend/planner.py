import logging
from typing import Dict, List, Literal, Any
from analytics_engine import analytics_engine

logger = logging.getLogger(__name__)

class InvalidGraphError(Exception):
    pass

class TaskNode:
    def __init__(self, node_id: str, node_type: str, payload: Dict[str, Any] = None):
        self.id = node_id
        self.type = node_type
        self.payload = payload or {}
        self.status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"] = "PENDING"
        self.result: Any = None
        self.error: str = None

class TaskGraph:
    def __init__(self, entry_node: str):
        self.nodes: Dict[str, TaskNode] = {}
        self.edges: Dict[str, List[str]] = {}
        self.entry_node = entry_node

    def add_node(self, node: TaskNode):
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []

    def add_edge(self, from_id: str, to_id: str):
        if from_id not in self.nodes or to_id not in self.nodes:
            raise ValueError(f"Cannot add edge: Nodes {from_id} and {to_id} must both exist in the graph.")
        self.edges[from_id].append(to_id)

    def get_next_nodes(self, node_id: str) -> List[str]:
        return self.edges.get(node_id, [])

    def validate_acyclic(self) -> bool:
        """Kahn's algorithm or DFS to detect cycles."""
        visited = set()
        rec_stack = set()

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in self.edges.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    raise InvalidGraphError("Graph contains a cycle.")
        return True

    def reset_states(self):
        for node in self.nodes.values():
            node.status = "PENDING"
            node.result = None
            node.error = None

class PlannerEngine:
    def __init__(self):
        self._handlers = {
            "analysis": self.handle_analysis,
            "code": self.handle_generation,
            "review": self.handle_review
        }

    def load_dummy_graph(self, intent_type: str, user_request: str = "") -> TaskGraph:
        """Returns a predefined graph based on intent type."""
        # For MVP, we provide a default complex_code_task template
        graph = TaskGraph(entry_node="analyze_request")
        
        request_msg = user_request if user_request else "the user's request"
        
        graph.add_node(TaskNode(node_id="analyze_request", node_type="analysis", payload={"message": f"Analyze the following request and plan the implementation: {request_msg}"}))
        graph.add_node(TaskNode(node_id="generate_code", node_type="code", payload={"message": f"Generate the code/files for: {request_msg}"}))
        graph.add_node(TaskNode(node_id="review_changes", node_type="review", payload={"message": f"Review and finalize: {request_msg}"}))

        graph.add_edge("analyze_request", "generate_code")
        graph.add_edge("generate_code", "review_changes")

        graph.validate_acyclic()
        return graph

    def emit_event(self, event_type: str, node_id: str, status: str, result: Any = None):
        """Stub for websocket/event-bus emission. Currently logs to standard backend logger."""
        event = {
            "type": event_type,
            "node_id": node_id,
            "status": status,
            "result": result
        }
        logger.info(f"EVENT EMITTED: {event}")
        # In a full React hookup, this would be pushed via FastAPI websockets.

    def execute_graph(self, graph: TaskGraph, context: dict) -> dict:
        """
        Executes a validated DAG sequentially (No parallel MVP). 
        Stops immediately on failure.
        """
        graph.validate_acyclic()
        graph.reset_states()

        completed_count = 0
        has_failed = False
        queue = [graph.entry_node]
        
        # Simple BFS/Sequential execution since edge logic currently represents strict dependency
        while queue:
            current_id = queue.pop(0)
            node = graph.nodes[current_id]
            
            # Transition to RUNNING
            node.status = "RUNNING"
            self.emit_event("dag_update", node.id, node.status)
            
            # Execute Handler
            handler = self._handlers.get(node.type)
            if not handler:
                node.status = "FAILED"
                node.error = f"No handler found for node type: {node.type}"
                self.emit_event("dag_update", node.id, node.status, {"error": node.error})
                has_failed = True
                break
                
            try:
                # Merge node payload and global context
                execution_context = {**context, **node.payload}
                result = handler(execution_context)
                
                node.status = "COMPLETED"
                node.result = result
                completed_count += 1
                self.emit_event("dag_update", node.id, node.status, result)
                
                # Queue dependencies
                next_nodes = graph.get_next_nodes(current_id)
                queue.extend(next_nodes)
                
            except Exception as e:
                logger.error(f"Node execution failed: {e}")
                node.status = "FAILED"
                node.error = str(e)
                has_failed = True
                self.emit_event("dag_update", node.id, node.status, {"error": node.error})
                break

        result_payload = {
            "completed_nodes": completed_count,
            "failed": has_failed,
            "final_state": {n.id: n.status for n in graph.nodes.values()}
        }
        
        analytics_engine.log_event("dag_failed" if has_failed else "dag_completed", result_payload)
        
        return result_payload

    def _build_dag_snapshot(self, graph: TaskGraph, current_node_id: str, template_context: dict = None) -> dict:
        """Build a full WebSocket-compatible dag_update payload."""
        nodes_list = []
        completed = 0
        for n in graph.nodes.values():
            nodes_list.append({"id": n.id, "status": n.status})
            if n.status == "COMPLETED":
                completed += 1
        total = len(graph.nodes)
        progress = round(completed / total, 2) if total > 0 else 0
        payload = {
            "type": "dag_update",
            "graph_id": "planner_dag",
            "nodes": nodes_list,
            "current_node": current_node_id,
            "progress": progress
        }
        if template_context:
            payload["template_context"] = template_context
        return payload

    def execute_graph_stream(self, graph: TaskGraph, context: dict, template_context: dict = None):
        """
        Generator that executes the DAG and yields dag_update snapshots
        at every state transition for real-time WebSocket forwarding.
        """
        graph.validate_acyclic()
        graph.reset_states()

        from explainability import ExplainabilityEmitter
        
        # Phase 7 Sprint 2: DAG Selection reasoning
        yield ExplainabilityEmitter.emit(
            source="planner",
            reason_code="dag_selection",
            summary=f"Using {len(graph.nodes)}-step execution plan for complex request.",
            context={"total_nodes": len(graph.nodes), "entry_node": graph.entry_node}
        )

        # Yield initial snapshot (everything PENDING)
        yield self._build_dag_snapshot(graph, graph.entry_node, template_context)

        completed_count = 0
        has_failed = False
        queue = [graph.entry_node]
        results = {}

        while queue:
            current_id = queue.pop(0)
            node = graph.nodes[current_id]

            node.status = "RUNNING"
            yield self._build_dag_snapshot(graph, current_id, template_context)
            
            # Phase 7 Sprint 2: Node Execution reasoning
            yield ExplainabilityEmitter.emit(
                source="planner",
                reason_code="node_execution",
                summary=f"Running '{node.type}' step -> node: {current_id}.",
                context={"node_id": current_id, "node_type": node.type, "previous_results": list(results.keys())}
            )

            handler = self._handlers.get(node.type)
            if not handler:
                node.status = "FAILED"
                node.error = f"No handler for type: {node.type}"
                has_failed = True
                yield self._build_dag_snapshot(graph, current_id, template_context)
                break

            try:
                # Merge node payload, global context, and previous results for context sharing
                execution_context = {**context, **node.payload, "previous_results": results}
                result = handler(execution_context)
                node.status = "COMPLETED"
                node.result = result
                results[current_id] = result
                completed_count += 1
                yield self._build_dag_snapshot(graph, current_id, template_context)

                next_nodes = graph.get_next_nodes(current_id)
                queue.extend(next_nodes)
            except Exception as e:
                logger.error(f"Node execution failed: {e}")
                node.status = "FAILED"
                node.error = str(e)
                has_failed = True
                yield self._build_dag_snapshot(graph, current_id, template_context)
                break
                
        # Phase 7 Sprint 5: Telemetry stream finish
        analytics_engine.log_event("dag_failed" if has_failed else "dag_completed", {
            "completed_nodes": completed_count,
            "failed": has_failed
        })

    # --- Real Handlers (Wired to Agent) ---
    
    def handle_analysis(self, context: dict) -> dict:
        runner = context.get("runner")
        if runner:
            prompt = f"Analyze this request and provide a detailed step-by-step technical plan: {context.get('message', '')}"
            res = runner(prompt)
            if not res or "402" in res:
                raise ValueError("API Quota Exhausted or Empty Analysis (402).")
            return {"action": "analyzed", "findings": res}
        return {"action": "analyzed", "findings": context.get("message", "")}

    def handle_generation(self, context: dict) -> dict:
        runner = context.get("runner")
        if runner:
            plan = context.get("previous_results", {}).get("analyze_request", {}).get("findings", "No plan available.")
            prompt = f"Based on this plan: {plan}\n\nActually implement every file and line of code mentioned for this requirement: {context.get('message', '')}. Use 'safe_write' for every file. Do not just describe the code, write it to disk."
            res = runner(prompt)
            if not res or "402" in res:
                raise ValueError("API Quota Exhausted or Empty Generation (402).")
            return {"action": "generated", "status": "success", "agent_response": res}
        return {"action": "generated", "status": "success"}

    def handle_review(self, context: dict) -> dict:
        runner = context.get("runner")
        if runner:
            prev = context.get("previous_results", {}).get("generate_code", {}).get("agent_response", "No code was generated.")
            prompt = f"Review the following implementation and confirm it meets all user goals: {context.get('message', '')}.\nImplementation summary: {prev}\nIf anything is missing (like a requested file), create it now using safe_write."
            res = runner(prompt)
            return {"action": "reviewed", "verdict": "approved", "agent_response": res}
        return {"action": "reviewed", "verdict": "approved"}
