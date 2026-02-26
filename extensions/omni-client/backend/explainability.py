import datetime
from typing import Literal, Dict, Any, Optional

class ExplainabilityEmitter:
    """
    Standardized emitter for explainability events across the Intelligence Layer.
    Emits serializable JSON-compatible dicts to be yielded through the agent stream.
    """

    @staticmethod
    def emit(
        source: Literal["router", "planner", "insights", "orchestrator"],
        reason_code: str,
        summary: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates a structured explainability event payload.
        
        Args:
            source: The backend module generating the event.
            reason_code: Machine-readable identifier for the decision type
                         (e.g., 'intent_classification', 'dag_selection', 'node_execution').
            summary: Human-readable explanation of the decision (<140 chars).
            context: Optional dictionary containing execution-specific context.
            
        Returns:
            A dictionary tagged with '__copilot_event__' for WebSocket routing.
        """
        payload = {
            "type": "explainability_event",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": source,
            "reason_code": reason_code,
            "summary": summary[:140],  # Enforce <140 char constraint
            "context": context or {}
        }

        # Tag for WebSocket detection
        return {
            "__copilot_event__": True,
            "source": source,
            "type": "explainability_event",
            "payload": payload
        }
