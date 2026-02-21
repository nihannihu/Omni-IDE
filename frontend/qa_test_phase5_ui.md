# Phase 5 UI — Staging & Diff Viewer QA Checklist

This document serves as the formal manual QA validation criteria for the **Atomic Diff Proposal System** frontend integration.

## 🧪 1. Functional Testing Scenarios

| ID | Module       | Scenario                                                                  | Expected Outcome                                                                 | Pass/Fail |
|----|--------------|---------------------------------------------------------------------------|----------------------------------------------------------------------------------|-----------|
| F1 | Diff Viewer  | Trigger an AI edit containing both additions and removals.                 | Panel extracts `Session ID` and displays unified diff. Additions are green (`+`), removals red (`-`). |         |
| F2 | API - Apply  | Click "Apply Patch" on a `PENDING` diff session.                         | Backend atomically updates file. Button swaps to `Processing...` Status transitions to `APPLIED`. |         |
| F3 | API - Discard| Click "Discard Patch" on a `PENDING` diff session.                         | Panel immediately disables actions. Status transitions to `DISCARDED`. Original file is 100% unaltered. |         |
| F4 | Fault Detect | Submit an invalid or missing `Session ID` to the DiffViewerPanel.         | UI correctly degrades into an isolated Error State boundary ("Failed to fetch patch data"). |         |
| F5 | Large Diffs  | Request AI to generate a block substitution over 100 lines.                | Diff UI does not freeze the main chat socket. Panel container scrolling operates smoothly without horizontal overflow. |         |
| F6 | Multi-patch  | AI generates 3 separate patches sequentially on different task commands.   | All 3 DiffViewer components render independently in the log stream with localized state retention. |         |

---

## ⚠️ 2. Edge Case Validation

| ID | Edge Case                 | Steps to Reproduce                                                | Expected Outcome                                                              | Pass/Fail |
|----|---------------------------|-------------------------------------------------------------------|-------------------------------------------------------------------------------|-----------|
| E1 | Double Application        | Click "Apply" on a patch that is already `APPLIED`.               | Buttons are disabled. `applyPatch` API rejects the request on the backend.    |         |
| E2 | Discard Applied Patch     | Click "Discard" on a patch that is already `APPLIED`.             | Buttons are disabled. Reversion blocked.                                        |         |
| E3 | Race Condition (Collision)| - Trigger patch creation.<br>- Manually edit file manually in IDE.<br>- Click "Apply". | Backend hash validation fails. Staging layer throws `Conflict Detected`. UI displays Global Error Banner. |         |
| E4 | Empty / Identical Diff    | AI generates a patch proposing identical source code.              | Backend skips staging. Chat UI does not spawn an orphaned UI ghost component. |         |
| E5 | Backend Disconnect        | - Patch generates.<br>- Manually kill `main.py`.<br>- Click "Apply". | Fetch throws network boundary exception. Global Error Banner gracefully captures frontend fault. |         |

---

## 🔭 3. UX Safety Checks

- [ ] **Data Readability**: Diff fonts are monospace, high-contrast, and clearly segmented.
- [ ] **Context Distinction**: Additions, deletions, and context lines (`@@`) correctly parse without regex bleed.
- [ ] **Accidental Interaction Guard**: "Apply" and "Discard" actions are physically separated preventing misclicks.
- [ ] **Clear State Ownership**: The Status Badge (Pending/Applied/Discarded) is the brightest anchor element on the component card.
- [ ] **No Auto-Applying**: The AI stream finishes rendering completely in a `PENDING` state before any disk write.

> **Lead QA Sign-off:** _________________  **(Date:** ____/____/2026)
