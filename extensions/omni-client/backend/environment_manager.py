import os
import subprocess
import json
import time
from config import PORTABLE_ROOT

class EnvironmentManager:
    ENV_DIR_NAME = ".antigravity_env"
    LOCKFILE_NAME = ".antigravity_lock.json"
    
    @staticmethod
    def get_global_cache_dir():
        # Portable cache layer: root/.antigravity_cache/wheels/
        cache_dir = PORTABLE_ROOT / ".antigravity_cache" / "wheels"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return str(cache_dir)

    @staticmethod
    def setup_project_env(working_directory, base_python_cmd):
        """
        Ensures a zero-config virtual environment exists for the project.
        Returns the command to execute the venv python and any logs.
        """
        start_time = time.time()
        env_path = os.path.join(working_directory, EnvironmentManager.ENV_DIR_NAME)
        
        if os.name == 'nt':
            venv_python = os.path.join(env_path, "Scripts", "python.exe")
        else:
            venv_python = os.path.join(env_path, "bin", "python")

        logs = []
        is_new = False
        
        if not os.path.exists(env_path):
            logs.append(f"[RUNTIME] Initializing isolated project environment in {EnvironmentManager.ENV_DIR_NAME}...")
            is_new = True
            try:
                # Build environment using the base system python
                subprocess.run(base_python_cmd + ["-m", "venv", env_path], check=True, capture_output=True)
                logs.append("[RUNTIME] Environment created successfully.")
            except subprocess.CalledProcessError as e:
                logs.append(f"[RUNTIME] ❌ Failed to create environment: {e.stderr.decode('utf-8', errors='ignore')}")
                # Fallback to system python if venv fails
                return base_python_cmd, "\n".join(logs) + "\n", (time.time() - start_time) * 1000
        
        # Determine python version
        python_version = "unknown"
        try:
            res = subprocess.run([venv_python, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"], capture_output=True, text=True)
            if res.returncode == 0:
                python_version = res.stdout.strip()
        except Exception:
            pass

        # Ensure lockfile exists
        lockfile_path = os.path.join(working_directory, EnvironmentManager.LOCKFILE_NAME)
        if not os.path.exists(lockfile_path):
            with open(lockfile_path, "w") as f:
                json.dump({
                    "python_version": python_version,
                    "dependencies": {},
                    "last_updated": time.time()
                }, f, indent=2)

        duration = (time.time() - start_time) * 1000
        logs.append(f"[RUNTIME] Env Ready: {duration:.1f}ms")
        
        return [venv_python], "\n".join(logs) + "\n", duration

    @staticmethod
    def is_dependency_locked(working_directory, module_name):
        lockfile_path = os.path.join(working_directory, EnvironmentManager.LOCKFILE_NAME)
        if os.path.exists(lockfile_path):
            try:
                with open(lockfile_path, "r") as f:
                    data = json.load(f)
                    return module_name in data.get("dependencies", {})
            except Exception:
                pass
        return False

    @staticmethod
    def update_lockfile(working_directory, module_name, version="latest"):
        lockfile_path = os.path.join(working_directory, EnvironmentManager.LOCKFILE_NAME)
        data = {
            "python_version": "unknown",
            "dependencies": {},
            "last_updated": time.time()
        }
        
        if os.path.exists(lockfile_path):
            try:
                with open(lockfile_path, "r") as f:
                    data = json.load(f)
            except Exception:
                pass
        
        data["dependencies"][module_name] = version
        data["last_updated"] = time.time()
        
        with open(lockfile_path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def rollback_env(working_directory):
        """If environment becomes corrupt, remove it to trigger rebuild next run."""
        env_path = os.path.join(working_directory, EnvironmentManager.ENV_DIR_NAME)
        import shutil
        try:
            if os.path.exists(env_path):
                shutil.rmtree(env_path)
        except Exception:
            pass
