import os
from dotenv import set_key
from pathlib import Path

test_env = Path("test_missing.env")
if test_env.exists():
    test_env.unlink()

print(f"Before set_key, exists? {test_env.exists()}")
set_key(str(test_env), "TEST_KEY", "TEST_VAL")
print(f"After set_key, exists? {test_env.exists()}")
with open(test_env, 'r') as f:
    print("Content:", f.read())

if test_env.exists():
    test_env.unlink()
