from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import logging
import os
import sys
import subprocess
import aiofiles
from pathlib import Path
from pydantic import BaseModel

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global State
WORKING_DIRECTORY = None  # No directory until user selects one

# Input/Output Models
class CodeRequest(BaseModel):
    code: str

class ChatRequest(BaseModel):
    text: str

class ChangeDirRequest(BaseModel):
    path: str

# CORS (Allow all for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files
# Detect if running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # If bundled, use the temporary _MEIPASS directory
    base_path = sys._MEIPASS
else:
    # If running as a script, use the local directory
    base_path = os.path.dirname(os.path.abspath(__file__))

static_path = os.path.join(base_path, "static")

# Mount the correct path
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(static_path, 'index.html'))

# --- Core API (Emergency Fix) ---

@app.post("/api/change_dir")
async def change_directory(request: ChangeDirRequest):
    """Update the working directory for the File Explorer."""
    global WORKING_DIRECTORY
    target_path = Path(request.path).resolve()
    
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid directory path.")
    
    WORKING_DIRECTORY = str(target_path)
    logger.info(f"Working Directory changed to: {WORKING_DIRECTORY}")
    return {"status": "success", "path": WORKING_DIRECTORY}

@app.post("/api/close_folder")
async def close_folder():
    """Reset WORKING_DIRECTORY to None (Close Folder)."""
    global WORKING_DIRECTORY
    WORKING_DIRECTORY = None
    # Also reset agent's directory
    from agent import WORKING_DIRECTORY as AGENT_WD
    import agent as agent_module
    agent_module.WORKING_DIRECTORY = None
    
    logger.info("Working Directory closed.")
    return {"status": "closed"}

@app.get("/api/files")
async def list_files(subpath: str = ""):
    """List files in the current WORKING_DIRECTORY, optionally in a subpath."""
    global WORKING_DIRECTORY
    files = []
    # Define safe extensions to show
    SAFE_EXTENSIONS = {'.py', '.txt', '.md', '.html', '.css', '.js', '.json', '.env',
                       '.yaml', '.yml', '.toml', '.cfg', '.ini', '.csv', '.xml',
                       '.tsx', '.jsx', '.ts', '.scss', '.less', '.svg', '.sh', '.bat',
                       '.dockerfile', '.gitignore', '.editorconfig', '.prettierrc'}
    IGNORED_DIRS = {'venv', 'venv_gpu', 'node_modules', '__pycache__', '.git', '.idea', '.vscode', 'dist', 'build', '.next'}
    
    try:
        if not WORKING_DIRECTORY:
            return {"files": [], "current_dir": None, "no_directory": True}
        
        # Resolve the target directory (base + optional subpath)
        base_path = Path(WORKING_DIRECTORY).resolve()
        if subpath:
            target_path = (base_path / subpath).resolve()
            # Security: prevent path traversal outside the working directory
            if not str(target_path).startswith(str(base_path)):
                raise HTTPException(status_code=403, detail="Access denied: Path traversal attempt.")
        else:
            target_path = base_path
        
        if not target_path.exists() or not target_path.is_dir():
            raise HTTPException(status_code=404, detail=f"Directory not found: {subpath}")
        
        # Scan the target directory
        with os.scandir(target_path) as entries:
            for entry in entries:
                if entry.name.startswith('.') and entry.name not in {'.env', '.gitignore', '.editorconfig', '.prettierrc'}: 
                    continue
                
                if entry.is_file() and (any(entry.name.endswith(ext) for ext in SAFE_EXTENSIONS) or '.' not in entry.name):
                    files.append({"name": entry.name, "type": "file"})
                elif entry.is_dir() and entry.name not in IGNORED_DIRS:
                    files.append({"name": entry.name, "type": "directory"})
        
        # Sort directories first, then files alphabetically
        files.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
        return {"files": files, "current_dir": WORKING_DIRECTORY, "subpath": subpath}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing files in {WORKING_DIRECTORY}/{subpath}: {e}")
        return {"files": [], "error": str(e)}

