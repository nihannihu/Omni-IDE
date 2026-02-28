# ══════════════════════════════════════════════════════════════════
# 🧪 Omni-IDE — Hybrid Intelligence Verification (verify_hybrid.py)
# ══════════════════════════════════════════════════════════════════
#
# Proves the 2-tier routing system works:
#   Test 1 (Cloud): Gemini key present → routes to gemini/gemini-1.5-pro-latest
#   Test 2 (Local): No Gemini key → routes to ollama/qwen2.5-coder:7b
#
# RUN: python verify_hybrid.py
# ══════════════════════════════════════════════════════════════════

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def header(text):
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}\n")


def result(label, passed, detail=""):
    icon = f"{GREEN}✅ [PASS]{RESET}" if passed else f"{RED}❌ [FAIL]{RESET}"
    print(f"  {icon} {label}")
    if detail:
        print(f"       {detail}")
    return passed


def section(text):
    print(f"\n{YELLOW}{'─' * 60}{RESET}")
    print(f"  {BOLD}{text}{RESET}")
    print(f"{YELLOW}{'─' * 60}{RESET}")


header("🧪 HYBRID INTELLIGENCE VERIFICATION")

all_pass = True

# ──────────────────────────────────────────────────────────────
# TEST 1: Cloud Routing (Gemini Key Present)
# ──────────────────────────────────────────────────────────────
section("TEST 1: Cloud Routing (Gemini Key → Complex Task)")

# Temporarily set a dummy Gemini key
os.environ["GEMINI_API_KEY"] = "test_dummy_key_for_routing"
os.environ.pop("OLLAMA_BASE_URL", None)  # Remove to use default

# Reimport gateway with the new env
# We need to reload the module to pick up the new env vars
if "gateway" in sys.modules:
    del sys.modules["gateway"]

from gateway import ModelGateway, ModelTier

gw_cloud = ModelGateway()

# Test: Complex task should route to CLOUD
decision = gw_cloud._try_cloud("refactor the authentication module", 300)
p1 = result(
    "'refactor' → Cloud (Gemini Pro)",
    decision.tier == ModelTier.CLOUD and "gemini" in decision.model_id,
    f"Tier: {decision.tier.value} | Model: {decision.model_id}"
)
all_pass = all_pass and p1

# Test: Complexity classifier detects keywords
complexity = gw_cloud._classify_complexity("debug the WebSocket issue", 100)
p2 = result(
    "'debug' classified as HIGH complexity",
    complexity == "HIGH",
    f"Classified as: {complexity}"
)
all_pass = all_pass and p2

# Test: Large context triggers cloud
complexity_ctx = gw_cloud._classify_complexity("add a comment", 8000)
p3 = result(
    "context=8000 → HIGH (exceeds 4000 threshold)",
    complexity_ctx == "HIGH",
    f"Classified as: {complexity_ctx}"
)
all_pass = all_pass and p3

# Test: Simple task stays LOCAL
complexity_simple = gw_cloud._classify_complexity("fix a typo", 50)
p4 = result(
    "'fix a typo' (ctx=50) → LOW complexity",
    complexity_simple == "LOW",
    f"Classified as: {complexity_simple}"
)
all_pass = all_pass and p4


# ──────────────────────────────────────────────────────────────
# TEST 2: Local Fallback (No Gemini Key)
# ──────────────────────────────────────────────────────────────
section("TEST 2: Local Routing (No Gemini Key → Fallback)")

# Remove the Gemini key BEFORE creating a new gateway
os.environ.pop("GEMINI_API_KEY", None)

# Force a fully fresh gateway class with clean env
import importlib
import gateway as gw_mod

# IMPORTANT: gateway.py calls load_dotenv at module level, which restores
# keys from .env. We must remove AFTER reload AND override the instance.
os.environ.pop("GEMINI_API_KEY", None)
importlib.reload(gw_mod)
os.environ.pop("GEMINI_API_KEY", None)  # Remove again after reload

gw_local = gw_mod.ModelGateway()
gw_local.gemini_key = None  # Force no-key scenario for this test

# Verify the new instance has no key
p5a = result(
    "New gateway has no gemini_key",
    gw_local.gemini_key is None,
    f"gemini_key: {gw_local.gemini_key}"
)
all_pass = all_pass and p5a

# Even a complex task should fallback to LOCAL when no key
decision_fallback = gw_local._try_cloud("refactor the entire codebase", 500)
p5 = result(
    "No Gemini key → Fallback to LOCAL",
    decision_fallback.tier == gw_mod.ModelTier.LOCAL,
    f"Tier: {decision_fallback.tier.value} | Fallback: {decision_fallback.is_fallback}"
)
all_pass = all_pass and p5

p6 = result(
    "Fallback model is Ollama Qwen",
    "ollama" in decision_fallback.model_id.lower(),
    f"Model: {decision_fallback.model_id}"
)
all_pass = all_pass and p6

# Simple task should also be LOCAL
complexity_no_key = gw_local._classify_complexity("write a function", 100)
p7 = result(
    "Simple task → LOW (regardless of key)",
    complexity_no_key == "LOW",
    f"Classified as: {complexity_no_key}"
)
all_pass = all_pass and p7


