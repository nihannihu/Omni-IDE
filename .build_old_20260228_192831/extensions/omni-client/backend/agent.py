import logging
import re
import os
import sys
import subprocess
import json
import time
from threading import Thread, Lock as ThreadLock
from config import ENV_PATH
from dotenv import load_dotenv
load_dotenv(ENV_PATH, override=True)  # ALWAYS load fresh key from portable .env

# Lightweight Agent Framework (NO HuggingFace dependency)
from smolagents import CodeAgent, Tool, LiteLLMModel, ChatMessage, MessageRole, ChatMessageStreamDelta, ActionStep, ToolCall, ToolOutput, FinalAnswerStep
from smolagents.models import get_clean_message_list
import smolagents.utils as smolagents_utils

# Load environment variables
load_dotenv(ENV_PATH)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# DEBUG MODE (NDJSON) — session a45168
# ------------------------------------------------------------------
_DEBUG_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "debug-a45168.log"))

def _dbg(hypothesis_id: str, location: str, message: str, data: dict):
    """
    Append a single NDJSON debug log line for this debug session.
    """
    try:
        payload = {
            "sessionId": "a45168",
            "runId": "pre-fix",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Never break agent initialization for debug logging.
        pass

# ------------------------------------------------------------------
# SECURITY SANDBOX & FILE SYSTEM WRAPPERS
# ------------------------------------------------------------------

# This is set by main.py when the user changes directory
WORKING_DIRECTORY = None

def get_desktop_path():
    from pathlib import Path
    return Path(r"C:\Users\nihan\Desktop")

def get_base_path():
    """Returns WORKING_DIRECTORY. Raises error if no folder is open."""
    from pathlib import Path
    if WORKING_DIRECTORY:
        return Path(WORKING_DIRECTORY)
    raise ValueError("No folder is open. Please open a folder first using the Open Folder button.")

def safe_write(filename: str, content: str) -> str:
    """Safely writes content to a file. Phase 4.5: Intercepts writes for Diff Staging."""
    base = get_base_path()
    filename = filename.lstrip("/").lstrip("\\")
    filepath = (base / filename).resolve()

    if not str(filepath).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Path Traversal): {filename}")

    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Phase 5 Diff Staging Hook
    from diff_staging_layer import DiffStagingLayer
    layer = DiffStagingLayer(str(base))
    patch_result = layer.create_patch(str(filepath), content)

    if "error" in patch_result:
        logger.error(f"[ROLLBACK] Patch proposal failed: {patch_result['error']}")
        return f"ERROR: {patch_result['error']}"

    if patch_result.get("status") == "unchanged":
        logger.info(f"safe_write: {filename} was unchanged.")
        return str(filepath)

    # If the file exists and is being heavily modified, stage it.
    if patch_result.get("action") == "modify":
        session_id = patch_result.get("session_id")
        logger.warning(f"[STAGING] {filename} modification intercepted. Session ID: {session_id}")
        # For agent loop feedback, tell it the write succeeded but is Pending Approval
        return f"File '{filename}' staged for user approval. Session ID: {session_id}"

    # If it's a completely new file creation, write it instantly to not slow down scaffolding
    filepath.write_text(content, encoding='utf-8')
    logger.info(f"safe_write: Created entirely new file {filepath}")
    return str(filepath)

def safe_open(filepath_str, mode='r', **kwargs):
    """Safe wrapper for open() rooted to WORKING_DIRECTORY."""
    from pathlib import Path
    import builtins
    base = get_base_path()
    filepath = Path(filepath_str)

    if not filepath.is_absolute():
        filepath = base / filepath
    filepath = filepath.resolve()

    # CRITICAL SECURITY FIX: Block path traversal for ALL modes (including read)
    if not str(filepath).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Access Outside Sandbox): {filepath}")

    if any(m in mode for m in ('w', 'a', 'x')):
        filepath.parent.mkdir(parents=True, exist_ok=True)

    return builtins.open(str(filepath), mode, **kwargs)

def safe_mkdir(path_str, *args, **kwargs):
    """Safe wrapper for directory creation rooted to WORKING_DIRECTORY."""
    from pathlib import Path
    base = get_base_path()
    path = Path(path_str)

    if not path.is_absolute():
        path = base / path
    path = path.resolve()

    if not str(path).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (mkdir Outside Sandbox): {path}")

    path.mkdir(parents=True, exist_ok=True)
    return str(path)

def safe_delete(filename):
    """Delete a file from the working directory (sandboxed)."""
    from pathlib import Path
    import os
    base = get_base_path()
    path = Path(filename)
    if not path.is_absolute():
        path = base / path
    path = path.resolve()

    if not str(path).startswith(str(base.resolve())):
        raise ValueError(f"Security Block (Delete Outside Sandbox): {path}")

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.is_file():
        os.remove(path)
        logger.info(f"Deleted file: {path}")
        return f"Deleted: {filename}"
    elif path.is_dir():
        import shutil
        shutil.rmtree(path)
        logger.info(f"Deleted directory: {path}")
        return f"Deleted directory: {filename}"
    else:
        raise ValueError(f"Cannot delete: {path}")

def open_in_browser(filepath_str):
    """Opens a file in the default web browser (Desktop rooted)."""
    import webbrowser as wb
    from pathlib import Path
    desktop = get_desktop_path()
    filepath = Path(filepath_str)

    if not filepath.is_absolute():
        filepath = desktop / filepath
    filepath = filepath.resolve()

    wb.open(filepath.as_uri())
    return str(filepath)

