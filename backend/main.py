from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import logging
import os
import shutil
from session_manager import session_manager
import subprocess
import aiofiles
from pathlib import Path
from pydantic import BaseModel
import sys

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

from setup import router as setup_router
app.include_router(setup_router, prefix="/api/setup", tags=["setup"])

# Global State
WORKING_DIRECTORY = None  # No directory until user selects one

# Input/Output Models
class CodeRequest(BaseModel):
    code: str

class ChatRequest(BaseModel):
    text: str

class ChangeDirRequest(BaseModel):
    path: str

class FeedbackRequest(BaseModel):
    event_id: str
    module: str
    rating: str
    comment: str | None = None
    context: dict | None = None

class TemplateRunRequest(BaseModel):
    template_id: str
    params: dict

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

# Mount Next.js assets to the root expected paths
next_dir = os.path.join(static_path, "_next")
if os.path.exists(next_dir):
    app.mount("/_next", StaticFiles(directory=next_dir), name="next-assets")

# Mount legacy static path just in case, though unused by Next
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(static_path, 'index.html'))

@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse(os.path.join(static_path, 'favicon.ico'))

# --- Core API (Emergency Fix) ---

@app.post("/api/change_dir")
async def change_directory(request: ChangeDirRequest):
    """Update the working directory for the File Explorer."""
    global WORKING_DIRECTORY
    target_path = Path(request.path).resolve()
    
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid directory path.")
    
    WORKING_DIRECTORY = request.path
    session_manager.save_last_folder(WORKING_DIRECTORY)
    logger.info(f"Directory changed to: {WORKING_DIRECTORY}")
    return {"status": "success", "current_dir": WORKING_DIRECTORY}

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

@app.get("/api/browse")
async def browse_system(path: str = ""):
    """List subdirectories in a given path for the server-side folder picker."""
    import string
    
    # 1. Handle "Quick Access" / Root for fresh navigation
    if not path or path == "undefined" or path == "null":
        drives = []
        if os.name == 'nt':
            # Fast check for Windows drives
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append({"name": drive, "path": drive, "type": "drive"})
        
        home = str(Path.home())
        quick_access = [
            {"name": "🏠 Home", "path": home, "type": "quick"},
            {"name": "🖥️ Desktop", "path": str(Path.home() / "Desktop"), "type": "quick"},
            {"name": "📂 Documents", "path": str(Path.home() / "Documents"), "type": "quick"}
        ]
        
        # Filter quick access for existence
        quick_access = [q for q in quick_access if os.path.exists(q["path"])]
        
        return {
            "folders": drives + quick_access,
            "current_path": "",
            "is_root": True
        }

    try:
        target_path = Path(path).resolve()
        
        if not target_path.exists() or not target_path.is_dir():
             # If path doesn't exist, try parent
             target_path = Path.home()
        
        folders = []
        
        # Add ".." for navigating up, unless at drive root
        parent = target_path.parent
        if parent != target_path:
            folders.append({"name": ".. (Back)", "path": str(parent), "type": "nav"})

        # IGNORED_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.next'}
        
        with os.scandir(target_path) as entries:
            for entry in entries:
                try:
                    if entry.is_dir() and not entry.name.startswith('.'):
                        folders.append({
                            "name": entry.name,
                            "path": str(Path(entry.path)),
                            "type": "folder"
                        })
                except (PermissionError, OSError):
                    continue
        
        # Sort folders alphabetically
        folders.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
        
        return {
            "folders": folders,
            "current_path": str(target_path),
            "is_root": False
        }
    except Exception as e:
        logger.error(f"Browse Error for {path}: {e}")
        return {"folders": [], "error": str(e), "current_path": path}

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

# --- CODE RUNNER WITH AUTO-DEPENDENCY INSTALL ---

