import os
import json
import fnmatch
from typing import Dict, List, Optional
from pathlib import Path

class IntelligenceCore:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else None
        self.memory_file = self.workspace_dir / ".omni_memory.json" if self.workspace_dir else None
        self.tasks_file = self.workspace_dir / ".omni_tasks.json" if self.workspace_dir else None

    # ------------------------------------------------------------------
    # 1. CONTEXT COLLECTOR (Git-Aware)
    # ------------------------------------------------------------------
    def _parse_gitignore(self) -> List[str]:
        """Reads .gitignore rules to prevent indexing unhelpful files."""
        base_ignores = ['.git', 'node_modules', '__pycache__', 'venv', 'env', '.env', '*.pyc', '*.exe', '.omni*']
        if not self.workspace_dir: return base_ignores
        
        gitignore_path = self.workspace_dir / '.gitignore'
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Basic glob conversion
                            line = line.rstrip('/')
                            base_ignores.append(f"*{line}*" if not line.startswith('*') else line)
            except Exception:
                pass
        return base_ignores

    def get_workspace_context(self, max_files: int = 20, max_chars_per_file: int = 1500) -> str:
        """Returns a lightweight map and content snippets of the current workspace."""
        if not self.workspace_dir or not self.workspace_dir.exists():
            return "No workspace folder is currently open."

        ignore_patterns = self._parse_gitignore()
        context_lines = ["--- WORKSPACE CONTEXT ---"]
        
        file_count = 0
        from pathlib import Path
        for root, dirs, files in os.walk(self.workspace_dir):
            # Apply ignores to directories
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pat) for pat in ignore_patterns)]
            
            for file in files:
                if any(fnmatch.fnmatch(file, pat) for pat in ignore_patterns):
                    continue
                
                if file_count >= max_files:
                    context_lines.append(f"\n... (Truncated. More than {max_files} files mapped)")
                    break
                    
                path = Path(root) / file
                rel_path = path.relative_to(self.workspace_dir)
                
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read(max_chars_per_file)
                        trunc_mark = "...\n[TRUNCATED]" if len(content) == max_chars_per_file else ""
                        context_lines.append(f"\n### File: {rel_path}\n```\n{content}{trunc_mark}\n```")
                        file_count += 1
                except UnicodeDecodeError:
                    context_lines.append(f"\n### File: {rel_path}\n[Binary/Non-Text File Ignored]")
                except Exception:
                    pass
            
            if file_count >= max_files:
                break
                
        return "\n".join(context_lines)

    # ------------------------------------------------------------------
    # 2. LIGHTWEIGHT MEMORY SYSTEM (With Compaction)
    # ------------------------------------------------------------------
    def load_memory(self) -> dict:
        if not self.memory_file or not self.memory_file.exists():
            return {"preferences": "", "notes": [], "recent_fixes": []}
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure structure
                if not isinstance(data, dict): data = {}
                data.setdefault("preferences", "")
                data.setdefault("notes", [])
                data.setdefault("recent_fixes", [])
                return data 
        except Exception:
            # [RECOVERY] Memory read failure -> safe recreation
            return {"preferences": "", "notes": [], "recent_fixes": []}

    def save_memory(self, memory_data: dict):
        if not self.memory_file: return
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, indent=2)

    def add_memory_note(self, note: str):
        mem = self.load_memory()
        mem["notes"].append(note)
        
        # [MEMORY COMPACTION] Retain only the 10 most recent chronological notes 
        # to prevent .omni_memory.json ballooning and injecting context window faults.
        if len(mem["notes"]) > 10:
            mem["notes"] = mem["notes"][-10:]
            
        self.save_memory(mem)

    # ------------------------------------------------------------------
    # 3. SMART TASK GENERATION
    # ------------------------------------------------------------------
    def load_tasks(self) -> list:
        if not self.tasks_file or not self.tasks_file.exists():
            return []
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def save_tasks(self, tasks: list):
        if not self.tasks_file: return
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)

    def generate_task_prompt(self, user_request: str) -> str:
        params = self.get_workspace_context()
        return f"""
{params}

The user wants to plan this objective: "{user_request}"
Analyze the workspace and generate a structured JSON array of tasks. 
Only output valid JSON with no markdown formatting.

Format:
[
  {{"task": "Name of task", "files_impacted": ["main.py"], "complexity": "Low/Medium/High"}}
]
"""

    # ------------------------------------------------------------------
    # 4. ERROR ANALYZER (Autonomous Debugging)
    # ------------------------------------------------------------------
    def build_debug_prompt(self, recent_error: str, code_snippet: str = "") -> str:
        ctx = self.get_workspace_context(max_files=5, max_chars_per_file=1000)
        return f"""
{ctx}

[AUTONOMOUS DEBUGGER]
The execution pipeline just crashed with this error:
```
{recent_error}
```

Target Code Snapshot (if available):
```
{code_snippet}
```

Provide:
1. The Root Cause Explanation.
2. The Suggested Fix.
3. Call the safe_write tool with the patched code if fixing it is straightforward.
"""

    # ------------------------------------------------------------------
    # 5. CODE HEALTH ANALYZER
    # ------------------------------------------------------------------
    def build_health_prompt(self) -> str:
        ctx = self.get_workspace_context(max_files=10)
        return f"""
{ctx}

[CODE HEALTH ANALYZER]
Act as an elite Staff Engineer. Review the provided workspace code for:
- Complexity / Readability
- Potential Bugs / Edge Cases
- Dead Code
- Performance Optimization
Provide a Code Health Score (0-100) at the top, followed by bulleted actionable advice.
"""
