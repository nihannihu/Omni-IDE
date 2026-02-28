import os
import sys
from dotenv import load_dotenv

# Load key from .env
load_dotenv(override=True)
key = os.getenv("GEMINI_API_KEY")

from litellm import completion

model = "gemini/gemini-2.5-pro"
print(f"\n=======================")
print(f"Testing: {model}")
try:
    response = completion(
        model=model,
        messages=[{"role": "user", "content": "Say 'hello' in pure lowercase text, nothing else"}],
        api_key=key,
        max_tokens=5
    )
    print(f"✅ SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__} - {e}")
