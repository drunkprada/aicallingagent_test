import argparse
import sys
from contextlib import ExitStack
from typing import Optional

import openai

from src.config import EXTRACTION_MODE, ensure_directories
from src.ingestion.extractor import ExtractionError, extract_candidate
from src.ingestion.mock_extractor import extract_candidate_mock
from src.ingestion.parsers import ParserError, extract_text
from src.ingestion.resume_loader import hash_file, move_to_failed, move_to_processed, scan_incoming
from src.logging_config import setup_logging
from src.models.schema import Candidate, CandidateStatus
from src.storage.db import get_candidate, init_db, upsert_candidate
from src.storage.excel_export import export_candidates

logger = setup_logging()

REQUIRED_FIELDS = ("full_name",)
CONTACT_FIELDS = ("email", "phone")
EXTRACTION_ERROR_PREFIX = "extraction error:"

MOCK_MODE_NOTE = (
    "mock/offline extraction (EXTRACTION_MODE=mock) -- regex heuristics only, "
    "not verified by Claude. Manually verify every field before calling this candidate."
)


def _build_candidate(
    resume_hash: str, filename: str, extraction, mock: bool, existing: Optional[Candidate] = None
) -> Candidate:
    notes = []
    for field in REQUIRED_FIELDS:
        if not getattr(extraction, field):
            notes.append(f"missing {field}")
    if not any(getattr(extraction, f) for f in CONTACT_FIELDS):
        notes.append("missing both email and phone")

    if mock:
        notes.insert(0, MOCK_MODE_NOTE)
        status = CandidateStatus.NEEDS_REVIEW
    else:
        status = CandidateStatus.NEEDS_REVIEW if notes else CandidateStatus.EXTRACTED

    fields = {
        **extraction.model_dump(),
        "resume_hash": resume_hash,
        "source_filename": filename,
        "status": status,
        "extraction_notes": "; ".join(notes) if notes else None,
    }
    # Replace extraction fields while retaining creation time and any call answers.
    return existing.model_copy(update=fields) if existing else Candidate(**fields)


def _can_retry_extraction(candidate: Candidate) -> bool:
    if candidate.status == CandidateStatus.EXTRACTION_FAILED:
        return True
    # Older versions used NEEDS_REVIEW for both failed and successful extraction.
    # Only the pipeline's explicit error note identifies a legacy failure.
    return candidate.status == CandidateStatus.NEEDS_REVIEW and (
        candidate.extraction_notes or ""
    ).startswith(EXTRACTION_ERROR_PREFIX)


def run_ingest() -> None:
    if EXTRACTION_MODE not in {"openai", "mock"}:
        raise ValueError(
            "Invalid EXTRACTION_MODE. Expected 'openai' or 'mock', "
            f"got {EXTRACTION_MODE!r}."
        )

    ensure_directories()
    init_db()

    mock = EXTRACTION_MODE == "mock"
    client = None
    if mock:
        logger.warning(
            "EXTRACTION_MODE=mock -- using free regex-based extraction, not OpenAI. "
            "All candidates will be flagged needs_review."
        )

    files = list(scan_incoming())
    if not files:
        logger.info("No new resumes found in data/incoming_resumes/")
    else:
        logger.info("Found %d resume(s) to process", len(files))

    # Empty, duplicate-only and unparseable batches need no API credentials.
    # Once opened, one client serves the batch and closes even on an exception.
    with ExitStack() as resources:
        for path in files:
            resume_hash = hash_file(path)

            existing = get_candidate(resume_hash)
            if existing and not _can_retry_extraction(existing):
                logger.info("Skipping %s (already processed, hash matches an existing record)", path.name)
                move_to_processed(path)
                continue

            if existing:
                logger.info("Retrying extraction for %s", path.name)

            try:
                text = extract_text(path)
            except ParserError as exc:
                logger.error("Parse failed for %s: %s", path.name, exc)
                move_to_failed(path)
                continue

            try:
                if mock:
                    extraction = extract_candidate_mock(text)
                else:
                    if client is None:
                        client = resources.enter_context(openai.OpenAI())
                    extraction = extract_candidate(text, client)
            except ExtractionError as exc:
                logger.error("Extraction failed for %s: %s", path.name, exc)
                candidate = existing or Candidate(resume_hash=resume_hash, source_filename=path.name)
                candidate = candidate.model_copy(
                    update={
                        "source_filename": path.name,
                        "status": CandidateStatus.EXTRACTION_FAILED,
                        "extraction_notes": f"{EXTRACTION_ERROR_PREFIX} {exc}",
                    }
                )
                upsert_candidate(candidate)
                move_to_failed(path)
                continue

            candidate = _build_candidate(resume_hash, path.name, extraction, mock, existing)
            upsert_candidate(candidate)
            logger.info(
                "Processed %s -> status=%s", path.name, candidate.status.value
            )
            move_to_processed(path)

    output_path = export_candidates()
    logger.info("Excel export refreshed at %s", output_path)


def run_export() -> None:
    ensure_directories()
    init_db()
    output_path = export_candidates()
    logger.info("Excel export refreshed at %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume screening pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("ingest", help="Scan incoming resumes, extract, store, and export")
    subparsers.add_parser("export", help="Regenerate candidates.xlsx from the current database")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest()
    elif args.command == "export":
        run_export()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
