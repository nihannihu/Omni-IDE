import os
import tempfile
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        # Force CPU to save VRAM for the LLM
        # if device == "auto": ... removed to force CPU
        
        logger.info(f"Loading Whisper model: {model_size} on cpu with {compute_type}...")
        self.model = WhisperModel(model_size, device="cpu", compute_type=compute_type)
        logger.info("Whisper model loaded on CPU.")

    def transcribe(self, audio_bytes: bytes) -> str:
        try:
            # Input Validation: Prevent huge payloads (DoS)
            if len(audio_bytes) > 2 * 1024 * 1024:  # 2MB limit
                logger.warning(f"Audio chunk too large: {len(audio_bytes)} bytes. Dropping.")
                return ""

            # Create a temporary file to store the audio bytes
            # faster-whisper handles various formats (wav, mp3, webm, etc.) via ffmpeg
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name

            segments, info = self.model.transcribe(temp_audio_path, beam_size=5)
            
            full_text = ""
            for segment in segments:
                full_text += segment.text + " "

            # Cleanup
            os.remove(temp_audio_path)
            
            return full_text.strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
