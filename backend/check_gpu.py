import torch
import sys

print(f"Torch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device count: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA NOT available. Torch is running on CPU.")

try:
    from faster_whisper import WhisperModel
    print("faster-whisper imported successfully.")
except ImportError as e:
    print(f"faster-whisper import failed: {e}")
