import uvicorn
import logging
from dotenv import load_dotenv
import sys
import os
from config import ENV_PATH

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        print("--- Starting Uvicorn (No Reload) ---")
        load_dotenv(ENV_PATH)
        
        # Run without reload to see clear errors
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
        
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
