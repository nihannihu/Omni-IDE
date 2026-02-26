# ══════════════════════════════════════════════════════════════════
# 🧠 Omni-IDE — Intent Router (v2.0 — NO HuggingFace)
# ══════════════════════════════════════════════════════════════════
# Uses Gemini via LiteLLM for LLM-powered intent classification.
# Falls back to keyword heuristics if LLM is unavailable.
# ══════════════════════════════════════════════════════════════════

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

from analytics_engine import analytics_engine


class IntentRouter:
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        if not self.gemini_key:
            logger.warning("GEMINI_API_KEY missing! Router will use heuristics only.")

    def _build_prompt(self, query: str) -> list:
        system_prompt = """You are the Omni-IDE Intent Router. 
Your job is to analyze the user's query and output a strict JSON strictly adhering to the schema below.
DO NOT output any markdown blocks, explanations, or text outside the JSON.

SCHEMA:
{
    "intent_type": "string (e.g., Code Generation, Refactoring, Debugging, Question)",
    "extracted_tools": ["list", "of", "required", "system", "tools", "(For simple file modifications, output EXACTLY ONE primary tool such as 'safe_write' or 'safe_delete', do NOT list 'safe_open' alongside 'safe_write')"],
    "extracted_files": ["list", "of", "files", "mentioned"],
    "confidence_score": 0.0 to 1.0 (float)
}"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

    def route_intent(self, query: str) -> Dict[str, Any]:
        """
        Routes the user's query through the Intelligence Layer.
        Uses Gemini via LiteLLM, falls back to heuristics.
        """
        # If no Gemini key, skip LLM and go straight to heuristics
        if not self.gemini_key:
            return self._heuristic_fallback(query)
        
        messages = self._build_prompt(query)
        
        try:
            import litellm
            response = litellm.completion(
                model="gemini/gemini-1.5-pro-latest",
                api_key=self.gemini_key,
                messages=messages,
                max_tokens=300,
            )
            raw_response = response.choices[0].message.content
            
            # Parse JSON (with fallback cleanup)
            try:
                parsed_data = json.loads(raw_response)
            except json.JSONDecodeError:
                clean = raw_response.replace("```json", "").replace("```", "").strip()
                parsed_data = json.loads(clean)

        except Exception as e:
            logger.error(f"Routing failed due to LLM error: {e}. Falling back to heuristics.")
            return self._heuristic_fallback(query)

        score = float(parsed_data.get("confidence_score", 0.0))
        extracted_tools = parsed_data.get("extracted_tools", [])
        extracted_files = parsed_data.get("extracted_files", [])

        # 1. Evaluate Confidence Threshold
        if score < self.confidence_threshold:
            return {
                "execution_path": "Clarification Needed",
                "reason": f"Confidence score {score} falls below threshold {self.confidence_threshold}.",
                "raw_data": parsed_data
            }

        # 2. Evaluate Complexity Heuristics (Planner vs Direct)
        if len(extracted_tools) > 1 or len(extracted_files) > 1:
            execution_path = "Task Graph Planner"
            reason = "Task is complex (requires >1 tool or >1 file)."
        else:
            execution_path = "Direct Execution"
            reason = "Task is simple (requires <=1 tool and <=1 file)."

        result = {
            "execution_path": execution_path,
            "reason": reason,
            "raw_data": parsed_data
        }

        # Phase 7 Sprint 5: Telemetry Hook
        analytics_engine.log_event("route_selected", {
            "execution_path": execution_path, 
            "confidence": score
        })

        return result

    def _heuristic_fallback(self, query: str) -> Dict[str, Any]:
        """Pure keyword-based routing when LLM is unavailable."""
        query_lower = query.lower()
        complex_keywords = ["create", "build", "implement", "scaffold", "make", "setup", "complete"]
        complexity_signals = ["game", "app", "dashboard", "page", "system", "feature", "module"]
        
        is_complex = any(k in query_lower for k in complex_keywords) and \
                     any(s in query_lower for s in complexity_signals)
        
        if is_complex:
            return {
                "execution_path": "Task Graph Planner",
                "reason": "Heuristic: Complex keywords detected (LLM unavailable).",
                "confidence": 0.9,
                "raw_data": {"confidence_score": 0.9}
            }
        return {
            "execution_path": "Direct Execution",
            "reason": "Heuristic: Simple query detected (LLM unavailable).",
            "confidence": 0.9,
            "raw_data": {"confidence_score": 0.9}
        }
