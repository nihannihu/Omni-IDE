import os
from dotenv import load_dotenv
from config import ENV_PATH
from smolagents import LiteLLMModel
import litellm

load_dotenv(ENV_PATH)
api_key = os.getenv("GEMINI_API_KEY")

print("Key available:", bool(api_key))

# Test if we can pass fallbacks to LiteLLMModel
try:
    model = LiteLLMModel(
        model_id="gemini/gemini-1.5-pro",
        api_key=api_key,
        fallbacks=[{"model": "gemini/gemini-1.5-flash"}]
    )
    # We purposefully use a tiny completion to test
    messages = [{"role": "user", "content": "Say hi"}]
    response = model(messages)
    print("Response:", response.content)
    print("Success with fallbacks!")
except Exception as e:
    print("Failed wrapper with fallbacks:", e)

    try:
        model = LiteLLMModel(
            model_id="gemini/gemini-1.5-pro",
            api_key=api_key,
            fallbacks=["gemini/gemini-1.5-flash"]
        )
        response = model(messages)
        print("Response 2:", response.content)
        print("Success with fallbacks list of strings!")
    except Exception as e2:
         print("Failed string fallbacks too:", e2)