# Standard library modules that should NOT be pip-installed
STDLIB_MODULES = {
    "os", "sys", "math", "random", "time", "datetime", "json", "re", "io",
    "pathlib", "subprocess", "threading", "multiprocessing", "collections",
    "functools", "itertools", "operator", "string", "textwrap", "typing",
    "abc", "copy", "enum", "dataclasses", "contextlib", "argparse",
    "logging", "unittest", "hashlib", "base64", "struct", "socket",
    "http", "urllib", "email", "html", "xml", "csv", "sqlite3",
    "pickle", "shelve", "shutil", "glob", "tempfile", "stat",
    "platform", "ctypes", "array", "queue", "heapq", "bisect",
    "decimal", "fractions", "statistics", "secrets", "uuid",
    "pprint", "traceback", "warnings", "weakref", "gc", "inspect",
    "dis", "code", "codeop", "compile", "ast", "token", "tokenize",
    "pdb", "profile", "timeit", "trace", "symtable",
    "curses", "readline", "rlcompleter",
    "turtle", "tkinter", "Tkinter",
    "__future__", "builtins", "importlib", "pkgutil",
    "zipfile", "tarfile", "gzip", "bz2", "lzma", "zlib",
    "signal", "mmap", "select", "selectors", "asyncio",
    "concurrent", "sched",
    "wave", "audioop", "ossaudiodev",
    "webbrowser", "cgi", "cgitb",
    "wsgiref", "xmlrpc", "ftplib", "poplib", "imaplib", "smtplib",
    "telnetlib", "socketserver",
}

# Map special import names to pip package names
IMPORT_TO_PIP = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "bs4": "beautifulsoup4",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "gi": "PyGObject",
    "wx": "wxPython",
    "serial": "pyserial",
    "usb": "pyusb",
}

def extract_imports(code: str) -> set:
    """Extract top-level module names from Python source code."""
    import re as _re
    modules = set()
    for line in code.split("\n"):
        line = line.strip()
        # import X, Y, Z
        m = _re.match(r'^import\s+(.+)', line)
        if m:
            for mod in m.group(1).split(","):
                mod = mod.strip().split(".")[0].split(" as ")[0].strip()
                if mod:
                    modules.add(mod)
        # from X import ...
        m = _re.match(r'^from\s+(\S+)\s+import', line)
        if m:
            mod = m.group(1).split(".")[0].strip()
            if mod:
                modules.add(mod)
    return modules

def get_missing_packages(modules: set) -> list:
    """Return list of (import_name, pip_name) for modules that aren't installed."""
    import importlib
    missing = []
    for mod in modules:
        if mod in STDLIB_MODULES:
            continue
        try:
            importlib.import_module(mod)
        except ImportError:
            pip_name = IMPORT_TO_PIP.get(mod, mod)
            missing.append((mod, pip_name))
    return missing

# --- PHASE 5: STAGING LAYER APIs ---
@app.get("/api/staging/active-sessions")
async def get_active_sessions():
    global WORKING_DIRECTORY
    if not WORKING_DIRECTORY:
        return []
    from diff_staging_layer import DiffStagingLayer
    layer = DiffStagingLayer(WORKING_DIRECTORY)
    return layer.get_active_sessions()

@app.get("/api/patch/{session_id}")
async def fetch_patch(session_id: str):
    global WORKING_DIRECTORY
    if not WORKING_DIRECTORY:
        raise HTTPException(status_code=400, detail="No folder is open.")
    from diff_staging_layer import DiffStagingLayer
    layer = DiffStagingLayer(WORKING_DIRECTORY)
    result = layer.get_patch(session_id)
    if "error" in result:
        return {"error": result["error"]}
    return result

@app.post("/api/patch/{session_id}/apply")
async def apply_patch(session_id: str):
    global WORKING_DIRECTORY
    if not WORKING_DIRECTORY:
        raise HTTPException(status_code=400, detail="No folder is open.")
    from diff_staging_layer import DiffStagingLayer
    layer = DiffStagingLayer(WORKING_DIRECTORY)
    result = layer.apply_patch(session_id)
    if "error" in result:
        return {"error": result["error"]}
    return result

@app.post("/api/patch/{session_id}/discard")
async def discard_patch(session_id: str):
    global WORKING_DIRECTORY
    if not WORKING_DIRECTORY:
        raise HTTPException(status_code=400, detail="No folder is open.")
    from diff_staging_layer import DiffStagingLayer
    layer = DiffStagingLayer(WORKING_DIRECTORY)
    result = layer.discard_patch(session_id)
    if "error" in result:
        return {"error": result["error"]}
    return result

# --- Phase 6: Background Insights API ---

