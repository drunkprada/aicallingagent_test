import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INCOMING_RESUMES_DIR = DATA_DIR / "incoming_resumes"
PROCESSED_DIR = DATA_DIR / "processed"
FAILED_DIR = PROCESSED_DIR / "failed"
EXPORTS_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "app.db"
EXCEL_EXPORT_PATH = EXPORTS_DIR / "candidates.xlsx"
LOGS_DIR = BASE_DIR / "logs"

EXTRACTION_MODEL = "gpt-4o"

# "openai" (default) calls the real API and costs tokens. "mock" uses a
# free, regex-based stand-in in src/ingestion/mock_extractor.py -- useful
# for exercising the pipeline with no API credits. Every candidate produced
# in mock mode is force-flagged NEEDS_REVIEW; never wire mock output
# straight to outbound calling.
EXTRACTION_MODE = os.getenv("EXTRACTION_MODE", "openai").strip().lower()

SUPPORTED_RESUME_EXTENSIONS = {".pdf", ".docx"}

# Phase 2 (outbound calling) -- text-to-speech. "Rachel", one of ElevenLabs'
# built-in premade voices; override with ELEVENLABS_VOICE_ID once a specific
# voice is chosen for the agent.
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
AUDIO_OUTPUT_FORMAT = "mp3_44100_128"


def ensure_directories() -> None:
    for directory in (
        INCOMING_RESUMES_DIR,
        PROCESSED_DIR,
        FAILED_DIR,
        EXPORTS_DIR,
        LOGS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
