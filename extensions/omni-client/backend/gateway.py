# ══════════════════════════════════════════════════════════════════
# 🧠 Omni-IDE — Hybrid Intelligence Gateway (v2.1)
# ══════════════════════════════════════════════════════════════════
#
#  Two-tier routing — NO HuggingFace:
#    CLOUD  →  Gemini 1.5 Pro  (PRIMARY for all user tasks)
#    LOCAL  →  Auto-detected Ollama model (offline fallback only)
#
#  The gateway auto-detects which models Ollama has installed and
#  picks the best one. Small local models (3B) are too weak for
#  smolagents' structured tool-calling, so Cloud is always primary.
#
# ══════════════════════════════════════════════════════════════════

import os
import re
import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ── Load environment ─────────────────────────────────────────
try:
    from config import ENV_PATH
    load_dotenv(ENV_PATH, override=True)
except ImportError:
    load_dotenv()

# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════

class ModelTier(Enum):
    CLOUD = "cloud"
    LOCAL = "local"


@dataclass
class RoutingDecision:
    tier: ModelTier
    model_id: str
    reason: str
    trigger_keyword: Optional[str] = None
    context_size: int = 0
    is_fallback: bool = False
    latency_ms: float = 0.0


# Trigger words that indicate a complex, reasoning-heavy task.
COMPLEXITY_TRIGGERS = frozenset({
    "refactor", "architect", "design", "explain", "debug",
    "why", "analyze", "plan", "optimize", "review",
    "migrate", "security", "audit", "performance", "scale",
    "compare", "evaluate", "strategy", "tradeoff", "trade-off",
})

# Context size threshold (in estimated tokens).
CONTEXT_THRESHOLD = 4000

# Model identifiers (LiteLLM format)
GEMINI_PRO_MODEL = "gemini/gemini-2.5-flash"


# Preferred local models (in order of preference)
OLLAMA_PREFERRED_MODELS = [
    "qwen2.5-coder:7b",
    "qwen2.5-coder:3b",
    "qwen2.5-coder:1.5b",
    "qwen2.5:7b",
    "qwen2.5:3b",
    "llama3:latest",
    "codellama:latest",
]
OLLAMA_FALLBACK_MODEL = "ollama/qwen2.5-coder:3b"

# Environment keys
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"
OLLAMA_DEFAULT_URL = "http://localhost:11434"


# ══════════════════════════════════════════════════════════════
# MODEL GATEWAY
# ══════════════════════════════════════════════════════════════