@app.get("/api/insights")
async def get_insights():
    """Run background analysis and return insight list."""
    global WORKING_DIRECTORY
    if not WORKING_DIRECTORY:
        return {"insights": [], "message": "No folder open."}
    from insights_engine import InsightsEngine
    engine = InsightsEngine(WORKING_DIRECTORY)
    insights = engine.run_scan()
    return {"insights": insights, "count": len(insights)}

@app.post("/api/insights/dismiss/{insight_id}")
async def dismiss_insight(insight_id: str):
    """Remove an insight from the cache."""
    global WORKING_DIRECTORY
    if not WORKING_DIRECTORY:
        raise HTTPException(status_code=400, detail="No folder open.")
    from insights_engine import InsightsEngine
    engine = InsightsEngine(WORKING_DIRECTORY)
    removed = engine.dismiss_insight(insight_id)
    return {"dismissed": removed}

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
        env['PYTHONIOENCODING'] = 'utf-8'
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
            
        base_cmd = python_cmd if isinstance(python_cmd, list) else [python_cmd]
        
        # --- PHASE 2: ZERO-CONFIG PROJECT ENVIRONMENT ---
        from environment_manager import EnvironmentManager
        import time
        venv_cmd, env_logs, env_duration = EnvironmentManager.setup_project_env(WORKING_DIRECTORY, base_cmd)
        
        exec_start_time = time.time()
        
        # --- PHASE 2: LIGHTWEIGHT SECURITY SANDBOX ---
        # Prevent accidental system file writes outside of the workspace directory.
        sandbox_header = f"""
import os, builtins
_orig_open = builtins.open
def _secure_open(path, *args, **kwargs):
    mode = args[0] if args else kwargs.get('mode', 'r')
    if any(m in mode for m in ['w', 'a', 'x', '+']):
        abs_path = os.path.abspath(path)
        # Windows robustness: normalize slashes and lower case for comparison
        clean_abs = os.path.normcase(os.path.normpath(abs_path))
        clean_wd = os.path.normcase(os.path.normpath(r'''{WORKING_DIRECTORY}'''))
        if not clean_abs.startswith(clean_wd):
            raise PermissionError(f"[SECURITY] Sandboxed execution prevents writing outside workspace directory.")
    return _orig_open(path, *args, **kwargs)
builtins.open = _secure_open
"""
        secure_code = sandbox_header + "\n" + code
        
        proc = subprocess.Popen(
            venv_cmd + ["-c", secure_code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            cwd=WORKING_DIRECTORY,
            env=env
        )
        
        try:
            # Wait up to 2.5 seconds for short scripts (e.g. calculation, print)
            stdout, stderr = proc.communicate(timeout=2.5)
            
            exec_duration = (time.time() - exec_start_time) * 1000
            runtime_logs = f"[RUNTIME] Execution: {exec_duration:.1f}ms\n"
            
            # --- AUTO-PIP DEPENDENCY MANAGER ---
            if proc.returncode != 0 and "ModuleNotFoundError: No module named" in stderr:
                from dependency_manager import DependencyManager
                out_app, err_app = DependencyManager.handle_auto_pip(stderr, venv_cmd, env, WORKING_DIRECTORY)
                stdout += out_app
                stderr += err_app
                
                # Rollback corrupt environment if installation critically failed
                if "❌ [AUTO-PIP] Failed to install" in out_app:
                    EnvironmentManager.rollback_env(WORKING_DIRECTORY)
            elif proc.returncode != 0:
                # Add diagnostics for other failures
                diag_code = "import sys,os; print(f'\\n--- DIAGNOSTICS ---\\nExecutable: {sys.executable}\\nSysPath: {sys.path}\\nEnviron: PYTHONPATH={os.environ.get(\\'PYTHONPATH\\', \\'None\\')}')"
                diag_proc = subprocess.run(base_cmd + ["-c", diag_code], capture_output=True, encoding='utf-8', errors='replace', env=env)
                stderr += diag_proc.stdout
                stderr += "\n💡 [AI CO-FOUNDER] Your code crashed. Type '/debug' in the chat to automatically analyze and fix this error.\n"
            # -----------------------------------
            
            if proc.returncode != 0 and hunter_log:
                stderr += "\n\n--- [IDE DIAGNOSTICS] PYTHON HUNTER TRACE ---\n" + "\n".join(hunter_log) + "\n"

            # Prepend performance telemetry to stdout for observability
            stdout = env_logs + runtime_logs + "\n" + stdout

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
                # Phase 6: Skip dag_event dicts in REST (they are for WebSocket only)
                if isinstance(token, dict):
                    continue
                full_response += str(token)
        except TypeError:
            async for token in agent.execute_stream(user_message):
                if isinstance(token, dict):
                    continue
                full_response += str(token)

        return {"response": full_response}
        
    except Exception as e:
        logger.error(f"Agent Error: {e}")
        # Return 500 so frontend sees the crash
        raise HTTPException(status_code=500, detail=f"Agent Crash: {str(e)}")

# --- Template API (Phase 7 Sprint 4) ---
from template_runner import template_runner
from fastapi import BackgroundTasks

@app.get("/api/templates")
async def list_templates():
    return template_runner.get_all()

@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    t = template_runner.get(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t

@app.post("/api/templates/run")
async def run_template(request: TemplateRunRequest, background_tasks: BackgroundTasks):
    t = template_runner.get(request.template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
        
    loop = asyncio.get_running_loop()
    
    def run_sync():
        def emit_cb(event):
            if isinstance(event, dict):
                # Wrap events if needed for WebSocket UI handling
                if event.get("type") == "dag_update":
                    wrapped = {"__dag_event__": True, **event}
                    asyncio.run_coroutine_threadsafe(manager.broadcast_json(wrapped), loop)
                elif event.get("__copilot_event__"):
                    payload = {
                        "type": "copilot_event",
                        "source": event.get("source", "router"),
                        "event_type": event.get("type", "unknown"),
                        "payload": event.get("payload", {})
                    }
                    asyncio.run_coroutine_threadsafe(manager.broadcast_json(payload), loop)

        try:
            template_runner.execute(request.template_id, request.params, emit_callback=emit_cb)
        except Exception as e:
            logger.error(f"Template run failed: {e}")

    background_tasks.add_task(run_sync)
    return {"status": "started", "template_id": request.template_id}

# --- Analytics API (Phase 7 Sprint 5) ---
from analytics_engine import analytics_engine

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    return analytics_engine.get_usage_summary()

@app.get("/api/analytics/workflows")
async def get_analytics_workflows():
    return analytics_engine.get_feature_adoption()

@app.get("/api/analytics/health")
async def get_analytics_health():
    # Health and failure rates
    return {
        "summary": analytics_engine.get_usage_summary(),
        "recent_failures": analytics_engine.get_failure_rates()
    }

@app.delete("/api/analytics/reset")
async def reset_analytics():
    analytics_engine.reset_analytics()
    return {"status": "success", "message": "Analytics data cleared."}

# --- Feedback API (Phase 7 Sprint 3) ---
from feedback_store import feedback_store

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Record user feedback for an AI action."""
    try:
        if request.module not in ["router", "planner", "insight", "copilot"]:
            raise ValueError("Invalid module name")
        if request.rating not in ["up", "down"]:
            raise ValueError("Invalid rating, must be 'up' or 'down'")
            
        record = feedback_store.add_feedback(
            event_id=request.event_id,
            module=request.module,
            rating=request.rating,
            comment=request.comment,
            context=request.context
        )
        return {"status": "success", "record_id": record["id"]}
    except Exception as e:
        logger.error(f"Feedback Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

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

    async def broadcast_json(self, message: dict):
        """Broadcasts a message to all connected clients."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                pass

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
                    # Phase 6/7: Detect dag_update and copilot_event payloads
                    if isinstance(token, dict):
                        if token.get("__dag_event__"):
                            payload = {k: v for k, v in token.items() if k != "__dag_event__"}
                            await manager.send_json(payload, websocket)
                        elif token.get("__copilot_event__"):
                            payload = {
                                "type": "copilot_event",
                                "source": token.get("source", "router"),
                                "event_type": token.get("type", "unknown"),
                                "payload": token.get("payload", {})
                            }
                            await manager.send_json(payload, websocket)
                        else:
                            await manager.send_json({"type": "agent_token", "text": str(token)}, websocket)
                            full_response += str(token)
                    else:
                        await manager.send_json({"type": "agent_token", "text": str(token)}, websocket)
                        full_response += str(token)
                
                await manager.send_json({"type": "agent_response_end"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        try:
            await manager.send_json({"type": "error", "message": str(e)}, websocket)
        except:
            pass
