# Lightweight Python 3.11 image for CPU inference (Cloud Brain)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# ffmpeg: needed for audio transcription (faster-whisper)
# git: needed for pip installs from git
# curl: for healthchecks
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to keep image small
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the API port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
