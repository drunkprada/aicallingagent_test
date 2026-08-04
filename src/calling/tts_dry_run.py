"""Standalone dry run: synthesize a line of text via ElevenLabs and save it
as a local audio file. No Twilio, no dialing -- just the TTS call, for
quickly checking that the API key and voice work.

Usage:
    python -m src.calling.tts_dry_run "Hello, this is a test call" out.mp3
"""

import argparse
import sys
from pathlib import Path

from src.calling.tts_agent import TTSAgent, TTSError


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run ElevenLabs TTS on a line of text")
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument(
        "output_path",
        nargs="?",
        type=Path,
        default=Path("tts_dry_run_output.mp3"),
        help="Where to save the audio (default: tts_dry_run_output.mp3)",
    )
    args = parser.parse_args()

    agent = TTSAgent()
    try:
        audio = agent.synthesize(args.text)
    except TTSError as exc:
        print(f"TTS failed: {exc}", file=sys.stderr)
        sys.exit(1)

    args.output_path.write_bytes(audio)
    print(f"Wrote {len(audio)} bytes to {args.output_path}")


if __name__ == "__main__":
    main()