class ModelGateway:
    """
    Intelligent model routing gateway for Omni-IDE.

    Cloud-Primary strategy — NO HuggingFace dependency:
      - ALL user tasks → Gemini 1.5 Pro (Cloud) — reliable tool-calling
      - Gemini down?   → Fallback to auto-detected Local Ollama model
      - Local 3B models are too small for smolagents protocol
    """

    def __init__(self):
        # ── FORCE RELOAD .env (keys may have been saved after server start) ──
        try:
            from config import ENV_PATH
            load_dotenv(str(ENV_PATH), override=True)
        except ImportError:
            load_dotenv(override=True)

        raw_key = os.getenv(GEMINI_API_KEY_ENV, "")

        # ── FALLBACK: Read .env directly if os.getenv missed it ──
        if not raw_key:
            try:
                from pathlib import Path
                from config import ENV_PATH as _env_path
                env_file = Path(_env_path)
                if env_file.exists():
                    for line in env_file.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY") and "=" in line:
                            raw_key = line.split("=", 1)[1].strip().strip("'").strip('"')
                            if raw_key:
                                os.environ[GEMINI_API_KEY_ENV] = raw_key
                                logger.info("🔑 GATEWAY: Loaded GEMINI_API_KEY directly from .env file")
                            break
            except Exception as e:
                logger.warning(f"⚠️ GATEWAY: Direct .env read failed: {e}")

        # Strip surrounding quotes that dotenv.set_key() may have added
        self.gemini_key = raw_key.strip("'").strip('"').strip() or None
        self.local_url = os.getenv(OLLAMA_BASE_URL_ENV, OLLAMA_DEFAULT_URL)
        self._routing_history: list[RoutingDecision] = []
        self._local_available: Optional[bool] = None
        self._last_health_check: float = 0.0
        self._health_check_ttl: float = 30.0

        # ── AUTO-DETECT LOCAL MODEL ───────────────────────────────
        self.local_model_id = self._detect_local_model()

        # ── Pre-build cloud model for runtime fallback ────────────
        self._cloud_model = None

        # Boot-time diagnostics
        print(f"🔑 GATEWAY DEBUG: Gemini Key Present? {bool(self.gemini_key)}")
        logger.info("🧠 GATEWAY: Hybrid Intelligence Engine v2.1 initialized.")
        logger.info(f"   ├─ Gemini API Key: {'✅ Loaded' if self.gemini_key else '❌ Missing (Local-only mode)'}")
        logger.info(f"   ├─ Ollama URL: {self.local_url}")
        logger.info(f"   ├─ Local Model: {self.local_model_id or '❌ None detected'}")
        logger.info(f"   └─ Context Threshold: {CONTEXT_THRESHOLD} tokens")

    def _detect_local_model(self) -> Optional[str]:
        """
        Query Ollama's /api/tags to find which models are actually installed.
        Returns the best available model in LiteLLM format.
        """
        try:
            import urllib.request
            import json
            req = urllib.request.Request(f"{self.local_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                installed = [m["name"] for m in data.get("models", [])]
                logger.info(f"   ├─ Ollama installed models: {installed}")

                for preferred in OLLAMA_PREFERRED_MODELS:
                    if preferred in installed:
                        model_id = f"ollama/{preferred}"
                        logger.info(f"   ├─ ✅ Auto-detected: {model_id}")
                        return model_id

                if installed:
                    local_models = [m for m in installed if 'cloud' not in m]
                    if local_models:
                        model_id = f"ollama/{local_models[0]}"
                        logger.warning(f"   ├─ ⚠️ No preferred model. Using: {model_id}")
                        return model_id

                logger.warning("   ├─ ❌ Ollama has no local models installed.")
                return None

        except Exception as e:
            logger.warning(f"   ├─ ❌ Ollama not reachable ({e}). Local unavailable.")
            return None

    def get_cloud_model(self):
        """Get or create a Gemini cloud model (for runtime fallback)."""
        if self._cloud_model is None and self.gemini_key:
            try:
                from smolagents import LiteLLMModel
                self._cloud_model = LiteLLMModel(
                    model_id=GEMINI_PRO_MODEL,
                    api_key=self.gemini_key,
                )
                logger.info(f"☁️  GATEWAY: Cloud fallback ready → {GEMINI_PRO_MODEL}")
            except Exception as e:
                logger.error(f"❌ GATEWAY: Cloud fallback init failed: {e}")
        return self._cloud_model

    # ----------------------------------------------------------
    # CORE ROUTING: get_brain()
    # ----------------------------------------------------------

    def get_brain(self, task_complexity: str = "AUTO", user_query: str = "", context_size: int = 0):
        """
        The Smart Router. Returns a ready-to-use LiteLLMModel.

        Args:
            task_complexity: "HIGH", "LOW", or "AUTO" (auto-detect from query).
            user_query: The user's request (used for auto-detection).
            context_size: Estimated token count of the current context.

        Returns:
            A smolagents.LiteLLMModel instance.
        """
        start = time.perf_counter()

        # Auto-detect complexity from query if set to AUTO
        if task_complexity == "AUTO" and user_query:
            task_complexity = self._classify_complexity(user_query, context_size)

        if task_complexity == "HIGH":
            decision = self._try_cloud(user_query, context_size)
        else:
            local_model = self.local_model_id or OLLAMA_FALLBACK_MODEL
            decision = RoutingDecision(
                tier=ModelTier.LOCAL,
                model_id=local_model,
                reason="Simple task — local model is optimal",
                context_size=context_size,
            )

        decision.latency_ms = (time.perf_counter() - start) * 1000
        self._routing_history.append(decision)
        self._log_decision(decision)

        return self._build_model(decision)

    def get_model_for_chat(self, user_query: str, file_content: str = ""):
        """
        Convenience method for the chat pipeline.
        Estimates context size from file content and routes accordingly.
        """
        context_tokens = len(file_content) // 4 if file_content else 0
        return self.get_brain(
            task_complexity="AUTO",
            user_query=user_query,
            context_size=context_tokens,
        )

    # ----------------------------------------------------------
    # COMPLEXITY CLASSIFIER
    # ----------------------------------------------------------

    def _classify_complexity(self, query: str, context_size: int) -> str:
        """Determine if a task is HIGH or LOW complexity."""
        query_lower = query.lower()

        # Condition A: Complexity trigger words
        for keyword in COMPLEXITY_TRIGGERS:
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, query_lower):
                logger.info(f"🔀 ROUTER: Complex task detected ('{keyword}'). → GEMINI PRO")
                return "HIGH"

        # Condition B: Large context window
        if context_size > CONTEXT_THRESHOLD:
            logger.info(f"🔀 ROUTER: Large context ({context_size} > {CONTEXT_THRESHOLD}). → GEMINI PRO")
            return "HIGH"

        # Condition C: Default — simple
        logger.info("🟢 ROUTER: Simple task. → LOCAL QWEN")
        return "LOW"

    # ----------------------------------------------------------
    # CLOUD ROUTER
    # ----------------------------------------------------------

    def _try_cloud(self, query: str, context_size: int) -> RoutingDecision:
        """Attempt to route to Gemini Pro. Falls back to local if unavailable."""
        if self.gemini_key:
            trigger = None
            query_lower = query.lower()
            for keyword in COMPLEXITY_TRIGGERS:
                if re.search(rf'\b{re.escape(keyword)}\b', query_lower):
                    trigger = keyword
                    break

            return RoutingDecision(
                tier=ModelTier.CLOUD,
                model_id=GEMINI_PRO_MODEL,
                reason=f"Complex task: '{trigger}'" if trigger else f"Large context ({context_size} tokens)",
                trigger_keyword=trigger,
                context_size=context_size,
            )
        else:
            local_model = self.local_model_id or OLLAMA_FALLBACK_MODEL
            logger.warning("⚠️ GATEWAY: No GEMINI_API_KEY. Falling back to Local.")
            return RoutingDecision(
                tier=ModelTier.LOCAL,
                model_id=local_model,
                reason="Gemini key missing — fallback to local",
                context_size=context_size,
                is_fallback=True,
            )

    # ----------------------------------------------------------
    # MODEL FACTORY
    # ----------------------------------------------------------

    def _build_model(self, decision: RoutingDecision):
        """Build the actual LiteLLMModel instance with automatic fallback."""
        from smolagents import LiteLLMModel

        # ── Cloud (Gemini) ────────────────────────────────────────
        if decision.tier == ModelTier.CLOUD:
            try:
                print("🔀 ROUTING: Attempting Gemini Pro (Cloud)...")
                model = LiteLLMModel(
                    model_id=GEMINI_PRO_MODEL,
                    api_key=self.gemini_key,
                )
                logger.info(f"☁️  GATEWAY: Gemini Pro ready → {GEMINI_PRO_MODEL}")
                return model
            except Exception as e:
                print(f"⚠️ CLOUD FAIL: {e}. Switching to Local...")
                logger.error(f"❌ Gemini init failed: {e}. Falling back to Local.")
                # Fall through to local

        # ── Local (auto-detected model via Ollama) ────────────────
        local_model = self.local_model_id
        if not local_model:
            if self.gemini_key and decision.tier != ModelTier.CLOUD:
                print("⚠️ No local model. Trying Gemini Cloud...")
                try:
                    model = LiteLLMModel(
                        model_id=GEMINI_PRO_MODEL,
                        api_key=self.gemini_key,
                    )
                    logger.info(f"☁️  GATEWAY: No local model → using Gemini Pro")
                    return model
                except Exception as e:
                    logger.error(f"❌ Cloud fallback also failed: {e}")

            raise RuntimeError(
                "🚨 GATEWAY CRITICAL: No models available.\n"
                "Ollama has no compatible models and Gemini is unavailable.\n"
                "Fix: Run 'ollama pull qwen2.5-coder:3b' or add GEMINI_API_KEY to .env."
            )

        print(f"🔀 ROUTING: Using Local {local_model}...")
        try:
            model = LiteLLMModel(
                model_id=local_model,
                api_base=self.local_url,
            )
            logger.info(f"⚡ GATEWAY: Local model ready → {local_model}")
            return model
        except Exception as e:
            logger.error(f"❌ Local init failed: {e}")
            if self.gemini_key:
                print("⚠️ Local failed. Falling back to Gemini Cloud...")
                try:
                    model = LiteLLMModel(
                        model_id=GEMINI_PRO_MODEL,
                        api_key=self.gemini_key,
                    )
                    logger.info(f"☁️  GATEWAY: Local failed → using Gemini Pro")
                    return model
                except Exception as cloud_err:
                    logger.error(f"❌ Cloud fallback also failed: {cloud_err}")

            raise RuntimeError(
                "🚨 GATEWAY CRITICAL: Both Local and Cloud models failed.\n"
                "Please ensure Ollama is running or add a valid GEMINI_API_KEY to .env."
            ) from e

    # ----------------------------------------------------------
    # HEALTH CHECK
    # ----------------------------------------------------------

    def _is_ollama_available(self) -> bool:
        """Check if Ollama is reachable (cached for 30s)."""
        now = time.time()
        if (now - self._last_health_check) < self._health_check_ttl and self._local_available is not None:
            return self._local_available

        try:
            import urllib.request
            req = urllib.request.Request(f"{self.local_url}/api/tags", method="GET")
            urllib.request.urlopen(req, timeout=2)
            self._local_available = True
        except Exception:
            self._local_available = False

        self._last_health_check = now
        return self._local_available

    # ----------------------------------------------------------
    # OBSERVABILITY
    # ----------------------------------------------------------

    def _log_decision(self, d: RoutingDecision):
        """Log a routing decision for observability."""
        icon = "☁️ " if d.tier == ModelTier.CLOUD else "⚡"
        print(
            f"{icon} GATEWAY: {d.tier.value.upper()} → {d.model_id} | "
            f"{d.reason} | ctx={d.context_size} | {d.latency_ms:.1f}ms"
        )

    def get_routing_stats(self) -> dict:
        """Return routing statistics for the /health endpoint."""
        total = len(self._routing_history)
        cloud = sum(1 for d in self._routing_history if d.tier == ModelTier.CLOUD)
        local = total - cloud
        avg_latency = (
            sum(d.latency_ms for d in self._routing_history) / total
            if total else 0
        )
        return {
            "total_routes": total,
            "cloud_routes": cloud,
            "local_routes": local,
            "avg_latency_ms": round(avg_latency, 2),
            "gemini_key_present": bool(self.gemini_key),
            "local_model": self.local_model_id,
            "ollama_available": self._local_available,
        }

    def select_model(self, *args, **kwargs):
        """Legacy compatibility shim."""
        return self.get_brain(*args, **kwargs)


