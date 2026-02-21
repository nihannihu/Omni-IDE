import os
import json
import shutil
import time

TEST_PROJECT = os.path.abspath(os.path.join(os.getcwd(), "qa_workspace_phase45"))

# Ensure clean state
if os.path.exists(TEST_PROJECT):
    shutil.rmtree(TEST_PROJECT)
os.makedirs(TEST_PROJECT)

# Create mock data
with open(os.path.join(TEST_PROJECT, ".gitignore"), "w") as f:
    f.write("ignored_folder/\n*.secret")

os.makedirs(os.path.join(TEST_PROJECT, "ignored_folder"))
with open(os.path.join(TEST_PROJECT, "ignored_folder", "bad_file.py"), "w") as f:
    f.write("print('Should not be read')")

with open(os.path.join(TEST_PROJECT, "app.py"), "w") as f:
    f.write("print('Original Content')")

from intelligence_core import IntelligenceCore
from diff_staging import DiffStagingLayer

try:
    print("\n" + "="*60)
    print(" QA TEST SUITE: Phase 4.5 Stabilization & Reliability")
    print("="*60)
    
    core = IntelligenceCore(TEST_PROJECT)
    stager = DiffStagingLayer(TEST_PROJECT)

    # -------------------------------------------------------------
    # CASE 1: Patch Proposal & Approval Flow
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 1: Staging & Atomic Approval")
    app_path = os.path.join(TEST_PROJECT, "app.py")
    proposal = stager.propose_patch(app_path, "print('New Content')")
    assert proposal["status"] == "staged", "Failed to stage patch."
    assert "--- a/app.py" in proposal["diff"], "Unified diff generation failed."
    
    # Apply
    apply_res = stager.apply_patch(app_path)
    assert apply_res["status"] == "success", "Atomic apply failed."
    with open(app_path, "r") as f:
        assert f.read() == "print('New Content')", "Atomic write corrupted data."
    print("✅ PASS: Patch successfully staged, diffed, and atomically applied.")

    # -------------------------------------------------------------
    # CASE 2: Patch Rejection
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 2: Patch Rejection")
    proposal = stager.propose_patch(app_path, "print('Destructive Content')")
    stager.discard_patch(app_path)
    with open(app_path, "r") as f:
        assert f.read() == "print('New Content')", "Discarded patch corrupted file!"
    print("✅ PASS: Rejected patch safely ignored.")

    # -------------------------------------------------------------
    # CASE 3: Unchanged Patch Detection
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 3: Unchanged Content Bypass")
    proposal = stager.propose_patch(app_path, "print('New Content')")
    assert proposal["status"] == "unchanged", "Failed to detect identical strings."
    print("✅ PASS: Unchanged patch caught safely.")

    # -------------------------------------------------------------
    # CASE 4: Git-Aware Context (Respect .gitignore)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 4: Git-Aware Context Collection")
    context = core.get_workspace_context()
    assert "app.py" in context, "Valid file missing from context."
    assert "bad_file.py" not in context, "Context collector ignored .gitignore rules!"
    print("✅ PASS: Context collector successfully filtered git-ignored folders.")

    # -------------------------------------------------------------
    # CASE 5: Memory Compaction System
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 5: Persistent Memory Compaction")
    # Force 15 notes into memory
    for i in range(15):
        core.add_memory_note(f"Note {i}")
        
    mem = core.load_memory()
    assert len(mem["notes"]) == 10, f"Memory compaction failed! Expected 10, got {len(mem['notes'])}"
    assert mem["notes"][0] == "Note 5", "Compaction deleted wrong notes."
    assert mem["notes"][9] == "Note 14", "Compaction deleted wrong notes."
    print("✅ PASS: Compaction algorithm correctly truncated older telemetry logs.")

    print("\n" + "="*60)
    print(" 🏆 ALL PHASE 4.5 QA TEST CASES PASSED SUCCESSFULLY ")
    print("="*60)

finally:
    # Cleanup
    print("\n🛑 Shutting down QA script & cleaning workspaces...")
    if os.path.exists(TEST_PROJECT):
        shutil.rmtree(TEST_PROJECT, ignore_errors=True)
