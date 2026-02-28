import sys
import os

# --- HOTFIX: PyInstaller sys.executable Interception ---
# When frozen, sys.executable points to OmniIDE.exe.
# /api/run uses sys.executable -c <code> to run scripts.
# We must intercept -c and run the code directly, otherwise we just spawn another IDE!
if len(sys.argv) >= 3 and sys.argv[1] == '-c':
    code_payload = sys.argv[2]
    try:
        # Execute in the global namespace like a normal script
        exec(code_payload, {'__name__': '__main__'})
        sys.exit(0)
    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        sys.exit(1)
# -------------------------------------------------------

import webview
import threading
import uvicorn
import sys
import os
import time
import urllib.request

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app 

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def wait_for_server():
    """Health check to ensure backend is ready before launching GUI."""
    url = "http://127.0.0.1:8000"
    retries = 20
    print(f"Waiting for server at {url}...")
    for i in range(retries):
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    print("Server is ready!")
                    return
        except Exception:
            time.sleep(0.5)
    print("Warning: Server execution timed out, launching GUI anyway...")

if __name__ == '__main__':
    # Start Backend in Thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # Wait for Health Check
    wait_for_server()

    # --- JS API Bridge ---
    class Api:
        def __init__(self, initial_folder):
            self.window = None
            self.initial_folder = initial_folder

        def get_initial_folder(self):
            return self.initial_folder

        def select_folder(self):
            # Opens a native OS folder selection dialog
            if self.window:
                result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
                if result and len(result) > 0:
                    return result[0]
            return None

    from session_manager import session_manager
    last_folder = session_manager.get_last_folder()
    
    api = Api(last_folder)

    # Launch GUI — Production Mode (no DevTools)
    window = webview.create_window(
        title='Omni-IDE', 
        url='http://localhost:8000',
        width=1200,
        height=800,
        resizable=True,
        confirm_close=True,
        js_api=api
    )
    api.window = window
    
    webview.start(debug=False)
