import os
import sys
from config import ENV_PATH

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def check_file(path, description):
    if os.path.exists(path):
        print(f"{GREEN}[PASS]{RESET} {description} found: {path}")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} {description} missing: {path}")
        return False

def check_env_var(var_name):
    value = os.getenv(var_name)
    if value and value.strip():
        print(f"{GREEN}[PASS]{RESET} Environment Variable {var_name} is set.")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} Environment Variable {var_name} is missing or empty.")
        return False

def check_dependency(package_name):
    import importlib.util
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"{GREEN}[PASS]{RESET} Dependency {package_name} is installed.")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} Dependency {package_name} is NOT installed.")
        return False

def main():
    print("=== Omni-IDE Environment Validator ===\n")
    all_pass = True

    # 1. Check .env
    if check_file(str(ENV_PATH), '.env file'):
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH)
        if not check_env_var('HUGGINGFACE_API_KEY'):
            all_pass = False
    else:
        all_pass = False

    # 2. Check Static Files
    static_files = [
        'static/index.html',
        'static/styles.css',
        'static/script.js'
    ]
    for f in static_files:
        if not check_file(f, f):
            all_pass = False

    # 3. Check Dependencies
    if not check_dependency('webview'): # pywebview module name is webview
        all_pass = False
    if not check_dependency('fastapi'):
        all_pass = False

    print("\n" + "="*40)
    if all_pass:
        print(f"{GREEN}READY FOR BUILD{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}ENVIRONMENT VALIDATION FAILED{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
