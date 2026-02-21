# Phase 6 Scope Document

## Vision
Phase 6 elevates Omni-IDE from a reactive tool to a proactive, intelligent co-founder. By introducing the **Intelligence Layer**, the system gains the ability to deeply comprehend user intent, decompose complex goals into multi-stage execution graphs, retain long-term project memory, and visually orchestrate tasks.

**Problems it solves:** 
- **Context Loss:** LLMs typically forget past architectural decisions; long-term memory solves this.
- **Micro-Management:** Users currently must prompt the AI step-by-step. A Task Graph Planner enables autonomous multi-step execution.
- **Execution Opacity:** Users lack visibility into what the AI is planning or doing in the background. 

**User Value:** 
Omni-IDE becomes a true autonomous digital worker. Users can hand off high-level architectural objectives ("Migrate our database to PostgreSQL") and trust the system to plan, execute, request review via the Diff Viewer, and finalize the integration seamlessly. 

---

## Goals & Non-Goals

### In Scope
- **Intent Routing (Foundation):** NLP-driven classification of user prompts to determine the required agent, tools, and execution path.
- **Task Graph + Planner:** A directed acyclic graph (DAG) engine to dynamically build, execute, and monitor multi-step AI workflows.
- **Project Memory:** Persistent, vectorizable storage (or structured JSON contextualization) of project architecture, design decisions, and past code reviews.
- **Execution Timeline UI:** A frontend dashboard component displaying the current DAG node, overall progress, and intelligent logs.
- **Background Insights:** Proactive, non-blocking background tasks (e.g., "Code Health Analysis") running while the user codes.

### Out of Scope (Non-Goals)
- Model fine-tuning or custom LLM training (we rely on prompt engineering and external APIs).
- Multi-repository or cross-system orchestration (scope is limited to the current open workspace folder).
- Fully undirected, infinite-loop agents (all execution paths must be finite and bounded by DAGs).
- Real-time pair-programming multiplayer (this is a single-user local IDE).

---

## Architecture Overview

The Phase 6 Intelligence Layer sits directly above the core execution layer and below the Frontend API tier:

1. **Frontend (Next.js/React):** 
   - Submits user prompts via WebSocket.
   - Renders the new *Execution Timeline UI* and *Background Insights* panels.
2. **Intent Router (Backend - `intent_router.py`):** 
   - Receives the raw query.
   - Uses zero-shot LLM classification or deterministic rules to route the request (e.g., `Query` -> `Code Generation` vs. `Refactoring` vs. `Analysis`).
3. **Planner Agent (Backend - `planner.py`):** 
   - If a complex task is detected, it builds a `Task Graph` (DAG) containing sequential and parallel steps.
4. **Project Memory Layer (Backend - `memory.py`):** 
   - Retrieves historical context and inserts it into the Planner's system prompt before graph execution.
5. **Execution Engine (Backend - `orchestrator.py`):** 
   - Walks the DAG, calling the Sub-Agents (`Coder`, `Reviewer`, etc.), generating patches via the Phase 5 Diff Staging Layer.

---

## Pillar Details

### 1. Intent Routing (Foundation)
- **Purpose:** To act as the brain's front door, intelligently dispatching work to the cheapest, fastest, or most capable tool.
- **Key Capabilities:** 
  - Classify prompts (Debug, Scaffold, Refactor, Question) and extract structured entities (File Paths).
  - **Confidence Threshold:** Routing must yield a confidence score. If ambiguous (below threshold), the system defaults to a "Clarification Needed" fallback before acting.
  - **Complexity Heuristics:** `IF task requires >1 tool OR >1 file → send to Planner | ELSE → direct execution`.
- **Dependencies:** Context Collector, LLM structured JSON output.
- **Success Criteria:** >95% accuracy in routing requests without needing explicit user slash-commands (e.g., `/debug`).

### 2. Task Graph + Planner
- **Purpose:** To execute complex objectives autonomously over long horizons.
- **Key Capabilities:** Dynamic DAG generation, state recovery on node failure, parallel execution of independent tasks (e.g., generating CSS and JS simultaneously), and human-in-the-loop pause nodes.
- **Dependencies:** Intent Router, Diff Staging Layer (for safe state transitions).
- **Success Criteria:** The system successfully completes a 5-step user objective with zero human intervention until the final approval stage.

### 3. Project Memory
- **Purpose:** To give Omni-IDE long-term retention of architecture rules, user preferences, and project history.
- **Key Capabilities:**
  - Summarizing completed Tasks into persistent 'Knowledge Items' (`.antigravity_memory.json`).
  - Injecting highly relevant KIs into the active context window.
  - **Write Policy:** Strict isolation—memory writes occur *only* after task completion (never during execution) to prevent context noise.
