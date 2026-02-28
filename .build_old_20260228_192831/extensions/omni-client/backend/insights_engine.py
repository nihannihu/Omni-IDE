import os
import re
import time
import uuid
import logging
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

from analytics_engine import analytics_engine

# ------------------------------------------------------------------
# INSIGHT EVENT SCHEMA
# ------------------------------------------------------------------

class Insight:
    def __init__(self, insight_type: str, severity: str, title: str,
                 description: str, file_path: str):
        self.id = str(uuid.uuid4())
        self.type = insight_type
        self.severity = severity
        self.title = title
        self.description = description
        self.file = file_path
        self.created_at = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "file": self.file,
            "created_at": self.created_at
        }

# ------------------------------------------------------------------
# DETERMINISTIC ANALYZERS (MVP — No LLM)
# ------------------------------------------------------------------

SAFE_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css',
                   '.json', '.md', '.yaml', '.yml', '.toml', '.sh'}
IGNORED_DIRS = {'venv', 'venv_gpu', 'node_modules', '__pycache__', '.git',
                '.idea', '.vscode', 'dist', 'build', '.next', '.omni'}

def _collect_files(workspace: str, max_files: int = 200) -> List[Path]:
    """Collect workspace files respecting scan limits."""
    collected = []
    try:
        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for fname in files:
                if len(collected) >= max_files:
                    return collected
                fpath = Path(root) / fname
                if fpath.suffix in SAFE_EXTENSIONS:
                    collected.append(fpath)
    except Exception as e:
        logger.error(f"File collection error: {e}")
    return collected


def analyze_long_functions(files: List[Path], threshold: int = 120) -> List[Insight]:
    """Flag Python functions exceeding threshold lines."""
    insights = []
    for fpath in files:
        if fpath.suffix != '.py':
            continue
        try:
            lines = fpath.read_text(encoding='utf-8', errors='ignore').splitlines()
            func_start = None
            func_name = ""
            for i, line in enumerate(lines):
                match = re.match(r'^(\s*)def\s+(\w+)', line)
                if match:
                    if func_start is not None:
                        length = i - func_start
                        if length > threshold:
                            insights.append(Insight(
                                "LONG_FUNCTION", "medium",
                                f"Long function: {func_name}()",
                                f"Function `{func_name}` is {length} lines (threshold: {threshold})",
                                str(fpath)
                            ))
                    func_start = i
                    func_name = match.group(2)
            # Check last function in file
            if func_start is not None:
                length = len(lines) - func_start
                if length > threshold:
                    insights.append(Insight(
                        "LONG_FUNCTION", "medium",
                        f"Long function: {func_name}()",
                        f"Function `{func_name}` is {length} lines (threshold: {threshold})",
                        str(fpath)
                    ))
        except Exception:
            continue
    return insights


def analyze_large_files(files: List[Path], threshold: int = 800) -> List[Insight]:
    """Flag files exceeding threshold line count."""
    insights = []
    for fpath in files:
        try:
            line_count = len(fpath.read_text(encoding='utf-8', errors='ignore').splitlines())
            if line_count > threshold:
                insights.append(Insight(
                    "LARGE_FILE", "low",
                    f"Large file: {fpath.name}",
                    f"File has {line_count} lines (threshold: {threshold})",
                    str(fpath)
                ))
        except Exception:
            continue
    return insights


def analyze_todo_fixme(files: List[Path]) -> List[Insight]:
    """Aggregate TODO/FIXME occurrences."""
    insights = []
    for fpath in files:
        try:
            content = fpath.read_text(encoding='utf-8', errors='ignore')
            todos = re.findall(r'#\s*(TODO|FIXME|HACK|XXX)\s*[:\-]?\s*(.*)', content, re.IGNORECASE)
            if todos:
                items = [f"{tag}: {msg.strip()}" for tag, msg in todos[:5]]
                summary = "; ".join(items)
                if len(todos) > 5:
                    summary += f" (+{len(todos) - 5} more)"
                insights.append(Insight(
                    "TODO_FIXME", "low",
                    f"{len(todos)} TODO/FIXME in {fpath.name}",
                    summary,
                    str(fpath)
                ))
        except Exception:
            continue
    return insights


def analyze_dead_files(files: List[Path], workspace: str) -> List[Insight]:
    """Best-effort dead file detection: Python files not imported anywhere."""
    insights = []
    py_files = [f for f in files if f.suffix == '.py']
    all_content = ""
    for f in py_files:
        try:
            all_content += f.read_text(encoding='utf-8', errors='ignore') + "\n"
        except Exception:
            continue

    for fpath in py_files:
        module_name = fpath.stem
        # Skip common entry points and test files
        if module_name in ('__init__', 'main', 'setup', 'conftest', 'manage'):
            continue
        if module_name.startswith('test_') or module_name.startswith('qa_'):
            continue
        # Check if imported anywhere
        patterns = [
            f"import {module_name}",
            f"from {module_name}",
            f"import {module_name} as",
        ]
        found = any(p in all_content for p in patterns)
        if not found:
            insights.append(Insight(
                "DEAD_FILE", "low",
                f"Potentially unused: {fpath.name}",
                f"Module `{module_name}` is not imported by any other Python file in the workspace.",
                str(fpath)
            ))
    return insights


