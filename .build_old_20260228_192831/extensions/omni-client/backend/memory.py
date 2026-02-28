import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ProjectMemory:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.memory_file = os.path.join(workspace_dir, ".omni_memory.json")
        self.cache = None

    def load_memory(self) -> Dict[str, Any]:
        """Loads JSON from disk, validates schema, caches in memory.
        If corrupted -> logs warning and resets safely.
        """
        if not os.path.exists(self.memory_file):
            self._create_empty_memory()
            
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate core schema
            if not isinstance(data, dict) or "version" not in data or "knowledge_items" not in data:
                raise ValueError("Invalid schema: missing version or knowledge_items")
            
            self.cache = data
            return data
        except Exception as e:
            logger.warning(f"Memory corrupted or failed to load: {e}. Resetting safely.")
            self._create_empty_memory()
            return self.cache

    def _create_empty_memory(self):
        self.cache = {"version": 1, "knowledge_items": []}
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to create empty memory file: {e}")

    def get_relevant_memory(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Lowercase keyword matching against title, summary, relevance_hint.
        Rank by number of keyword matches. Return top_k items.
        """
        if self.cache is None:
            self.load_memory()
            
        query_words = set(query.lower().split())
        query_lower = query.lower()
        items = self.cache.get("knowledge_items", [])
        
        scored_items = []
        for item in items:
            score = 0
            
            # Check title
            title_words = set(item.get("title", "").lower().split())
            score += len(query_words.intersection(title_words))
            
            # Check summary
            summary_words = set(item.get("summary", "").lower().split())
            score += len(query_words.intersection(summary_words))
            
            # Check relevance hints
            hints = item.get("relevance_hint", [])
            for hint in hints:
                if hint.lower() in query_lower:
                    score += 2  # Higher weight for explicit hint match
                    
            if score > 0:
                scored_items.append((score, item))
                
        # Sort by score descending
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored_items[:top_k]]

    def format_memory_for_prompt(self, items: List[Dict[str, Any]]) -> str:
        """Convert retrieved items into concise bullet context. Max 300 tokens total (~1200 chars)."""
        if not items:
            return ""
            
        lines = []
        for item in items:
            cat = item.get("type", "context").replace("_", " ").title()
            title = item.get("title", "Untitled")
            summary = item.get("summary", "")
            lines.append(f"* [{cat}] {title}: {summary}")
            
        context = "\n".join(lines)
        if len(context) > 1200:
            context = context[:1197] + "..."
            
        return context

    def safe_memory_read(self, query: str, top_k: int = 3) -> str:
        """Wrapper that ensures system never crashes if memory fails."""
        try:
            items = self.get_relevant_memory(query, top_k)
            context = self.format_memory_for_prompt(items)
            return context
        except Exception as e:
            logger.error(f"Safe memory read failed: {e}")
            return ""

    def add_knowledge_item(self, item: Dict[str, Any]):
        """Helper to scaffold memory items (write-only basic support)."""
        if self.cache is None:
            self.load_memory()
        self.cache.setdefault("knowledge_items", []).append(item)
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to write knowledge item: {e}")