- **Dependencies:** File system storage, optionally lightweight vector embedding models if JSON scaling becomes an issue.
- **Success Criteria:** The AI references a custom architecture rule explicitly defined in a chat 3 days prior without the user reminding it.

### 4. Execution Timeline UI
- **Purpose:** To maintain user trust by making AI invisible thinking explicitly visible.
- **Key Capabilities:** A React component showing the generated Task Plan (DAG), indicating which step is "In Progress", "Completed", or "Blocked", alongside localized step-logs.
- **Dependencies:** A new WebSocket event payload format (`{'type': 'dag_update'}`).
- **Success Criteria:** Users can visually track a complex 3-minute generation job and understand exactly why it takes time.

### 5. Background Insights
- **Purpose:** To proactively assist the developer even when they aren't chatting.
- **Key Capabilities:** 
  - Spawning low-priority daemon threads when the IDE is idle to run security audits or suggest performance refactors.
  - **Resource Guardrails:** Engine enforces a strict CPU/IO budget cap and automatically pauses insight execution when the user is actively typing. 
- **Dependencies:** `main.py` asyncio loop, IDE file watchers.
- **Success Criteria:** Omni-IDE generates a purely proactive, non-blocking recommendation to fix a poorly written function while the user is typing elsewhere.

---

## Technical Principles

- **Modularity:** The Planner, Router, and Execution Engine must be strictly decoupled to allow swapping underlying LLMs.
- **Determinism over Magic:** The DAG execution must be deterministic. We prefer explicitly defined steps over unpredictable autonomous loops.
- **Observability:** Every node in the Task Graph must emit telemetry. If the AI hallucinates, the Execution Timeline must allow the developer to trace exactly which node failed.
- **Model-Agnostic Design:** The Intelligence Layer must rely on standard OpenAI/HuggingFace API JSON output schemas, avoiding proprietary vendor-lockin capabilities where possible.
- **Privacy & Security:** Project Memory remains entirely strictly local (`.antigravity/` dir). No workspace context is ever used to fine-tune global models. 

---

## Milestones

1. **Sprint 1: The Brain (Router & Memory)**
   - Deliverable: Develop the `Intent Router` and `Project Memory` JSON architecture.
   - Checkpoint: The system dynamically retrieves historical context without slash commands.
2. **Sprint 2: The Graph (Planner Engine)**
   - Deliverable: Build the DAG execution engine backing the multi-agent orchestrator. 
   - Checkpoint: A hardcoded dummy 3-step graph executes successfully.
3. **Sprint 3: The Dashboard (Timeline UI)**
   - Deliverable: React components linking the Task Graph state to the Frontend.
   - Checkpoint: The UI beautifully renders a progress checklist as the AI works.
4. **Sprint 4: The Proactive Co-Founder (Insights)**
   - Deliverable: Asynchronous background watchers that push insights to the user.
   - Checkpoint: System generates a proactive code smell warning without a prompt.
5. **Sprint 5: QA & Integration**
   - Deliverable: Full end-to-end integration testing and UX dogfooding.

---

## Risks

- **Technical Risk:** Context Window Overflow. As the Project Memory grows, injecting too many historical facts into the Intent Router/Planner could trigger API `max_token` errors or dilute prompt adherence. 
  - *Mitigation:* Implement strict token counting, FIFO memory discarding, or semantic search.
- **Product Risk:** UI Clutter. Adding DAG progress bars and Background Insights could overwhelm the clean chat interface. 
  - *Mitigation:* Keep the UI minimalistic and collapsed by default. 
- **Unknowns:** The LLM's capability to reliably generate valid JSON Directed Acyclic Graphs without hallucinating circular dependencies.
  - *Mitigation:* The Python execution backend must aggressively validate DAG structures and strip cyclic paths before execution starts.

---

## Success Metrics

| Metric | Target | Measurement Method |
| :--- | :--- | :--- |
| **Complex Task Success Rate** | > 85% | Percentage of multi-step (DAG) jobs that reach the final "Apply" state without exploding. |
| **Routing Accuracy** | > 95% | Percentage of tasks sent to the correct Sub-Agent / Tool path. |
| **Planner Latency** | < 4.0s | Time taken from User Prompt -> DAG creation and the start of Node 1 execution. |
| **Trust Score (UI)** | 9/10 | Qualitative Dogfooding measurement of exactly how comfortable the user feels reading the Execution Timeline. |
| **Proactive Acceptance Rate** | > 40% | The percentage of Background Insights (Unprompted suggestions) that the user actively applies to their code. |