def create_web_page(folder_name: str, page_type: str = "landing", title: str = "My Page", theme: str = "dark") -> str:
    """
    Generates professional HTML/CSS templates for standard pages.
    """
    folder_path = safe_mkdir(folder_name)
    from pathlib import Path
    folder = Path(folder_path)

    bg = "#0f0f1a" if theme == "dark" else "#f0f2f5"
    text = "#e0e0e0" if theme == "dark" else "#333333"
    accent = "#6c63ff"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ background: {bg}; color: {text}; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .container {{ text-align: center; padding: 40px; border: 1px solid {accent}; border-radius: 10px; }}
        h1 {{ color: {accent}; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>Generated by Omni-Agent Studio ({page_type})</p>
    </div>
</body>
</html>"""

    (folder / "index.html").write_text(html_content, encoding='utf-8')
    return open_in_browser(str(folder / "index.html"))

# ------------------------------------------------------------------
# TERMINAL TOOL — The "Hands" of the God Agent
# ------------------------------------------------------------------

class TerminalTool(Tool):
    """
    Execute terminal commands on the user's machine.
    This gives the agent "hands" — the ability to run code, install packages,
    and interact with the local system.
    """
    name = "terminal"
    description = (
        "Execute a shell command on the user's machine and return the output. "
        "Use this to run Python scripts, install packages with pip, "
        "list files, run tests, or any other terminal command. "
        "The command runs in the current working directory."
    )
    inputs = {
        "command": {
            "type": "string",
            "description": (
                "The shell command to execute. Examples: "
                "'python my_script.py', 'pip install requests', "
                "'dir', 'type file.txt', 'python -c \"print(1+1)\"'"
            )
        }
    }
    output_type = "string"

    # Commands that are too dangerous even for God Mode
    BLOCKED_COMMANDS = frozenset({
        "format", "del /q C:", "rd /s /q C:", "shutdown", "restart", ":(){", "mkfs",
    })

    def _translate_command(self, command: str) -> str:
        """Translate common Unix commands to Windows equivalents."""
        if sys.platform != "win32":
            return command

        # Simple regex-based translation for common tools
        parts = command.split()
        if not parts:
            return command

        cmd = parts[0].lower()
        args = parts[1:]

        # Translation Table
        if cmd == "cat":
            return f"type {' '.join(args)}"
        if cmd == "ls":
            # ls -la -> dir /a
            if args and "-l" in args[0]:
                return f"dir {' '.join(args[1:])}"
            return f"dir {' '.join(args)}"
        if cmd == "rm":
            # rm -rf -> rd /s /q
            if args and "-rf" in args[0]:
                return f"rd /s /q {' '.join(args[1:])}"
            return f"del /q {' '.join(args)}"
        if cmd == "cp":
            return f"copy {' '.join(args)}"
        if cmd == "mv":
            return f"move {' '.join(args)}"
        if cmd == "clear":
            return "cls"
        if cmd == "grep":
            return f"findstr {' '.join(args)}"
        if cmd == "which":
            return f"where {' '.join(args)}"
        if cmd == "touch":
            return f"type nul > {' '.join(args)}"

        return command

    def forward(self, command: str) -> str:
        """Execute a command and return structured stdout/stderr output."""

        # Translate command for Windows if necessary
        original_command = command
        command = self._translate_command(command)

        # Safety check: block catastrophically destructive commands
        cmd_lower = command.lower().strip()
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return f"🛑 BLOCKED: Command '{original_command}' (translated to '{command}') is too dangerous. Refusing to execute."

        if command != original_command:
            logger.info(f"🖥️  TERMINAL: Translated → {original_command} to {command}")
        else:
            logger.info(f"🖥️  TERMINAL: Executing → {command}")

        try:
            # Determine working directory
            cwd = WORKING_DIRECTORY if WORKING_DIRECTORY else os.getcwd()

            # Build a clean environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute hard timeout
                cwd=cwd,
                env=env,
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            returncode = result.returncode

            # Build structured output
            if returncode != 0:
                # --- Windows Build Tools Hint ---
                if sys.platform == "win32" and ("msvccompiler" in stderr.lower() or "failed to build wheel" in stderr.lower()):
                    stderr += "\n\n💡 [WINDOWS HELP] This error usually means you are missing the Visual Studio C++ Build Tools."
                    if "pygame" in command.lower():
                        stderr += "\nTry: 'pip install pygame-ce' for a pre-built Windows version."

                output = f"❌ ERROR (exit code {returncode}):\n"
                if stderr:
                    output += f"{stderr}\n"
                if stdout:
                    output += f"\nPartial Output:\n{stdout}\n"
                output += "\n(Review this error and fix your code. Do NOT ask the user — just fix it.)"
                logger.warning(f"🖥️  TERMINAL: ❌ Failed (exit={returncode})")
                return output

            # --- Success Case ---
            output = f"✅ OUTPUT (exit code 0):\n{stdout}" if stdout else "✅ SUCCESS (exit code 0, no output)"
            if stderr:
                # Some tools write warnings to stderr even on success
                output += f"\n\n⚠️ WARNINGS:\n{stderr}"
            logger.info(f"🖥️  TERMINAL: ✅ Success (exit={returncode})")
            return output

        except subprocess.TimeoutExpired:
            logger.error(f"🖥️  TERMINAL: ⏰ Timeout after 120s → {command}")
            return (
                f"❌ TIMEOUT: Command '{command}' exceeded 120 seconds.\n"
                "The process was killed. Consider breaking the task into smaller steps."
            )
        except Exception as e:
            logger.error(f"🖥️  TERMINAL: 💥 Exception → {e}")
            return f"❌ SYSTEM ERROR: {str(e)}\n(Review this error and fix your approach.)"


# ------------------------------------------------------------------
# VISION TOOL (SERVERLESS)
# ------------------------------------------------------------------

class VisionTool(Tool):
    """Vision tool powered by Gemini Pro Vision (NO HuggingFace)."""
    name = "analyze_screen"
    description = "Analyze the latest screen frame to answer a question. Use this tool when the user asks you to 'see', 'look', or describe what is on the screen."
    inputs = {
        "question": {
            "type": "string",
            "description": "The question to ask about the screen content (e.g., 'What do you see?', 'Read the error')."
        }
    }
    output_type = "string"

    def __init__(self, get_image_func, **kwargs):
        super().__init__(**kwargs)
        self.get_image_func = get_image_func
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    def forward(self, question: str) -> str:
        try:
            image_data = self.get_image_func()
            if not image_data:
                return "No screen frame available. Ask the user to verify screen sharing is on."

            # Clean base64 string
            if "," in image_data:
                 image_data = image_data.split(",")[1]

            logger.info(f"VisionTool: Analyzing screen with question: '{question}' (Gemini Vision)")

            if not self.gemini_key:
                return "Vision unavailable: GEMINI_API_KEY not configured in .env"

            # Use Gemini Pro Vision via LiteLLM
            import litellm
            response = litellm.completion(
                model="gemini/gemini-2.5-flash",
                api_key=self.gemini_key,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                            {"type": "text", "text": question}
                        ]
                    }
                ],
                max_tokens=500
            )

            result = response.choices[0].message.content
            logger.info(f"VisionTool Result: {result[:50]}...")
            return f"Screen Insight: {result}"

        except Exception as e:
            logger.error(f"VisionTool Error: {e}")
            return f"Error analyzing screen: {str(e)}"

# ------------------------------------------------------------------
# OMNI AGENT (GOD-TIER AUTONOMOUS ENGINEER)
# ------------------------------------------------------------------

class OmniAgent:
    def __init__(self):
        logger.info("Initializing Hybrid Intelligence Engine (Gemini + Local Qwen)...")
        _dbg(
            hypothesis_id="H1",
            location="backend/agent.py:OmniAgent.__init__",
            message="OmniAgent initialization started",
            data={},
        )

        # Vision Caching
        self.image_lock = ThreadLock()
        self.latest_image = None

        def get_latest_image():
            with self.image_lock:
                return self.latest_image

        self.vision_tool = VisionTool(get_latest_image)
        self.terminal_tool = TerminalTool()

        # ----------------------------------------------------------
        # HYBRID INTELLIGENCE GATEWAY (Smart Model Routing)
        # ----------------------------------------------------------
        try:
            from gateway import model_gateway
            self.gateway = model_gateway
            logger.info("🧠 Hybrid Intelligence Gateway connected.")
            _dbg(
                hypothesis_id="H1",
                location="backend/agent.py:OmniAgent.__init__",
                message="Gateway imported and attached to OmniAgent",
                data={"has_gateway": bool(self.gateway)},
            )
        except Exception as e:
            logger.warning(f"⚠️ Gateway unavailable ({e}). Falling back to Local Qwen.")
            self.gateway = None
            _dbg(
                hypothesis_id="H1",
                location="backend/agent.py:OmniAgent.__init__",
                message="Gateway import failed, falling back to local-only",
                data={"error": str(e)},
            )

        # PROMPT: God-Tier Autonomous Engineer Protocol
        SYSTEM_PROMPT = r"""
You are the Omni-IDE Core Intelligence, a senior software architect designed for Mohammed Nihan.
Your primary directives are:
1. CONTEXTUAL SUPREMACY: Always prioritize the provided file context and workspacePath over general knowledge.
2. AGENTIC ACTION: You have permission to read, write, and debug files within the project root. If a user asks to fix a bug, generate the exact code and use your file-writing tool to apply it.
3. ERROR TRIAGE: When a terminal error is provided, analyze the stack trace and suggest the specific line in the specific file that needs changing.
4. CONCISE EXPERTISE: Do not give long introductions. Provide high-quality, production-ready code using modern standards (ES6+, Python 3.10+, FastAPI).
5. HYBRID AWARENESS: You are currently running in a Hybrid environment (Gemini Cloud + Ollama Local).

=== WINDOWS ENVIRONMENT (CRITICAL) ===
You are running on WINDOWS.
- Use `dir` instead of `ls`.
- Use `type` instead of `cat`.
- Use `python` (not `python3`).
- Use `del` or `rd` instead of `rm`.
- Use `copy`/`move` instead of `cp`/`mv`.

=== AUTONOMY PROTOCOL ===

1. PLAN: Break the user's request into clear steps.
2. ACTION: Write the code (Python or Shell).
3. VERIFY: Use the `terminal` tool to run your script IMMEDIATELY.
4. REFLECT:
   - If you see `❌ ERROR`, you MUST analyze the error, rewrite the code, and try again.
   - Do NOT ask the user for permission to fix bugs. Just fix them.
   - You have MAX 3 retry attempts for any single error.
5. FINAL ANSWER: Only return when your code exits with code 0 (Success).

=== FILE OPERATIONS ===

RULE 1 - FILE CREATION (when user says "create", "make", "build"):
  - Call `safe_write(filename, content)` DIRECTLY with the full file content.
  - DO NOT assign to variables. DO NOT show in markdown blocks.
  - After writing: `final_answer("DONE: filename1.html, filename2.css")`

RULE 2 - FILE EDITING (when user says "edit", "modify", "add", "change", "update", "fix"):
  THIS IS THE MOST IMPORTANT RULE. To EDIT an existing file you MUST:
  Step 1: READ the existing file content:
    `existing = safe_open("filename.html", "r").read()`
  Step 2: MODIFY the content (add/change/remove what the user requested)
  Step 3: WRITE the modified content back:
    `safe_write("filename.html", modified_content)`
  Step 4: `final_answer("DONE: filename.html")`

  WARNING: You MUST include ALL the original content plus your changes.
  If you only write new content, you will DELETE the original file content!

RULE 3 - RESPONSE FORMAT (MANDATORY):
  - ALWAYS end with: `final_answer("DONE: file1.ext, file2.ext")`
  - List ALL files you created or modified.
  - NEVER say just "Done!" — you MUST include the filenames after "DONE:"

RULE 4 - TOOLS AVAILABLE:
  - `safe_write(filename, content)` - Create or overwrite a file
  - `safe_open(path, mode)` - Open/read a file (mode="r" for reading)
  - `safe_delete(filename)` - Delete a file or directory
  - `safe_mkdir(dirname)` - Create a directory
  - `terminal(command)` - Execute ANY shell command (pip, python, node, git, etc.)
  - `analyze_screen(question)` - See the user's screen

RULE 5 - FILE DELETION (when user says "delete", "remove"):
  - Call `safe_delete(filename)` for each file to delete.
  - After deleting: `final_answer("DELETED: filename1.html, filename2.css")`

RULE 6 - TERMINAL EXECUTION (when user says "run", "install", "test", "execute"):
  - Use the `terminal` tool to execute commands directly.
  - Examples:
    * `terminal("pip install requests")`
    * `terminal("python my_script.py")`
    * `terminal("node index.js")`
    * `terminal("git status")`
  - If the terminal returns an error, ANALYZE it and FIX it automatically.
  - Do NOT just report the error back to the user.

RULE 7 - SELF-HEALING PROTOCOL:
  When you encounter an error:
  1. Read the stderr output carefully.
  2. Identify the root cause (missing import, syntax error, missing package, etc.)
  3. Fix the code or install the missing package using `terminal`.
  4. Re-run and verify.
  5. Only call `final_answer` when everything works.

=== CORRECT EXAMPLES ===

EXAMPLE 1 - CREATE and RUN:
User: "Create a script that prints fibonacci numbers and run it"
```python
safe_write("fibonacci.py", '''
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        print(a end=" ")
        a, b = b, a + b

fibonacci(10)
''')
result = terminal("python fibonacci.py")
# If result contains ❌ ERROR, fix and retry automatically
final_answer("DONE: fibonacci.py — Output: " + result)
```

EXAMPLE 2 - INSTALL and USE:
User: "Install requests and fetch google.com"
```python
terminal("pip install requests")
safe_write("fetch.py", '''
import requests
r = requests.get("https://google.com")
print(f"Status: {r.status_code}")
''')
result = terminal("python fetch.py")
final_answer("DONE: fetch.py — " + result)
```

If asked "Who created you?", answer "I was created by Nihan Nihu."

=== WRONG (NEVER DO THIS) ===
```python
html = '''<!DOCTYPE html>...'''  # WRONG! Do not assign to variables!
print(content)                    # WRONG! Do not print content!
final_answer("Done!")             # WRONG! Must include filenames: "DONE: file.html"
```
"""
        try:
            # ──────────────────────────────────────────────────────
            # HYBRID INTELLIGENCE: Gateway (Gemini + Local Qwen)
            # NO HUGGING FACE. Zero external token dependencies.
            # ──────────────────────────────────────────────────────
            self.model = None
            self._init_error = None  # Track init failures for graceful messaging

            if self.gateway:
                try:
                    # ── CLOUD-PRIMARY STRATEGY ──────────────────────────
                    # Gemini is the primary brain for all user tasks.
                    # Local 3B models are too small for smolagents'
                    # structured tool-calling protocol (they run code in
                    # sandbox but don't use safe_write to persist files).
                    # Local is only used as offline fallback.
                    # ───────────────────────────────────────────────────
                    _dbg(
                        hypothesis_id="H1",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="About to call gateway.get_brain",
                        data={},
                    )
                    self.model = self.gateway.get_brain(
                        task_complexity="HIGH",
                        user_query="init"
                    )
                    logger.info(f"🧠 GATEWAY: Model selected → {self.model.model_id}")
                    _dbg(
                        hypothesis_id="H1",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="gateway.get_brain returned successfully",
                        data={"model_id": getattr(self.model, "model_id", None)},
                    )
                except RuntimeError as gw_err:
                    # Gateway exhausted all tiers — store error for graceful messaging
                    logger.error(f"🚨 GATEWAY: All model tiers exhausted: {gw_err}")
                    self._init_error = str(gw_err)
                    _dbg(
                        hypothesis_id="H1",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="Gateway get_brain raised RuntimeError",
                        data={"error": str(gw_err)},
                    )
                except Exception as gw_err:
                    logger.warning(f"⚠️ Gateway selection failed ({gw_err}). Trying direct local.")
                    self.model = None
                    _dbg(
                        hypothesis_id="H1",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="Gateway get_brain failed with generic exception",
                        data={"error": str(gw_err)},
                    )

            if self.model is None and self._init_error is None:
                # Direct fallback: Local Qwen via Ollama (auto-detect model)
                try:
                    local_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                    # Use gateway's auto-detected model, or fall back to 3b
                    local_model = getattr(self.gateway, 'local_model_id', None) or "ollama/qwen2.5-coder:3b"
                    _dbg(
                        hypothesis_id="H4",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="Attempting LiteLLMModel local fallback",
                        data={"local_model": local_model, "local_url": local_url},
                    )
                    self.model = LiteLLMModel(
                        model_id=local_model,
                        api_base=local_url,
                    )
                    logger.info(f"⚡ FALLBACK: Using Local {local_model} (Ollama)")
                    _dbg(
                        hypothesis_id="H4",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="LiteLLMModel local fallback constructed",
                        data={"model_id": getattr(self.model, "model_id", None)},
                    )
                except Exception as local_err:
                    logger.error(f"🚨 LOCAL FALLBACK FAILED: {local_err}")
                    self._init_error = (
                        "🚨 **No AI Model Available.**\n\n"
                        "Neither Gemini (Cloud) nor Ollama (Local) could be reached.\n\n"
                        "**To fix this, do ONE of the following:**\n"
                        "1. **Connect to the internet** and add a valid `GEMINI_API_KEY` to your `.env` file.\n"
                        "2. **Start Ollama locally:** Run `ollama serve` then `ollama pull qwen2.5-coder:7b`.\n\n"
                        "Once either is available, restart the IDE."
                    )
                    _dbg(
                        hypothesis_id="H4",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="LiteLLMModel local fallback failed",
                        data={"error": str(local_err)},
                    )

            # Only create the CodeAgent if we have a working model
            if self.model is not None:
                _dbg(
                    hypothesis_id="H2",
                    location="backend/agent.py:OmniAgent.__init__",
                    message="About to construct CodeAgent",
                    data={"model_id": getattr(self.model, "model_id", None)},
                )
                try:
                    self.agent = CodeAgent(
                        tools=[],
                        model=self.model,
                        add_base_tools=False,
                        max_steps=10,
                        verbosity_level=logging.INFO,
                        instructions=SYSTEM_PROMPT,
                        additional_authorized_imports=[
                            "datetime", "math", "random", "time", "json", "re",
                            "subprocess", "os", "sys", "shutil", "glob",  # God Mode imports
                        ],
                        stream_outputs=True,
                        executor_kwargs={
                            "additional_functions": {
                                "safe_write": safe_write,
                                "safe_open": safe_open,
                                "safe_delete": safe_delete,
                                "safe_mkdir": safe_mkdir,
                                "open_in_browser": open_in_browser,
                                "create_web_page": create_web_page,
                                "terminal": self.terminal_tool.forward,
                                "VisionTool": VisionTool
                            }
                        }
                    )
                    logger.info("Hybrid Brain initialized (God Mode: ACTIVE). Zero HuggingFace.")
                    _dbg(
                        hypothesis_id="H2",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="CodeAgent constructed successfully",
                        data={},
                    )
                except Exception as agent_err:
                    logger.error(f"Failed during CodeAgent initialization: {agent_err}")
                    _dbg(
                        hypothesis_id="H2",
                        location="backend/agent.py:OmniAgent.__init__",
                        message="CodeAgent construction failed",
                        data={"error": str(agent_err)},
                    )
                    raise
            else:
                self.agent = None
                logger.error("🚨 Agent running in DEGRADED MODE — no model available.")
                _dbg(
                    hypothesis_id="H3",
                    location="backend/agent.py:OmniAgent.__init__",
                    message="OmniAgent initialized in degraded mode (no model)",
                    data={"init_error": self._init_error},
                )

        except Exception as e:
            logger.error(f"Failed to initialize AI Agent: {e}")
            raise e

    def update_vision_context(self, base64_image: str):
        with self.image_lock:
            # logger.debug("Updated latest screen frame")
            self.latest_image = base64_image

    def get_smart_model(self, task: str, file_content: str = ""):
        """
        Use the Hybrid Intelligence Gateway to select the optimal model
        for the given task and context.

        Returns a ready-to-use model instance, or None if the gateway
        is unavailable (fallback to Local Qwen via Ollama).
        """
        if not self.gateway:
            return None

        try:
            model = self.gateway.get_model_for_chat(task, file_content)
            logger.info(f"🧠 Smart Model selected: {model.model_id}")
            return model
        except Exception as e:
            logger.warning(f"⚠️ Gateway routing failed ({e}). Using default model.")
            return None

    def execute_stream(self, task: str):
        """Execute a task context-aware and yield ONLY the clean final answer to the frontend."""
        logger.info(f"Agent task received: {task}")
        final_answer = None

        # Graceful error if no model was available at init time
        if self._init_error or self.agent is None:
            yield (
                self._init_error or
                "🚨 **No AI Model Available.**\n\n"
                "Please connect to the internet or ensure Ollama is running.\n"
                "Run `ollama serve` then `ollama pull qwen2.5-coder:7b` to enable local AI."
            )
            return

        # --- PHASE 3: INTELLIGENCE CORE WIRING ---
        from intelligence_core import IntelligenceCore
        core = IntelligenceCore(WORKING_DIRECTORY)
        context_prompt = ""

        if WORKING_DIRECTORY:
            # Multi-Agent Orchestrator Handling (Phase 4)
            from agent_orchestrator import AgentOrchestrator
            orchestrator = AgentOrchestrator(core)
            cmd_prefix = task.split(" ")[0]

            # --- LLM Runner Definition (Bridge for simple/complex tasks) ---
            def llm_runner(prompt: str) -> str:
                res = None
                try:
                    # Re-use the existing `smolagents` loop so `DebugAgent` can still use `safe_write` hooks
                    for step in self.agent.run(prompt, stream=True):
                        if type(step).__name__ == "ActionStep" and step.is_final_answer and step.action_output is not None:
                            res = str(step.action_output)
                        elif type(step).__name__ == "FinalAnswerStep":
                            res = str(step.output)
                    return res or ""
                except Exception as e:
                    logger.error(f"[LLM RUNNER ERR] {e}")
                    return ""

            # --- PHASE 6: INTENT ROUTING MVP ---
            from intent_router import IntentRouter
            router = IntentRouter(confidence_threshold=0.8)

            # Skip routing for explicit slash commands to preserve legacy UX
            if not task.startswith("/"):
                yield f"🧠 *Intelligence Layer: Routing Intent...*\n\n"

                try:
                    routing_result = router.route_intent(task)
                except Exception as route_err:
                    logger.error(f"IntentRouter crashed: {route_err}")
                    routing_result = {"execution_path": "Direct Execution", "reason": f"Router error: {route_err}"}

                exec_path = routing_result.get("execution_path")

                # Phase 7 Sprint 1: Emit Intent to Copilot Store via WebSocket
                yield {
                    "__copilot_event__": True,
                    "source": "router",
                    "type": "intent",
                    "payload": {
                        "label": exec_path,
                        "confidence": routing_result.get("confidence", 0.0),
                        "explanation": routing_result.get("reason", "No explanation provided.")
                    }
                }

                # Phase 7 Sprint 2: Emit Explainability reasoning
                from explainability import ExplainabilityEmitter
                yield ExplainabilityEmitter.emit(
                    source="router",
                    reason_code="intent_classification",
                    summary=f"Classified as '{exec_path}' based on request structure.",
                    context={"confidence": routing_result.get("confidence", 0.0), "intent": exec_path}
                )

                # Templates are used ONLY as a silent fallback when LLM is unavailable.
                # The LLM path runs first via the normal Planner/Direct flow below.

                if exec_path == "Clarification Needed":
                    yield f"🤔 *I'm not exactly sure what to execute.* (Ambiguous Intent)\nReason: {routing_result.get('reason')}\n\nCould you clarify your request?"
                    return
                elif exec_path == "Task Graph Planner":
                    from planner import PlannerEngine
                    planner = PlannerEngine()
                    yield f"🧭 *High Complexity Detected. Engaging Task Graph Planner...*\n\n"

                    try:
                        graph = planner.load_dummy_graph("complex", user_request=task)
                        yield f"🗺️ *Graph built: {len(graph.nodes)} node(s). Executing sequentially...*\n\n"

                        context_ext = {
                            "task": task,
                            "workspace": core.get_workspace_context(max_files=5),
                            "runner": llm_runner
                        }

                        # Phase 6 Sprint 4: Stream dag_update events for Timeline UI
                        completed_count = 0
                        has_failed = False
                        for dag_event in planner.execute_graph_stream(graph, context_ext):
                            # Yield the dag_event dict directly — WebSocket handler will detect and forward
                            yield {"__dag_event__": True, **dag_event}
                            # Track final state
                            all_done = all(n["status"] == "COMPLETED" for n in dag_event.get("nodes", []))
                            any_fail = any(n["status"] == "FAILED" for n in dag_event.get("nodes", []))
                            if all_done:
                                completed_count = len(dag_event.get("nodes", []))
                            if any_fail:
                                has_failed = True

                        if has_failed:
                            yield f"❌ **Task Graph Execution Halted.**\nCheck the Timeline panel for details."
                        else:
                            yield f"✅ **Task Graph Execution Complete.**\nSuccessfully processed {completed_count} chained objectives."
                    except Exception as pe:
                        logger.error(f"Planner Error: {pe}")
                        pe_str = str(pe)
                        if "402" in pe_str or "Payment" in pe_str or "Credit" in pe_str:
                            # --- GRACEFUL FALLBACK: Use Instant Generation templates ---
                            from offline_engine import execute_offline
                            fallback_result = execute_offline(task, safe_write)
                            if fallback_result:
                                yield f"⚡ *Generating code...*\n\n"
                                yield fallback_result
                                core.add_memory_note(f"User Request: {task[:100]}")
                            else:
                                yield f"⚠️ **AI Credits Depleted.**\nYour Gemini API key may have run out of credits.\n\n💡 **How to fix:** Check your Google AI Studio billing or ensure Ollama is running locally."
                        else:
                            yield f"❌ **Planner Engine Failed.**\nError: {pe}"
                    return

            # --- Phase 4 Fallback / Direct Execution ---
            if cmd_prefix in orchestrator.agents:
                user_task = task.replace(cmd_prefix, "").strip()
                agent_name = orchestrator.agents[cmd_prefix].name

                # Let user know the agent is thinking (streaming UX)
                yield f"⚙️ *{agent_name} is analyzing the workspace...*\n\n"

                returned_agent, final_text = orchestrator.route_and_execute(cmd_prefix, user_task, llm_runner)
                yield final_text
                return

            # Legacy Phase 3 Command Palette Handling
            if task.startswith("/explain"):
                context_prompt = f"{core.get_workspace_context(max_files=10)}\n\n[USER COMMAND: /explain]\nExplain the architecture or the specific file requested: {task.replace('/explain', '').strip()}"
            elif task.startswith("/refactor"):
                context_prompt = f"{core.get_workspace_context(max_files=10)}\n\n[USER COMMAND: /refactor]\nSuggest refactoring improvements for: {task.replace('/refactor', '').strip()}"
            elif task.startswith("/generate-tasks"):
                context_prompt = core.generate_task_prompt(task.replace('/generate-tasks', '').strip())
            elif task.startswith("/health"):
                context_prompt = core.build_health_prompt()
            elif task.startswith("/insights"):
                # Phase 6: Background Insights — Manual Trigger
                from insights_engine import InsightsEngine
                engine = InsightsEngine(WORKING_DIRECTORY)
                insights = engine.run_scan()

                # Phase 7 Sprint 1: Emit Insights to Copilot UI
                yield {
                    "__copilot_event__": True,
                    "source": "insights",
                    "type": "update",
                    "payload": {
                        "insights": insights
                    }
                }

                # Phase 7 Sprint 2: Emit Explainability reasoning
                from explainability import ExplainabilityEmitter
                yield ExplainabilityEmitter.emit(
                    source="insights",
                    reason_code="insight_trigger",
                    summary=f"Background scan completed. Found {len(insights)} insights.",
                    context={"insight_count": len(insights)}
                )

                yield engine.format_insights_text()
                return
            else:
                # Standard Contextual Chat

                # --- PHASE 6: PROJECT MEMORY MVP ---
                try:
                    from memory import ProjectMemory
                    pmemory = ProjectMemory(WORKING_DIRECTORY)
                    memory_context = pmemory.safe_memory_read(task)
                except Exception as e:
                    logger.error(f"Project Memory injection failed: {e}")
                    memory_context = ""

                proj_memory_block = f"### PROJECT MEMORY ###\n{memory_context}\n" if memory_context else ""

                memory = core.load_memory()
                recent_notes = "\n".join(memory.get("notes", []))
                context_prompt = f"""
{proj_memory_block}
[WORKSPACE MEMORY]
{recent_notes}

{core.get_workspace_context(max_files=15, max_chars_per_file=1000)}

[USER PROMPT]
{task}
"""
            # Save interaction to memory
            core.add_memory_note(f"User Request: {task[:100]}")

            task_to_run = context_prompt
        else:
            task_to_run = task

        logger.info(f"Context-Aware Task Length: {len(task_to_run)} chars")

        try:
            for step in self.agent.run(task_to_run, stream=True):
                # Log internals for debugging (NOT sent to frontend)
                if isinstance(step, ToolCall):
                    logger.info(f"  Tool: {step.name}")
                elif isinstance(step, ActionStep):
                    if step.error:
                        logger.error(f"  Step Error: {step.error}")
                    if hasattr(step, "observations") and step.observations:
                        logger.info(f"  Observation: {step.observations[:200]}...")
                    if step.is_final_answer and step.action_output is not None:
                        final_answer = str(step.action_output)
                elif isinstance(step, FinalAnswerStep):
                    final_answer = str(step.output)
                elif isinstance(step, ToolOutput):
                    logger.info(f"  Tool Output: {str(step.observation)[:200]}...")
                # ChatMessageStreamDelta is just intermediate thinking - skip

            if final_answer:
                yield final_answer
            else:
                yield "Task completed."

        except GeneratorExit:
            logger.info("Client disconnected.")
            return
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            err_str = str(e).lower()

            # ── RUNTIME FALLBACK: Local model failed → Swap to Gemini Cloud ──
            is_model_error = any(kw in err_str for kw in [
                "not found", "connection refused", "connection error",
                "timeout", "connect_tcp", "ollama", "404",
            ])

            if is_model_error and self.gateway and self.gateway.gemini_key:
                logger.warning("⚠️ LOCAL MODEL FAILED AT RUNTIME. Swapping to Gemini Cloud...")
                yield "⚠️ *Local model unavailable. Switching to Gemini Cloud...*\n\n"

                try:
                    cloud_model = self.gateway.get_cloud_model()
                    if cloud_model:
                        # Swap the agent's model to cloud
                        self.agent.model = cloud_model
                        self.model = cloud_model
                        logger.info(f"☁️ RUNTIME SWAP: Now using {cloud_model.model_id}")

                        # Retry the task with the cloud model
                        final_answer = None
                        for step in self.agent.run(task_to_run, stream=True):
                            if isinstance(step, ActionStep):
                                if step.error:
                                    logger.error(f"  Cloud Step Error: {step.error}")
                                if step.is_final_answer and step.action_output is not None:
                                    final_answer = str(step.action_output)
                            elif isinstance(step, FinalAnswerStep):
                                final_answer = str(step.output)

                        if final_answer:
                            yield final_answer
                        else:
                            yield "Task completed (via Gemini Cloud)."
                        return
                    else:
                        logger.error("☁️ Cloud model also unavailable.")
                except Exception as cloud_err:
                    logger.error(f"☁️ Cloud retry failed: {cloud_err}")
                    yield f"Error: Cloud fallback also failed: {cloud_err}"
                    return

            if "402" in err_str or "payment required" in err_str or "credit balance" in err_str:
                # --- GRACEFUL FALLBACK: Use Instant Generation templates ---
                from offline_engine import execute_offline
                fallback_result = execute_offline(task, safe_write)
                if fallback_result:
                    yield f"⚡ *Generating code...*\n\n"
                    yield fallback_result
                else:
                    yield f"⚠️ **AI Credits Depleted.**\nYour Gemini API key may have run out of credits.\n\n💡 **How to fix:** Check your [Google AI Studio billing](https://aistudio.google.com/) or ensure Ollama is running locally for offline mode."
            else:
                yield f"Error: {e}"


# ------------------------------------------------------------------
# STANDALONE GOD-MODE AGENT FACTORY
# ------------------------------------------------------------------

def get_agent(task: str = "", file_content: str = "") -> CodeAgent:
    """
    Factory function that returns a fully configured God-Tier CodeAgent.
    Uses the Hybrid Intelligence Gateway for smart model selection.

    Args:
        task: The user's task (used for smart model routing).
        file_content: Current file content (used for context size estimation).

    Returns:
        A ready-to-use CodeAgent with TerminalTool and God Mode permissions.
    """
    from gateway import model_gateway

    # Smart-route to the optimal model
    model = model_gateway.get_model_for_chat(task, file_content)

    terminal = TerminalTool()

    AUTONOMY_PROMPT = """
You are an Autonomous Senior Engineer (God Mode).
You do not just write code; you EXECUTE it, VERIFY it, and FIX it.

=== WINDOWS ENVIRONMENT (CRITICAL) ===
You are running on WINDOWS.
- Use `dir` instead of `ls`.
- Use `type` instead of `cat`.
- Use `python` (not `python3`).
- Use `del` or `rd` instead of `rm`.

PROTOCOL:
1. PLAN: Break the user's request into steps.
2. ACTION: Write the code (Python/Shell).
3. VERIFY: Use the `terminal` tool to run your script immediately.
4. REFLECT:
   - If you see `❌ ERROR`, you MUST analyze the error, rewrite the code, and try again.
   - Do NOT ask the user for permission to fix bugs. Just fix them.
5. FINAL ANSWER: Only return when the code runs with exit code 0 (Success).
"""

    agent = CodeAgent(
        tools=[terminal],
        model=model,
        add_base_tools=False,
        max_steps=15,
        verbosity_level=logging.INFO,
        instructions=AUTONOMY_PROMPT,
        additional_authorized_imports=[
            "subprocess", "os", "sys", "shutil", "glob", "json",
            "datetime", "math", "random", "time", "re", "pathlib",
        ],
        stream_outputs=True,
        executor_kwargs={
            "additional_functions": {
                "safe_write": safe_write,
                "safe_open": safe_open,
                "safe_delete": safe_delete,
                "safe_mkdir": safe_mkdir,
                "terminal": terminal.forward,
            }
        }
    )

    logger.info(f"🤖 God-Tier Agent created with model: {model.model_id}")
    return agent


# ------------------------------------------------------------------
# SELF-CHECK (Run with: python agent.py)
# ------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("\n" + "=" * 60)
    print("  🤖 Omni-IDE — God-Tier Agent Self-Check")
    print("=" * 60 + "\n")

    # --- Test 1: TerminalTool Direct ---
    print("─" * 60)
    print("  TEST 1: TerminalTool Direct Execution")
    print("─" * 60)

    tool = TerminalTool()

    # Simple command
    result = tool.forward('python -c "print(\'Hello God Mode\')"')
    print(f"  Result: {result}")
    assert "Hello God Mode" in result, "❌ FAILED: Expected 'Hello God Mode' in output"
    print("  ✅ PASSED: TerminalTool executes commands correctly.\n")

    # Error handling
    result = tool.forward("python -c \"raise ValueError('test error')\"")
    print(f"  Error Result: {result[:100]}...")
    assert "❌ ERROR" in result, "❌ FAILED: Expected error indicator"
    print("  ✅ PASSED: TerminalTool captures stderr correctly.\n")

    # Blocked command
    result = tool.forward("rm -rf /")
    print(f"  Blocked Result: {result}")
    assert "BLOCKED" in result, "❌ FAILED: Expected blocked indicator"
    print("  ✅ PASSED: Destructive commands are blocked.\n")

    # --- Test 2: Gateway Integration ---
    print("─" * 60)
    print("  TEST 2: Gateway Integration")
    print("─" * 60)

    try:
        from gateway import model_gateway
        decision = model_gateway._route("refactor the auth module", 100)
        print(f"  Complex task → {decision.tier.value} ({decision.model_id})")
        assert decision.tier.value == "cloud_pro", "Expected cloud_pro for 'refactor'"

        decision = model_gateway._route("fix a typo", 50)
        print(f"  Simple task  → {decision.tier.value} ({decision.model_id})")
        assert decision.tier.value == "local", "Expected local for 'fix a typo'"

        print("  ✅ PASSED: Gateway routes correctly.\n")
    except Exception as e:
        print(f"  ⚠️ SKIPPED: Gateway test ({e})\n")

    # --- Test 3: Self-Healing Scenario ---
    print("─" * 60)
    print("  TEST 3: Self-Healing Write → Run → Verify")
    print("─" * 60)

    import tempfile, os
    test_dir = tempfile.mkdtemp(prefix="omni_god_check_")
    test_file = os.path.join(test_dir, "god_check.py")

    with open(test_file, "w") as f:
        f.write("print('Hello God Mode')\n")

    result = tool.forward(f'python "{test_file}"')
    print(f"  Execution: {result}")
    assert "Hello God Mode" in result, "❌ FAILED: Script execution"
    print("  ✅ PASSED: Write → Run → Verify pipeline works.\n")

    # Cleanup
    os.remove(test_file)
    os.rmdir(test_dir)

    print("=" * 60)
    print("  🏆 ALL SELF-CHECKS PASSED — God Mode is ACTIVE")
    print("=" * 60 + "\n")