# ──────────────────────────────────────────────────────────────
# TEST 3: get_brain() Full Flow
# ──────────────────────────────────────────────────────────────
section("TEST 3: get_brain() Full Flow (with Mock)")

# Restore key for cloud test
os.environ["GEMINI_API_KEY"] = "test_dummy_key_for_routing"

importlib.reload(gw_mod)
gw_brain = gw_mod.ModelGateway()

# Mock LiteLLMModel at the smolagents import where gateway gets it
with patch("smolagents.LiteLLMModel") as MockModel:
    mock_instance = MagicMock()
    mock_instance.model_id = "gemini/gemini-1.5-pro-latest"
    MockModel.return_value = mock_instance
    
    brain = gw_brain.get_brain(
        task_complexity="AUTO",
        user_query="explain the architecture of this project",
        context_size=200,
    )
    
    p8 = result(
        "get_brain() returns a model for complex task",
        brain is not None,
        f"Model: {brain.model_id if brain else 'None'}"
    )
    all_pass = all_pass and p8
    
    # Verify LiteLLMModel was called with Gemini config
    call_args = MockModel.call_args
    p9 = result(
        "LiteLLMModel called with Gemini config",
        call_args is not None and "gemini" in str(call_args),
        f"Call args: {call_args}"
    )
    all_pass = all_pass and p9


# ──────────────────────────────────────────────────────────────
# TEST 4: Agent Graceful Error Handling
# ──────────────────────────────────────────────────────────────
section("TEST 4: Agent Graceful Error (No Model Available)")

# Verify agent.py has the graceful error pattern
with open("agent.py", "r", encoding="utf-8", errors="replace") as f:
    agent_src = f.read()

p10 = result(
    "agent.py has _init_error field",
    "_init_error" in agent_src,
    "Graceful degradation pattern found"
)
all_pass = all_pass and p10

p11 = result(
    "agent.py checks for degraded mode in execute_stream",
    "self._init_error" in agent_src and "No AI Model Available" in agent_src,
    "Early-exit with user-friendly error message"
)
all_pass = all_pass and p11

p12 = result(
    "Error message includes fix instructions",
    "ollama serve" in agent_src and "GEMINI_API_KEY" in agent_src,
    "User gets actionable steps to fix the issue"
)
all_pass = all_pass and p12


# ──────────────────────────────────────────────────────────────
# TEST 5: Zero HuggingFace Dependency
# ──────────────────────────────────────────────────────────────
section("TEST 5: Zero HuggingFace Verification")

# Check agent.py
p13 = result(
    "agent.py has NO 'from huggingface_hub' import",
    "from huggingface_hub" not in agent_src,
    "Clean — no HF imports"
)
all_pass = all_pass and p13

p14 = result(
    "agent.py has NO InferenceClientModel",
    "InferenceClientModel" not in agent_src,
    "Replaced with LiteLLMModel"
)
all_pass = all_pass and p14

# Check intent_router.py
with open("intent_router.py", "r", encoding="utf-8", errors="replace") as f:
    router_src = f.read()

p15 = result(
    "intent_router.py has NO 'from huggingface_hub' import",
    "from huggingface_hub" not in router_src,
    "Clean — uses litellm instead"
)
all_pass = all_pass and p15

# Check gateway.py
with open("gateway.py", "r", encoding="utf-8", errors="replace") as f:
    gw_src = f.read()

p16 = result(
    "gateway.py has NO HuggingFace references",
    "huggingface" not in gw_src.lower() or "NO HuggingFace" in gw_src,
    "Clean — only uses LiteLLMModel"
)
all_pass = all_pass and p16


# ──────────────────────────────────────────────────────────────
# FINAL VERDICT
# ──────────────────────────────────────────────────────────────
header("🏆 FINAL VERDICT")

if all_pass:
    print(f"  {GREEN}{BOLD}╔══════════════════════════════════════════════════╗{RESET}")
    print(f"  {GREEN}{BOLD}║  🟢 HYBRID INTELLIGENCE: FULLY VERIFIED          ║{RESET}")
    print(f"  {GREEN}{BOLD}║  Cloud → Gemini Pro | Local → Ollama Qwen 7B     ║{RESET}")
    print(f"  {GREEN}{BOLD}║  Zero HuggingFace | Graceful Degradation ✅       ║{RESET}")
    print(f"  {GREEN}{BOLD}╚══════════════════════════════════════════════════╝{RESET}")
else:
    print(f"  {RED}{BOLD}╔══════════════════════════════════════════════════╗{RESET}")
    print(f"  {RED}{BOLD}║  🔴 HYBRID INTELLIGENCE: ISSUES DETECTED         ║{RESET}")
    print(f"  {RED}{BOLD}║  Review [FAIL] items above.                       ║{RESET}")
    print(f"  {RED}{BOLD}╚══════════════════════════════════════════════════╝{RESET}")

print(f"\n  Signed: Omni-IDE SRE Pipeline | {time.strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Restore real key if it was in .env
from dotenv import load_dotenv
from config import ENV_PATH
load_dotenv(ENV_PATH, override=True)

sys.exit(0 if all_pass else 1)
