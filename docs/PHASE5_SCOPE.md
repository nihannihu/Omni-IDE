# Phase 5 — Staging & Atomic Diff Proposal System

## Objective

The objective of Phase 5 is to introduce a secure, intermediate staging layer between the AI Co-Founder's generated code and the user's active file system. 

Currently, AI-driven file modifications execute instantaneously. This introduces a critical risk of data corruption, partial writes, or loss of user intent when an LLM hallucinates or produces syntax errors. By introducing an Atomic Diff Proposal System, the AI will instead generate a proposed patch that is held in an isolated staging environment. The user can review a unified diff representation of the changes and explicitly approve or reject them, dramatically improving system safety, reversibility, and developer trust.

## Core Capabilities

- **Isolated Staging Workspace**: An in-memory or temporary file buffer that holds proposed changes without touching the original source code.
- **Diff Generation Engine**: A backend mechanism to compute precise unified diffs between the active file state and the AI's proposed modifications.
- **Approval / Rejection Workflow**: Explicit lifecycle triggers allowing the orchestrator to either promote a patch to production or discard it entirely.
- **Snapshot & Rollback Safety**: Pre-computation safeguards ensuring that atomic filesystem swaps (temp-to-main file replacements) can recover cleanly if the OS blocks the write.
- **Session Lifecycle Management**: Automatic cleanup of orphaned staging sessions and stale patches.

## Non-Goals (Out of Scope)

- Advanced UI polish or interactive, line-by-line Git-style chunk staging.
- Multi-repo support or cross-workspace patching workflows.
- Cloud synchronization of patches or staging sessions.
- Collaborative multi-user editing features.
- AI integration directly into native IDE source editors (e.g., VSCode extensions).

## Technical Approach (High Level)

The staging system will intercept all `safe_write` operations invoked by the Multi-Agent Orchestrator. When an agent proposes a file modification, the text payload will be routed to a `DiffStagingLayer`.

This layer will read the pristine source file, compute a text-based unified diff using standard libraries, and park the new payload into a localized, short-lived session context or temporary file structure. The system will then emit a structured event representing the diff payload. 

Upon user approval, the promotion sequence will trigger an atomic write. The system will create a `.tmp` file beside the target, flush the staged buffer to disk, and utilize an OS-level atomic rename to overwrite the original source file, guaranteeing zero byte-level corruption even in the event of a power loss or thread panic.

## Risks & Mitigations

- **Risk: File Corruption during application.**
  *Mitigation*: Strict adherence to atomic writes (POSIX/Windows cross-compatible) using temporary contiguous file writing followed by locked renaming.
- **Risk: Performance Overhead on large files.**
  *Mitigation*: Limiting diff computation to files under 1MB. Files over this limit will trigger a "Full Replace Confirmation" instead of a computed chunk diff.
- **Risk: Race Conditions (User edits file while patch is pending).**
  *Mitigation*: Staging patches will store the last modified timestamp of the original file. If the original file changes before approval, the patch is automatically invalidated.
- **Risk: User Confusion over patch states.**
  *Mitigation*: Simple binary states for patches (`Pending`, `Applied`, `Discarded`) combined with clear text-based visual cues representing the diff.

## Definition of Done ✅

- [ ] System intercepts agent write commands and diverts them to a staging buffer instead of writing to disk.
- [ ] Backend reliably computes and returns a unified diff signature.
- [ ] System exposes an API or hook to explicitly `apply_patch` or `discard_patch`.
- [ ] Rejecting a patch leaves the original file system perfectly unchanged and clears the buffer.
- [ ] Approving a patch atomically updates the target file using safe temp-file replacement.
- [ ] Outdated or conflicting patches are caught and gracefully discarded (handling race conditions).
- [ ] Full suite of unit tests validates atomic failure recovery and rollback mechanisms.

## Success Metrics 📊

- **Diff Generation Latency**: < 50ms per file to avoid blocking the AI stream.
- **Approval Success Rate**: 100% atomic write success rate under normal OS conditions.
- **Zero File Corruption Incidents**: 0 reported instances of half-written files or lost data in the QA suite.
- **Dogfooding Satisfaction**: High subjective developer confidence when observing the AI generate complex, multi-line refactors safely.
