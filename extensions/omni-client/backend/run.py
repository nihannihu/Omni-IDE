import subprocess
import sys
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def ensure_dependencies():
    """Pre-install requirements.txt BEFORE importing main.py.
    This prevents the server from hanging on missing imports."""
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_file):
        logger.warning("requirements.txt not found, skipping dependency check.")
        return

    logger.info("--- Checking dependencies ---")
    start = time.time()

    try:
        # Quick check: try importing the heaviest packages
        # If they exist, skip pip install entirely (fast path)
        import smolagents  # noqa: F401
        import litellm     # noqa: F401
        import fastapi     # noqa: F401
        import uvicorn     # noqa: F401
        logger.info(f"--- Dependencies OK ({time.time()-start:.1f}s) ---")
        return
    except ImportError as e:
        logger.info(f"Missing dependency detected: {e}")
        logger.info("--- Installing dependencies (first run) ---")

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file,
             "--no-cache-dir", "--disable-pip-version-check", "--quiet"],
            capture_output=True, text=True, timeout=300,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        duration = time.time() - start
        if proc.returncode == 0:
            logger.info(f"--- Dependencies installed ({duration:.1f}s) ---")
        else:
            logger.error(f"pip install failed:\n{proc.stderr[-500:]}")
    except subprocess.TimeoutExpired:
        logger.error("pip install timed out after 300s")
    except Exception as e:
        logger.error(f"pip install error: {e}")

if __name__ == "__main__":
    try:
        # Step 1: Ensure all dependencies are installed BEFORE importing main
        ensure_dependencies()

        # Step 2: NOW import and start the server
        print("--- Starting Uvicorn (No Reload) ---")
        from dotenv import load_dotenv
        from config import ENV_PATH
        load_dotenv(ENV_PATH)

        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
