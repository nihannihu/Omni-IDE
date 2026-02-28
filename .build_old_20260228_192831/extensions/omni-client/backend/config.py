import sys
import os
from pathlib import Path

def get_portable_root():
    """
    Returns the folder where the actual EXE or Script is running.
    NOT the temp folder (_MEI) and NOT the User Home.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE (PyInstaller)
        # sys.executable is the path to the EXE
        return Path(sys.executable).parent
    else:
        # Running as Python Script
        # __file__ is backend/config.py, so parent.parent is the project root
        return Path(__file__).parent.parent

# Define portable paths
PORTABLE_ROOT = get_portable_root()
ENV_PATH = PORTABLE_ROOT / ".env"
CONFIG_PATH = PORTABLE_ROOT / ".omni_ide_config.json"