# ── Singleton ─────────────────────────────────────────────────
def get_gateway() -> ModelGateway:
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = ModelGateway()
    return _gateway_instance

def reinitialize_gateway() -> ModelGateway:
    """Force-recreate the gateway (picks up new .env keys)."""
    global _gateway_instance
    _gateway_instance = None
    return get_gateway()

# ── Dynamic Singleton Proxy ──────────────────────────────────
class GatewayProxy:
    """Ensures 'from gateway import model_gateway' always hits the latest instance."""
    def __getattr__(self, name):
        return getattr(get_gateway(), name)

model_gateway = GatewayProxy()


# ══════════════════════════════════════════════════════════════
# SELF-TEST
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    gw = ModelGateway()

    test_cases = [
        ("refactor the auth module", "HIGH"),
        ("fix a typo", "LOW"),
        ("debug websocket", "HIGH"),
        ("add a comment", "LOW"),
        ("explain architecture", "HIGH"),
        ("hello", "LOW"),
        ("design database schema", "HIGH"),
        ("rename variable", "LOW"),
        ("optimize query performance", "HIGH"),
        ("update readme", "LOW"),
    ]

    print("\n🧪 Gateway Self-Test:")
    correct = 0
    for query, expected in test_cases:
        result = gw._classify_complexity(query, 100)
        ok = result == expected
        correct += ok
        print(f"  {'✅' if ok else '❌'} '{query}' → {result} (expected {expected})")

    print(f"\n  Score: {correct}/{len(test_cases)}")
    print(f"  Stats: {gw.get_routing_stats()}")