@app.get("/api/read")
async def read_file(filename: str):
    """Read content of a file from WORKING_DIRECTORY."""
    global WORKING_DIRECTORY
    try:
        if not WORKING_DIRECTORY:
            raise HTTPException(status_code=400, detail="No folder is open. Please open a folder first.")
        base_path = Path(WORKING_DIRECTORY).resolve()
        file_path = (base_path / filename).resolve()
        
        if not str(file_path).startswith(str(base_path)):
             raise HTTPException(status_code=403, detail="Access denied: Path traversal attempt.")
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {filename} in {WORKING_DIRECTORY}")
            
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
        return {"content": content, "path": str(file_path)}
        
    except HTTPException:
        raise  # Let HTTP errors pass through
    except Exception as e:
        logger.error(f"Read Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Lightweight health check for connection heartbeat."""
    return {"status": "ok"}

@app.get("/workspace/{filepath:path}")
async def serve_workspace_file(filepath: str):
    """Serve ANY file from WORKING_DIRECTORY. This is the key to making HTML previews work
    with relative CSS/JS/image references. When browser loads /workspace/page.html and
    that HTML has <link href='style.css'>, browser resolves to /workspace/style.css ✅"""
    global WORKING_DIRECTORY
    try:
        if not WORKING_DIRECTORY:
            raise HTTPException(status_code=400, detail="No folder is open.")
        base_path = Path(WORKING_DIRECTORY).resolve()
        file_path = (base_path / filepath).resolve()
        
        # Security: must stay within working directory
        if not str(file_path).startswith(str(base_path)):
            raise HTTPException(status_code=403, detail="Access denied.")
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
        
        # FileResponse auto-detects MIME type from extension
        return FileResponse(file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workspace file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save")
async def save_file(filename: str, request: CodeRequest):
    """Save editor content back to a file in WORKING_DIRECTORY."""
    global WORKING_DIRECTORY
    try:
        if not WORKING_DIRECTORY:
            raise HTTPException(status_code=400, detail="No folder is open. Please open a folder first.")
        base_path = Path(WORKING_DIRECTORY).resolve()
        file_path = (base_path / filename).resolve()
        
        if not str(file_path).startswith(str(base_path)):
            raise HTTPException(status_code=403, detail="Access denied.")
        
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(request.code)
        
        logger.info(f"Saved: {file_path}")
        return {"status": "saved", "path": str(file_path)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete")
async def delete_file(filename: str):
    """Delete a file from WORKING_DIRECTORY (reliable, UI-driven)."""
    global WORKING_DIRECTORY
    try:
        if not WORKING_DIRECTORY:
            raise HTTPException(status_code=400, detail="No folder is open. Please open a folder first.")
        base_path = Path(WORKING_DIRECTORY).resolve()
        file_path = (base_path / filename).resolve()
        
        if not str(file_path).startswith(str(base_path)):
            raise HTTPException(status_code=403, detail="Access denied.")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        import os, shutil
        if file_path.is_file():
            os.remove(file_path)
        elif file_path.is_dir():
            shutil.rmtree(file_path)
        
        logger.info(f"Deleted: {file_path}")
        return {"status": "deleted", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run")
async def run_code(request: CodeRequest):
    """Execute Python code and return output."""
    global WORKING_DIRECTORY
    code = request.code
    try:
        # Determine the correct Python executable
        # In a frozen PyInstaller build, sys.executable is OmniIDE.exe (no external libs)
        # So we fall back to the host system's 'python' command.
        
        env = os.environ.copy()
        python_cmd = sys.executable
        hunter_log = []
        
        if getattr(sys, 'frozen', False):
            # Strip PyInstaller sandbox variables so system Python can find global libraries (like Pygame)
            env.pop('PYTHONHOME', None)
            env.pop('PYTHONPATH', None)
            env.pop('LD_LIBRARY_PATH', None)
            # CRITICAL: PyInstaller prepends _MEIPASS to PATH, which corrupts pip build tools. We must strip it.
            meipass = getattr(sys, '_MEIPASS', '')
            if meipass:
                clean_path = [p for p in env.get('PATH', '').split(os.pathsep) if not p.startswith(meipass)]
                env['PATH'] = os.pathsep.join(clean_path)
            
            # The user might have experimental Python versions (like 3.14) on their PATH as the default 'python'
            # Experimental versions lack pre-compiled wheels (like pygame).
            # We must actively hunt for a stable Python version (3.12, 3.11, 3.10) first.
            import shutil
            stable_found = False
            
            # 1. Try explicit version commands (common on Linux/Mac, sometimes Windows)
            for version in ["python3.12", "python3.11", "python3.10", "python3.9", "python3.8", "python3"]:
                path = shutil.which(version, path=env.get('PATH'))
                hunter_log.append(f"shutil.which({version}) -> {path}")
                if path and "WindowsApps" not in path and "windowsapps" not in path.lower():
                    python_cmd = path
                    stable_found = True
                    break
                elif path:
                    hunter_log.append(f"Rejected alias -> {path}")
            
            # 2. On Windows, explicit versions are rarely on PATH. Use the 'py' launcher to specifically target stable versions.
            py_path = shutil.which("py", path=env.get('PATH')) or r"C:\Windows\py.exe"
            hunter_log.append(f"py_path resolved -> {py_path}")
            if not stable_found and os.path.exists(py_path):
                for version in ["-3.12", "-3.11", "-3.10", "-3.9", "-3.8", "-3"]:
                    try:
                        # Check if this version exists via the launcher, using the cleaned environment!
                        result = subprocess.run([py_path, version, "-c", "import sys"], capture_output=True, text=True, env=env)
                        hunter_log.append(f"Tested [py {version}] -> returncode: {result.returncode}")
                        if result.returncode == 0:
                            # Instead of a bare executable, we return a list for Popen
                            python_cmd = [py_path, version]
                            stable_found = True
                            break
                    except Exception as e:
                        hunter_log.append(f"Tested [py {version}] -> Exception: {e}")
                        pass
                        
            # 3. Locate the first valid python.exe on PATH that is NOT the Windows Store alias
            if not stable_found:
                env_path = env.get("PATH", "")
                for p in env_path.split(os.pathsep):
                    exe_path = os.path.join(p, "python.exe")
                    if os.path.exists(exe_path):
                        if "WindowsApps" not in exe_path and "windowsapps" not in exe_path.lower():
                            # Verify the python actually executes (the Store alias exits with code 9009 or fails)
                            try:
                                proc = subprocess.run([exe_path, "-c", "pass"], capture_output=True, env=env)
                                hunter_log.append(f"Tested PATH EXE {exe_path} -> returncode: {proc.returncode}")
                                if proc.returncode == 0:
                                    python_cmd = exe_path
                                    stable_found = True
                                    break
                            except Exception as e:
                                hunter_log.append(f"Tested PATH EXE {exe_path} -> Exception: {e}")
                                pass
                        else:
                            hunter_log.append(f"Skipped PATH EXE (WindowsApps) -> {exe_path}")

            # 4. Aggressive Absolute Path Scanning for Windows
            if not stable_found and os.name == 'nt':
                common_dirs = [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python"),
                    os.path.expandvars(r"%PROGRAMFILES%\Python"),
                    os.path.expandvars(r"%PROGRAMFILES(x86)%\Python"),
                    r"C:\Python312", r"C:\Python311", r"C:\Python310"
                ]
                for base_dir in common_dirs:
                    if os.path.exists(base_dir):
                        for sub in os.listdir(base_dir):
                            if sub.lower().startswith("python"):
                                exe_path = os.path.join(base_dir, sub, "python.exe")
                                if os.path.exists(exe_path):
                                    try:
                                        proc = subprocess.run([exe_path, "-c", "pass"], capture_output=True, env=env)
                                        hunter_log.append(f"Tested ABS EXE {exe_path} -> returncode: {proc.returncode}")
                                        if proc.returncode == 0:
                                            python_cmd = exe_path
                                            stable_found = True
                                            break
                                    except Exception as e:
                                        hunter_log.append(f"Tested ABS EXE {exe_path} -> Exception: {e}")
                                        pass
                    if stable_found:
                        break

            if not stable_found:
                # 5. Total fallback string (which we know might trigger the store alias, but better than crashing Python)
                hunter_log.append("WARNING: FAILED ALL HUNTER CHECKS. FALLING BACK TO 'python' STRING.")
                python_cmd = "python"
            
        # Handle python_cmd being a string or a list (from py launcher)
        base_cmd = python_cmd if isinstance(python_cmd, list) else [python_cmd]
        
        proc = subprocess.Popen(
            base_cmd + ["-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=WORKING_DIRECTORY,
            env=env
        )
        
        try:
            # Wait up to 2.5 seconds for short scripts (e.g. calculation, print)
            stdout, stderr = proc.communicate(timeout=2.5)
            
            # --- AUTO-PIP DEPENDENCY MANAGER ---
            if proc.returncode != 0 and "ModuleNotFoundError: No module named" in stderr:
                import re
                match = re.search(r"No module named '([^']+)'", stderr)
                if match:
                    missing_module = match.group(1)
                    stdout += f"\n[⚙️ AUTO-PIP] Missing module '{missing_module}' detected!\n"
                    
                    # Add diagnostic info about which python pip is actually using
                    ident_proc = subprocess.run(base_cmd + ["-c", "import sys; print(f'Target Python: {sys.executable} | Version: {sys.version}')"], capture_output=True, text=True, env=env)
                    stdout += f"[⚙️ AUTO-PIP] {ident_proc.stdout.strip()}\n"
                    stdout += f"[⚙️ AUTO-PIP] Installing '{missing_module}' (Pre-compiled Binary). Please wait...\n"
                    
                    try:
                        # 1. Upgrade core build tools
                        subprocess.run(base_cmd + ["-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], capture_output=True, env=env)
                        
                        # 2. Force install the binary wheel with VERBOSE output to see why it rejects wheels
                        pip_proc = subprocess.run(
                            base_cmd + ["-m", "pip", "install", missing_module, "--only-binary=:all:", "-v"],
                            capture_output=True,
                            text=True,
                            env=env
                        )
                        if pip_proc.returncode == 0:
                            stdout += f"\n✅ [AUTO-PIP] Successfully installed '{missing_module}'!\n"
                            stdout += f"👉 [AUTO-PIP] Please click 'Run Code' again to execute your script.\n"
                        else:
                            stdout += f"\n❌ [AUTO-PIP] Failed to install '{missing_module}'.\n"
                            stderr += f"\n--- PIP INSTALL ERROR ---\n{pip_proc.stderr}\n"
                            
                            # Give the user a hint if they are running an experimental Python version
                            if "3.13" in ident_proc.stdout or "3.14" in ident_proc.stdout:
                                stdout += f"\n💡 HINT: Your system Python is very new. Pre-compiled binaries for '{missing_module}' might not exist yet. Please install Python 3.12 for maximum compatibility.\n"

                    except Exception as e:
                        stdout += f"\n❌ [AUTO-PIP] Error running pip: {e}\n"
            elif proc.returncode != 0:
                # Add diagnostics for other failures
                diag_code = "import sys,os; print(f'\\n--- DIAGNOSTICS ---\\nExecutable: {sys.executable}\\nSysPath: {sys.path}\\nEnviron: PYTHONPATH={os.environ.get(\\'PYTHONPATH\\', \\'None\\')}')"
                diag_proc = subprocess.run(base_cmd + ["-c", diag_code], capture_output=True, text=True, env=env)
                stderr += diag_proc.stdout
            # -----------------------------------
            
            if proc.returncode != 0 and hunter_log:
                stderr += "\n\n--- [IDE DIAGNOSTICS] PYTHON HUNTER TRACE ---\n" + "\n".join(hunter_log) + "\n"

            return {
                "stdout": stdout,
                "stderr": stderr,
                "returncode": proc.returncode
            }
        except subprocess.TimeoutExpired:
            # For long-running apps (like Pygame or GUI), return early so UI doesn't hang.
            # We do NOT kill the process; it lives on in the background.
            return {
                "stdout": "🚀 Process launched and running in the background (GUI/Server)...",
                "stderr": "",
                "returncode": 0
            }
            
    except Exception as e:
        logger.error(f"Run code error: {e}")
        error_msg = str(e)
        if hunter_log:
            error_msg += "\n\n--- [IDE DIAGNOSTICS] PYTHON HUNTER TRACE ---\n" + "\n".join(hunter_log) + "\n"
        # If the code itself fails, return the error
        return {"stdout": "", "stderr": error_msg, "returncode": -1}

# --- AUTHENTICATION GATE ---
class APIKeyRequest(BaseModel):
    key: str

@app.get("/api/check-auth")
async def check_auth():
    """Check if user has a valid HuggingFace API key configured."""
    current_key = os.getenv("HUGGINGFACE_API_KEY")
    if current_key and current_key.startswith("hf_"):
        return {"authenticated": True}
    return {"authenticated": False}

@app.post("/api/save-key")
async def save_key(request: APIKeyRequest):
    """Save user's HuggingFace API key to runtime and .env file."""
    new_key = request.key.strip()

    # 1. Validate format
    if not new_key.startswith("hf_"):
        raise HTTPException(status_code=400, detail="Invalid key format. Must start with 'hf_'")

    # 2. Update runtime immediately
    os.environ["HUGGINGFACE_API_KEY"] = new_key

    # 3. Determine correct path for .env file
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    env_path = os.path.join(base_path, ".env")

    # 4. Write/update .env file (preserve other vars if they exist)
    env_lines = []
    if os.path.isfile(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if not line.strip().startswith("HUGGINGFACE_API_KEY"):
                    env_lines.append(line)
    env_lines.append(f"HUGGINGFACE_API_KEY={new_key}\n")

    with open(env_path, "w") as f:
        f.writelines(env_lines)

    # 5. Re-initialize the agent with the new key
    try:
        import importlib
        importlib.reload(agent_module)
        global agent
        agent = agent_module.OmniAgent()
        logger.info("Agent re-initialized with new API key.")
    except Exception as e:
        logger.warning(f"Agent reload after key save failed: {e}")

    logger.info(f"API key saved to {env_path}")
    return {"status": "saved"}

# --- Agent Logic (Robust REST Endpoint) ---
from agent import OmniAgent
import agent as agent_module  # Access module-level vars
agent = OmniAgent()

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Synced Chat Endpoint for Stability."""
    global WORKING_DIRECTORY
    user_message = request.text
    try:
        if not WORKING_DIRECTORY:
            return {"reply": "🛑 **Workspace Missing**\n\nI need a place to work! Please click **'Open Folder'** in the sidebar so I can start building your files.", "response": "🛑 **Workspace Missing**\n\nI need a place to work! Please click **'Open Folder'** in the sidebar so I can start building your files."}
        # FIX: Set agent's working directory WITHOUT os.chdir (which breaks static serving)
        agent_module.WORKING_DIRECTORY = WORKING_DIRECTORY
        logger.info(f"Agent will write files to: {WORKING_DIRECTORY}")
        
        full_response = ""
        try:
            response_generator = agent.execute_stream(user_message)
            for token in response_generator:
                full_response += token
        except TypeError:
            async for token in agent.execute_stream(user_message):
                full_response += token

        return {"response": full_response}
        
    except Exception as e:
        logger.error(f"Agent Error: {e}")
        # Return 500 so frontend sees the crash
        raise HTTPException(status_code=500, detail=f"Agent Crash: {str(e)}")

# --- WebSocket Chat Logic (Legacy/Streaming support) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/omni")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "text_input":
                text = data.get("text")
                await manager.send_json({"type": "agent_response_start"}, websocket)
                
                full_response = ""
                # Assuming sync generator for now based on previous code
                for token in agent.execute_stream(text):
                    await manager.send_json({"type": "agent_token", "text": token}, websocket)
                    full_response += token
                
                await manager.send_json({"type": "agent_response_end"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        try:
            await manager.send_json({"type": "error", "message": str(e)}, websocket)
        except:
            pass
