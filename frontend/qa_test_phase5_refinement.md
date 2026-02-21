# Phase 5 Refinement: QA Validation Plan

## 🧪 Functional Tests

| ID | Module      | Scenario | Expected Outcome | Pass/Fail |
|---|---|---|---|---|
| F1 | Session Restore | Refresh the browser while a patch is still `PENDING`. | The Dashboard calls `GET /api/staging/active-sessions` and auto-populates the "Action Required" Patch Queue. | |
| F2 | Diff Collapsing | View a massive patch (e.g., >100 lines). | Diff Panel renders exactly 50 lines. A prominent "Expand Diff" button appears below the code block. | |
| F3 | Chunk Rendering | Click "Expand Diff" on a >500 line patch. | Panel loads first 500 lines instantly without hanging the browser. "Load Next 500 Lines" button appears. | |
| F4 | TTL Display | Inspect a newly intercepted patch. | The header displays `🕒 Expires in 60 min` and decrements naturally. | |
| F5 | Queue Navigation| Click an inactive patch resting in the Patch Queue sidebar. | The Dashboard forces the Diff Viewer Panel to render seamlessly in the chat flow pointing to the orphaned Session ID. | |

---

## ⚠️ Edge Case Tests

| ID | Scenario | Expected Outcome | Pass/Fail |
|---|---|---|---|
| E1 | Automatic TTL Removal | Wait 61 minutes for a patch session to expire. | Backend sweeps it. The frontend queue gracefully drops the item on next refresh. |
| E2 | Non-Pending Exclusions| Manually `APPLY` a patch and wait/refresh. | The Patch Queue explicitly ignores applied and discarded patches. |
| E3 | No Content / Same Hash| Agent triggers safe_write but content is perfectly identical. | No ghost session UI floats in the sidebar. |
| E4 | Persistent Backend | Restart the `uvicorn` backend server halfway through a review. | Patches remain secured natively via `.antigravity_staging.json`. |

---

## 🚀 Performance Checks

- [ ] Restore sessions on `Dashboard` mount takes `< 200ms`
- [ ] Render / Expand a massive `500+` line diff takes `< 50ms` (no DOM freeze)
- [ ] No unhandled Promise rejections or memory leaks on multiple clicks.

> **Target readiness:** 100% test passing required.
