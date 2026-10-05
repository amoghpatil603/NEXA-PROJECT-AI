import base64
import io
import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceEngine:
    """Provider-backed voice adapter.

    STT uses an installed local command when configured. TTS uses the browser
    by default; server-side synthesis can be enabled with NEXA_TTS_COMMAND.
    """

    def transcribe(self, audio_path: str) -> str:
        command = os.getenv("NEXA_STT_COMMAND")
        if not command:
            raise RuntimeError("No STT provider configured. Set NEXA_STT_COMMAND.")
        result = subprocess.run(
            command.format(input=audio_path),
            shell=True, capture_output=True, text=True, timeout=120, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "STT provider failed")
        return result.stdout.strip()

    def synthesize(self, text: str) -> bytes:
        command = os.getenv("NEXA_TTS_COMMAND")
        if not command:
            raise RuntimeError("No server-side TTS provider configured. Use browser Web Speech API or set NEXA_TTS_COMMAND.")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "speech.wav"
            result = subprocess.run(
                command.format(text=text, output=str(output)),
                shell=True, capture_output=True, text=True, timeout=120, check=False
            )
            if result.returncode != 0 or not output.exists():
                raise RuntimeError(result.stderr.strip() or "TTS provider failed")
            return output.read_bytes()

    def process_voice(self, text: str) -> dict:
        return {"transcript": text, "tts_configured": bool(os.getenv("NEXA_TTS_COMMAND"))}