def analyze_complexity(files: List[Path], threshold: int = 800) -> List[Insight]:
    """Simple complexity heuristic based on line count (alias for large file with higher severity)."""
    insights = []
    for fpath in files:
        try:
            line_count = len(fpath.read_text(encoding='utf-8', errors='ignore').splitlines())
            if line_count > threshold * 1.5:  # 1200+ lines = high complexity
                insights.append(Insight(
                    "HIGH_COMPLEXITY", "high",
                    f"High complexity: {fpath.name}",
                    f"File has {line_count} lines — consider breaking into smaller modules.",
                    str(fpath)
                ))
        except Exception:
            continue
    return insights


# ------------------------------------------------------------------
# INSIGHTS ENGINE
# ------------------------------------------------------------------

class InsightsEngine:
    """Non-blocking background insights worker."""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.insights_cache: Dict[str, dict] = {}  # id -> insight dict
        self._last_scan_time: float = 0
        self._debounce_seconds: float = 15.0
        self._max_files: int = 200
        self._lock = threading.Lock()
        self._is_scanning = False

    def run_scan(self) -> List[dict]:
        """
        Execute a full deterministic scan. Respects debounce rules.
        Returns list of insight dicts generated in this scan.
        """
        now = time.time()
        if now - self._last_scan_time < self._debounce_seconds:
            logger.info(f"[INSIGHTS] Debounced — last scan was {now - self._last_scan_time:.1f}s ago")
            return list(self.insights_cache.values())

        if self._is_scanning:
            logger.info("[INSIGHTS] Scan already in progress, skipping.")
            return list(self.insights_cache.values())

        self._is_scanning = True
        scan_start = time.time()
        new_insights: List[Insight] = []

        try:
            files = _collect_files(self.workspace_dir, self._max_files)
            logger.info(f"[INSIGHTS] Scanning {len(files)} files...")

            new_insights += analyze_long_functions(files)
            new_insights += analyze_large_files(files)
            new_insights += analyze_todo_fixme(files)
            new_insights += analyze_dead_files(files, self.workspace_dir)
            new_insights += analyze_complexity(files)

            # Enforce 2s max runtime
            elapsed = time.time() - scan_start
            if elapsed > 2.0:
                logger.warning(f"[INSIGHTS] Scan exceeded 2s budget ({elapsed:.2f}s). Results may be partial.")

        except Exception as e:
            logger.error(f"[INSIGHTS] Scan failed: {e}")
        finally:
            self._is_scanning = False
            self._last_scan_time = time.time()

        # Replace cache atomically
        with self._lock:
            self.insights_cache = {ins.id: ins.to_dict() for ins in new_insights}

        scan_duration = time.time() - scan_start
        logger.info(f"[INSIGHTS] Scan complete: {len(new_insights)} insights in {scan_duration:.2f}s")
        
        # Analytics Hook
        analytics_engine.log_event("insight_trigger", {
            "insight_count": len(new_insights),
            "scan_duration_ms": int(scan_duration * 1000)
        })
        
        return list(self.insights_cache.values())

    def get_insights(self) -> List[dict]:
        """Return cached insights."""
        with self._lock:
            return list(self.insights_cache.values())

    def dismiss_insight(self, insight_id: str) -> bool:
        """Remove an insight from the cache."""
        with self._lock:
            if insight_id in self.insights_cache:
                del self.insights_cache[insight_id]
                return True
            return False

    def accept_insight(self, insight_id: str) -> bool:
        """Track that an insight was accepted/acted upon."""
        with self._lock:
            if insight_id in self.insights_cache:
                insight = self.insights_cache[insight_id]
                analytics_engine.log_event("insight_accepted", {
                    "insight_id": insight_id,
                    "insight_type": insight.get("type")
                })
                # Auto-dismiss after acceptance for UX
                del self.insights_cache[insight_id]
                return True
            return False

    def format_insights_text(self) -> str:
        """Format insights for chat output."""
        insights = self.get_insights()
        if not insights:
            return "✅ **No issues detected.** Your workspace looks clean!"

        severity_icons = {"high": "🔴", "medium": "🟡", "low": "🔵"}
        lines = [f"### 🔍 Background Insights ({len(insights)} found)\n"]
        for ins in sorted(insights, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["severity"], 3)):
            icon = severity_icons.get(ins["severity"], "⚪")
            fname = Path(ins["file"]).name
            lines.append(f"- {icon} **[{ins['type']}]** {ins['title']} — `{fname}`")
            lines.append(f"  _{ins['description']}_")
        return "\n".join(lines)
