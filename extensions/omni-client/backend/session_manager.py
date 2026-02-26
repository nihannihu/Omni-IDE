import json
import os
from pathlib import Path
import logging
from config import CONFIG_PATH

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.config_path = CONFIG_PATH

    def get_last_folder(self) -> str:
        """Read the last opened folder from the config file."""
        if not self.config_path.exists():
            return None
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("last_opened_folder")
        except Exception as e:
            logger.error(f"Error reading session config: {e}")
            return None

    def save_last_folder(self, path: str):
        """Save the last opened folder to the config file."""
        try:
            data = {"last_opened_folder": path}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Session saved: {path}")
        except Exception as e:
            logger.error(f"Error saving session config: {e}")

session_manager = SessionManager()
