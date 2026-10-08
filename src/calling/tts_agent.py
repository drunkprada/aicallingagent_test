"""ElevenLabs text-to-speech wrapper for the Phase 2 calling agent.

Synthesizes the REQUIRED_CALL_QUESTIONS prompts (and other agent dialogue)
into audio. Standalone and testable without Twilio -- see tts_dry_run.py to
generate a local audio file. Once Twilio streaming is wired up, CallAgent
will pipe this audio into the <Stream> instead of writing it to disk.
"""

import logging

from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError

from src.config import AUDIO_OUTPUT_FORMAT, ELEVENLABS_MODEL, ELEVENLABS_VOICE_ID

logger = logging.getLogger("resume_agent")


class TTSError(Exception):
    """Raised when ElevenLabs fails to synthesize audio."""


class TTSAgent:
    def __init__(self, client: ElevenLabs | None = None):
        self.client = client or ElevenLabs()

    def synthesize(self, text: str) -> bytes:
        """Convert text to speech and return the raw audio bytes."""
        if not text.strip():
            raise TTSError("Cannot synthesize empty text")

        try:
            audio_stream = self.client.text_to_speech.convert(
                ELEVENLABS_VOICE_ID,
                text=text,
                model_id=ELEVENLABS_MODEL,
                output_format=AUDIO_OUTPUT_FORMAT,
            )
            # The SDK sends the request lazily when the stream is consumed.
            return b"".join(audio_stream)
        except ApiError as exc:
            raise TTSError(f"ElevenLabs TTS failed: {exc}") from exc
