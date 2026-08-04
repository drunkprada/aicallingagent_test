"""Standalone dry run: extract structured fields from a single resume via
the OpenAI API and print the result. No database, no folder scan, no file
moving -- just the extraction call, for quickly checking that the API key
and prompt work.

Usage:
    python -m src.dry_run path/to/resume.pdf
"""

import argparse
import json
import sys
from pathlib import Path

import openai

from src.ingestion.extractor import ExtractionError, extract_candidate
from src.ingestion.parsers import ParserError, extract_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run a single resume through the OpenAI extractor")
    parser.add_argument("resume_path", type=Path, help="Path to a .pdf or .docx resume")
    args = parser.parse_args()

    if not args.resume_path.exists():
        print(f"File not found: {args.resume_path}", file=sys.stderr)
        sys.exit(1)

    try:
        text = extract_text(args.resume_path)
    except ParserError as exc:
        print(f"Parse failed: {exc}", file=sys.stderr)
        sys.exit(1)

    client = openai.OpenAI()
    try:
        extraction = extract_candidate(text, client)
    except ExtractionError as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(extraction.model_dump(), indent=2))


if __name__ == "__main__":
    main()
