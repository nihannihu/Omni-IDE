import platform
import subprocess
import re
import time

WINDOWS_UNSUPPORTED = {
    "termios": "Use msvcrt on Windows",
    "tty": "Use msvcrt or keyboard library",
    "fcntl": "Not available on Windows"
}

class Logger:
    def __init__(self):
        self.stdout = []
        self.stderr = []

    def log_info(self, msg):
        self.stdout.append(msg)
        
    def log_error(self, msg):
        self.stderr.append(msg)
        
    def get_output(self):
        out = "\n".join(self.stdout) + "\n" if self.stdout else ""
        err = "\n".join(self.stderr) + "\n" if self.stderr else ""
        return out, err

class ImportScanner:
    @staticmethod
    def detect_missing_module(stderr_output):
        match = re.search(r"No module named '([^']+)'", stderr_output)
        if match:
            return match.group(1)
        return None

class CompatibilityValidator:
    @staticmethod
    def detect_os():
        system = platform.system().lower()
        if "windows" in system:
            return "windows"
        elif "darwin" in system:
            return "mac"
        return "linux"

    @staticmethod
    def is_supported(module_name):
        current_os = CompatibilityValidator.detect_os()
        if current_os == "windows" and module_name in WINDOWS_UNSUPPORTED:
            return False, WINDOWS_UNSUPPORTED[module_name]
        return True, ""

from environment_manager import EnvironmentManager

class InstallerService:
    @staticmethod
    def install_module(module_name, base_cmd, env, logger, working_directory):
        try:
            # Check lockfile first (cache hit)
            if EnvironmentManager.is_dependency_locked(working_directory, module_name):
                logger.log_info(f"[RUNTIME] Deps Installed: 0 (cache hit for '{module_name}')")
                return True

            start_time = time.time()
            ident_proc = subprocess.run(base_cmd + ["-c", "import sys; print(f'Target Python: {sys.executable} | Version: {sys.version}')"], capture_output=True, text=True, env=env)
            logger.log_info(f"[⚙️ AUTO-PIP] {ident_proc.stdout.strip()}")
            logger.log_info(f"[⚙️ AUTO-PIP] Installing '{module_name}' to isolated project environment...")
            
            # 1. Upgrade core build tools
            subprocess.run(base_cmd + ["-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], capture_output=True, env=env)
            
            # 2. Force install from global cache to optimize speeds
            cache_dir = EnvironmentManager.get_global_cache_dir()
            pip_proc = subprocess.run(
                base_cmd + ["-m", "pip", "install", module_name, "--cache-dir", cache_dir, "-v"],
                capture_output=True,
                text=True,
                env=env
            )
            
            duration = (time.time() - start_time) * 1000
            if pip_proc.returncode == 0:
                logger.log_info(f"\n✅ [INSTALLED] Successfully installed '{module_name}'! ({duration:.1f}ms)")
                logger.log_info(f"👉 [EXECUTION CONTINUES] Please click 'Run Code' again to execute your script.")
                # Update Lockfile
                EnvironmentManager.update_lockfile(working_directory, module_name)
                return True
            else:
                logger.log_info(f"\n❌ [AUTO-PIP] Failed to install '{module_name}'.")
                logger.log_error(f"\n--- PIP INSTALL ERROR ---\n{pip_proc.stderr}")
                
                if "3.13" in ident_proc.stdout or "3.14" in ident_proc.stdout:
                    logger.log_info(f"\n💡 HINT: Your system Python is very new. Pre-compiled binaries for '{module_name}' might not exist yet. Please install Python 3.12 for maximum compatibility.")
                
                # Rollback corrupt environment state if install critically failed
                # EnvironmentManager.rollback_env(working_directory)
                return False
        except Exception as e:
            logger.log_info(f"\n❌ [AUTO-PIP] Error running pip: {e}")
            return False

class DependencyManager:
    @staticmethod
    def handle_auto_pip(stderr_output, base_cmd, env, working_directory):
        logger = Logger()
        
        missing_module = ImportScanner.detect_missing_module(stderr_output)
        if not missing_module:
            return "", ""
            
        logger.log_info(f"\n[⚙️ AUTO-PIP] Missing module '{missing_module}' detected!")
        
        current_os = CompatibilityValidator.detect_os()
        logger.log_info(f"[⚙️ DEPENDENCY CHECK] OS: {current_os.upper()}")
        
        is_supported, reason = CompatibilityValidator.is_supported(missing_module)
        if not is_supported:
            logger.log_info(f"⏭️ [SKIPPED: PLATFORM] Skipped '{missing_module}' — not supported on Windows. ({reason})")
            logger.log_info(f"🚀 [EXECUTION CONTINUES] Skipping auto-install to prevent pipeline failure.")
            return logger.get_output()
            
        InstallerService.install_module(missing_module, base_cmd, env, logger, working_directory)
        
        return logger.get_output()
