import os
import json
import uuid
import shutil
import time

TEST_PROJECT = os.path.abspath(os.path.join(os.getcwd(), "qa_workspace_phase5"))

# Ensure clean state
if os.path.exists(TEST_PROJECT):
    shutil.rmtree(TEST_PROJECT)
os.makedirs(TEST_PROJECT)

# Create an initial file to diff against
app_path = os.path.join(TEST_PROJECT, "server.py")
with open(app_path, "w") as f:
    f.write("def start_server():\n    print('Server listening on port 8000')\n")

from diff_staging_layer import DiffStagingLayer

try:
    print("\n" + "="*60)
    print(" QA TEST SUITE: Phase 5 - Staging & Atomic Diff Proposal System")
    print("="*60)
    
    stager = DiffStagingLayer(TEST_PROJECT)

    # -------------------------------------------------------------
    # CASE 1: Patch Creation & Diff Generation
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 1: Patch Creation creates valid diff payload")
    new_content = "def start_server():\n    print('Server listening on port 8080')\n"
    proposal = stager.create_patch(app_path, new_content)
    
    assert proposal["status"] == "staged", "Failed to stage patch."
    assert "session_id" in proposal, "Session ID missing."
    assert "--- a/server.py" in proposal["diff"], "Unified diff generation failed."
    assert "port 8080" in proposal["diff"], "Diff content mismatch."
    
    session_id = proposal["session_id"]
    print(f"✅ PASS: Diff successfully computed. Session tracking actively as {session_id[:8]}...")

    # -------------------------------------------------------------
    # CASE 2: Get Patch Meta
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 2: Retrieval API")
    meta = stager.get_patch(session_id)
    assert meta["status"] == "PENDING", "Metadata status corrupted."
    assert meta["original_hash"] is not "", "Hash signature missing."
    print("✅ PASS: Retrieval API returned valid staging object.")

    # -------------------------------------------------------------
    # CASE 3: Apply Patch (Atomic Success)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 3: Atomic Application Workflow")
    apply_res = stager.apply_patch(session_id)
    assert apply_res.get("status") == "success", f"Apply failed: {apply_res}"
    
    with open(app_path, "r") as f:
         assert f.read() == new_content, "Disk write corrupted."
         
    meta_post = stager.get_patch(session_id)
    assert meta_post["status"] == "APPLIED", "Status state not transitioning cleanly."
    print("✅ PASS: Patch deployed atomically strictly updating status states.")

    # -------------------------------------------------------------
    # CASE 4: Patch Rejection (Discard)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 4: Discard / Rejection Workflow")
    destructive_content = ""
    proposal2 = stager.create_patch(app_path, destructive_content)
    session_id_2 = proposal2["session_id"]
    
    discard_res = stager.discard_patch(session_id_2)
    assert discard_res["status"] == "discarded", "Buffer rejection failed."
    
    # State check
    meta2 = stager.get_patch(session_id_2)
    assert meta2["status"] == "DISCARDED"
    assert meta2["proposed_content"] == "", "Memory buffer failed to drop payload payload on rejection."
    
    with open(app_path, "r") as f:
         assert f.read() == new_content, "Rejection somehow corrupted underlying active filesystem!"
    print("✅ PASS: Rejected patch wiped from cache and disk stayed pristine.")

    # -------------------------------------------------------------
    # CASE 5: Collision Detection (File Modified ExternALLY)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 5: Collision / Race Condition Detection")
    proposal3 = stager.create_patch(app_path, "print('AI Write')")
    session_id_3 = proposal3["session_id"]
    
    # User edits file behind the back of the Staging Layer
    time.sleep(0.1) # guarantee MTIME jump
    with open(app_path, "w") as f:
         f.write("print('User Write')")
         
    # Staging Layer attempts application
    conflict_res = stager.apply_patch(session_id_3)
    assert "error" in conflict_res, "Conflict Engine failed to intercept race condition."
    assert "Conflict Detected" in conflict_res["error"], "Wrong error type."
    
    with open(app_path, "r") as f:
         assert f.read() == "print('User Write')", "Atomic apply overwrote the user's manual change!"
    print("✅ PASS: External modification hash/MTIME collision detected correctly.")

    # -------------------------------------------------------------
    # CASE 6: Cleanup Process (Garbage Collection)
    # -------------------------------------------------------------
    print("\n▶️  TEST CASE 6: TTL Garbage Collection")
    # Both APPLIED, DISCARDED, and PENDING (if stale) should vanish.
    stager.cleanup_expired(ttl_seconds=-1) # Forcibly expire all PENDING
    assert len(stager.sessions) == 0, f"Cleanup logic failed. {len(stager.sessions)} lingering sessions."
    print("✅ PASS: Garbage collection sweep ran successfully.")

    print("\n" + "="*60)
    print(" 🏆 ALL PHASE 5 QA TEST CASES PASSED SUCCESSFULLY ")
    print("="*60)

finally:
    # Cleanup
    print("\n🛑 Shutting down QA script & cleaning workspaces...")
    if os.path.exists(TEST_PROJECT):
        shutil.rmtree(TEST_PROJECT, ignore_errors=True)
        
    # Nuke the staging file from Omni directory
    staging_file = os.path.abspath(os.path.join(os.getcwd(), "qa_workspace_phase5", ".antigravity_staging.json"))
    if os.path.exists(staging_file):
        os.remove(staging_file)
