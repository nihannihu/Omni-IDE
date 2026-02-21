# Phase 6 Sprint 4 — Execution Timeline UI QA Validation
# ========================================================
# Authored: 2026-02-21

## Functional Tests

### F1 — DAG Render
- [ ] When a `dag_update` event arrives via WebSocket → `TimelinePanel` auto-appears
- [ ] Panel renders all nodes from the payload

### F2 — State Transition
- [ ] Node visually transitions: 🟡 PENDING → 🔵 RUNNING → 🟢 COMPLETED
- [ ] Color-coded badges update correctly

### F3 — Completion Reset
- [ ] When all nodes COMPLETE → Timeline fades to 50% opacity after 2s delay
- [ ] After fade, panel auto-hides on next empty state

### F4 — Multiple DAG Runs
- [ ] Second workflow replaces first graph cleanly
- [ ] No stale node data from previous run

### F5 — Collapse Toggle
- [ ] User clicks header → panel collapses, preserving state
- [ ] User clicks again → panel expands, showing same node states

---

## Edge Cases

### E1 — Partial Payload
- [ ] Missing `progress` field → UI still renders (estimated from node states)
- [ ] Missing `current_node` → No crash, no highlight

### E2 — Unknown Node Status
- [ ] Unrecognized status string → Displays ⚪ UNKNOWN badge

### E3 — Rapid Event Burst
- [ ] 10+ rapid events → No dropped frames or UI freezing
- [ ] React state batching handles correctly

### E4 — WebSocket Reconnect
- [ ] After disconnect + reconnect → Next `dag_update` resyncs Timeline

---

## Performance Checks

- [ ] Timeline render < 16ms per frame
- [ ] No memory leaks after 10 consecutive DAG runs
- [ ] No unnecessary re-renders observed in React DevTools

---

## Integration Tests

### I1 — Backend → WebSocket → Frontend Pipeline
- [ ] `planner.py execute_graph_stream()` yields valid JSON snapshots
- [ ] `main.py` WebSocket detects `__dag_event__` and strips marker before forwarding
- [ ] `Dashboard.tsx` dispatches `dag_update` events to `timelineStore`

### I2 — REST Endpoint Safety
- [ ] REST `/chat` endpoint skips dict tokens without crashing
- [ ] Normal text responses unaffected

### I3 — Chat Performance Isolation
- [ ] Timeline rendering does NOT block chat token streaming
- [ ] No visible latency increase in agent responses
