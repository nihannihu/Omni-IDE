from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import psutil
import urllib.request
import json
import os
import subprocess
from dotenv import set_key
from config import ENV_PATH
import logging
import threading

logger = logging.getLogger(__name__)
router = APIRouter()

# Global State for background installation
INSTALL_STATE = {"status": "idle", "message": ""}

class KeyRequest(BaseModel):
    key: str

class InstallRequest(BaseModel):
    model_name: str

@router.get("/status")
def get_setup_status():
    status = {}

    # 1. RAM Check
    try:
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        status["ram_gb"] = ram_gb

        if ram_gb < 8:
            status["recommendation"] = "CLOUD_ONLY"
        elif ram_gb < 16:
            status["recommendation"] = "HYBRID_LIGHT"
        else:
            status["recommendation"] = "HYBRID_PRO"
    except Exception as e:
        logger.error(f"Error checking RAM: {e}")
        status["ram_gb"] = 0
        status["recommendation"] = "CLOUD_ONLY"

    # 2. Ollama Check
    status["ollama_running"] = False
    status["models"] = []
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
            status["ollama_running"] = True
            status["models"] = [m["name"] for m in data.get("models", [])]
    except Exception:
        pass # Ollama not reachable

    # 3. Key Check — strip surrounding quotes that dotenv.set_key() adds
    raw_key = os.getenv("GEMINI_API_KEY", "")
    clean_key = raw_key.strip("'").strip('"').strip()
    status["has_gemini_key"] = bool(clean_key)

    return status

def _save_key_to_env(clean_key: str):
    """Internal helper to save key to .env without FastAPI dependencies."""
    env_file = str(ENV_PATH)
    lines = []
    key_found = False
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    lines.append(f'GEMINI_API_KEY={clean_key}\n')
                    key_found = True
                else:
                    lines.append(line)
    if not key_found:
        lines.append(f'GEMINI_API_KEY={clean_key}\n')
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    # Update current process
    os.environ["GEMINI_API_KEY"] = clean_key

    # Update the gateway singleton if it's already instantiated
    try:
        from gateway import get_gateway
        get_gateway().gemini_key = clean_key
        logger.info("Updated ModelGateway with custom Gemini API Key.")
    except Exception as e:
        logger.warning(f"Failed to update gateway dynamically: {e}")

@router.post("/save_key")
def save_api_key_endpoint(request: KeyRequest):
    if not request.key:
        raise HTTPException(status_code=400, detail="Key is required")

    # Strip any accidental quotes from user input
    clean_key = request.key.strip("'").strip('"').strip()
    _save_key_to_env(clean_key)
    return {"status": "success"}

def pull_model_thread(model_name: str):
    global INSTALL_STATE
    INSTALL_STATE["status"] = "running"
    INSTALL_STATE["message"] = f"Initializing download for {model_name}..."
    logger.info(f"Starting background download for {model_name}...")

    try:
        kwargs = {}
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            **kwargs
        )

        for line in process.stdout:
            line = line.strip()
            if line:
                # E.g., parse json if ollama outputs json, otherwise just raw line
                # Ollama generally outputs small progress JSONs during pull
                try:
                    data = json.loads(line)
                    status_text = data.get("status", line)
                    if "completed" in data and "total" in data:
                        # Convert to MB
                        completed_mb = data["completed"] / (1024 * 1024)
                        total_mb = data["total"] / (1024 * 1024)
                        status_text += f" ({completed_mb:.1f}/{total_mb:.1f} MB)"
                    INSTALL_STATE["message"] = status_text
                except json.JSONDecodeError:
                    # Fallback to raw text
                    INSTALL_STATE["message"] = line

                logger.debug(f"Ollama Pull: {INSTALL_STATE['message']}")

        process.wait()

        if process.returncode == 0:
            INSTALL_STATE["status"] = "completed"
            INSTALL_STATE["message"] = f"Successfully installed {model_name}"
            logger.info(f"Ollama pull for {model_name} completed.")
        else:
            INSTALL_STATE["status"] = "error"
            INSTALL_STATE["message"] = f"Process failed with exit code {process.returncode}"
            logger.error(f"Ollama pull failed with code {process.returncode}")

    except Exception as e:
        logger.error(f"Error starting ollama pull: {e}")
        INSTALL_STATE["status"] = "error"
        INSTALL_STATE["message"] = str(e)

@router.post("/install_local")
def install_local_model(request: InstallRequest):
    global INSTALL_STATE
    if not request.model_name:
        raise HTTPException(status_code=400, detail="Model name is required")

    if INSTALL_STATE["status"] == "running":
        return {"status": "Already running", "message": INSTALL_STATE["message"]}

    thread = threading.Thread(target=pull_model_thread, args=(request.model_name,))
    thread.daemon = True
    thread.start()

    return {"status": "started", "message": f"Downloading {request.model_name} in background..."}

@router.get("/progress")
def get_setup_progress():
    global INSTALL_STATE
    return INSTALL_STATE
