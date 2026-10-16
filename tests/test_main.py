import shutil
from unittest.mock import MagicMock

import openpyxl
import pytest
from docx import Document

from src import main
from src.ingestion import resume_loader
from src.ingestion.extractor import ExtractionError
from src.models.schema import Candidate, CandidateStatus, ResumeExtraction
from src.storage import db, excel_export


def test_invalid_extraction_mode_fails_before_side_effects(monkeypatch):
    ensure_directories = MagicMock()
    init_db = MagicMock()
    openai_client = MagicMock()

    monkeypatch.setattr(main, "EXTRACTION_MODE", "typo")
    monkeypatch.setattr(main, "ensure_directories", ensure_directories)
    monkeypatch.setattr(main, "init_db", init_db)
    monkeypatch.setattr(main.openai, "OpenAI", openai_client)

    with pytest.raises(
        ValueError,
        match="Invalid EXTRACTION_MODE.*'openai' or 'mock'.*'typo'",
    ):
        main.run_ingest()

    ensure_directories.assert_not_called()
    init_db.assert_not_called()
    openai_client.assert_not_called()


@pytest.fixture
def offline_ingest(tmp_path, monkeypatch):
    incoming = tmp_path / "incoming"
    processed = tmp_path / "processed"
    failed = processed / "failed"
    for directory in (incoming, processed, failed):
        directory.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "candidates.db"
    output = tmp_path / "candidates.xlsx"
    extractor = MagicMock()
    client = MagicMock()

    monkeypatch.setattr(resume_loader, "INCOMING_RESUMES_DIR", incoming)
    monkeypatch.setattr(resume_loader, "PROCESSED_DIR", processed)
    monkeypatch.setattr(resume_loader, "FAILED_DIR", failed)
    monkeypatch.setattr(main, "EXTRACTION_MODE", "openai")
    monkeypatch.setattr(main, "ensure_directories", lambda: None)
    monkeypatch.setattr(main, "init_db", lambda: db.init_db(db_path))
    monkeypatch.setattr(main, "get_candidate", lambda h: db.get_candidate(h, db_path))
    monkeypatch.setattr(main, "upsert_candidate", lambda c: db.upsert_candidate(c, db_path))
    monkeypatch.setattr(excel_export, "get_all_candidates", lambda: db.get_all_candidates(db_path))
    monkeypatch.setattr(main, "export_candidates", lambda: excel_export.export_candidates(output))
    monkeypatch.setattr(main.openai, "OpenAI", client)
    monkeypatch.setattr(main, "extract_candidate", extractor)
    return incoming, processed, failed, db_path, output, extractor, client


def _resume(incoming, name="resume.docx"):
    document = Document()
    document.add_paragraph("Jane Doe")
    document.add_paragraph("jane@example.com")
    path = incoming / name
    document.save(path)
    return path, resume_loader.hash_file(path)


def test_failed_extraction_can_be_retried(offline_ingest):
    incoming, processed, failed, db_path, _, extractor, _ = offline_ingest
    path, resume_hash = _resume(incoming)
    extractor.side_effect = [
        ExtractionError("temporary API failure"),
        ResumeExtraction(full_name="Jane Doe", email="jane@example.com"),
    ]

    main.run_ingest()
    first = db.get_candidate(resume_hash, db_path)
    assert (failed / path.name).exists()
    shutil.move(failed / path.name, incoming / path.name)

    main.run_ingest()
    recovered = db.get_candidate(resume_hash, db_path)
    assert recovered.full_name == "Jane Doe"
    assert recovered.status == CandidateStatus.EXTRACTED
    assert recovered.extraction_notes is None
    assert recovered.created_at == first.created_at
    assert extractor.call_count == 2
    assert len(db.get_all_candidates(db_path)) == 1
    assert (processed / path.name).exists()
    assert not (failed / path.name).exists()


@pytest.mark.parametrize("status", [
    CandidateStatus.EXTRACTED, CandidateStatus.NEEDS_REVIEW, CandidateStatus.CALL_COMPLETED,
])
def test_successful_records_are_still_deduplicated(offline_ingest, status):
    incoming, processed, _, db_path, _, extractor, _ = offline_ingest
    path, resume_hash = _resume(incoming)
    db.init_db(db_path)
    db.upsert_candidate(Candidate(
        resume_hash=resume_hash, source_filename="original.docx", status=status,
        full_name="Reviewed Name", extraction_notes="missing both email and phone",
        call_attempts=2, salary_expectation="reviewed value",
    ), db_path)
    before = db.get_candidate(resume_hash, db_path)

    main.run_ingest()

    extractor.assert_not_called()
    assert db.get_candidate(resume_hash, db_path) == before
    assert (processed / path.name).exists()
    assert len(db.get_all_candidates(db_path)) == 1


def test_legacy_failure_retry_preserves_existing_call_data(offline_ingest):
    incoming, processed, _, db_path, _, extractor, _ = offline_ingest
    path, resume_hash = _resume(incoming)
    db.init_db(db_path)
    db.upsert_candidate(Candidate(
        resume_hash=resume_hash, source_filename="old-name.docx",
        status=CandidateStatus.NEEDS_REVIEW,
        extraction_notes="extraction error: previous API failure",
        salary_expectation="45000", nationality="provided answer",
        notice_period="one month", call_status="failed", call_attempts=2,
        last_call_at="2026-01-01T10:00:00+00:00",
    ), db_path)
    before = db.get_candidate(resume_hash, db_path)
    extractor.return_value = ResumeExtraction(full_name="Jane Doe", email="jane@example.com")

    main.run_ingest()

    after = db.get_candidate(resume_hash, db_path)
    assert after.full_name == "Jane Doe"
    assert after.source_filename == path.name
    assert after.status == CandidateStatus.EXTRACTED
    assert after.extraction_notes is None
    for field in ("created_at", "salary_expectation", "nationality", "notice_period",
                  "call_status", "call_attempts", "last_call_at"):
        assert getattr(after, field) == getattr(before, field)
    assert (processed / path.name).exists()


def test_extraction_failure_does_not_stop_batch_or_disappear_from_export(offline_ingest):
    incoming, processed, failed, db_path, output, extractor, _ = offline_ingest
    bad, bad_hash = _resume(incoming, "a-failure.docx")
    good, _ = _resume(incoming, "b-success.docx")
    # Make the two resumes different even if ZIP timestamps are identical.
    document = Document(good)
    document.add_paragraph("Python")
    document.save(good)
    good_hash = resume_loader.hash_file(good)
    extractor.side_effect = [
        ExtractionError("temporary API failure"),
        ResumeExtraction(full_name="Jane Doe", email="jane@example.com"),
    ]

    main.run_ingest()

    assert db.get_candidate(bad_hash, db_path).status.value == "extraction_failed"
    assert db.get_candidate(good_hash, db_path).status == CandidateStatus.EXTRACTED
    assert (failed / bad.name).exists()
    assert (processed / good.name).exists()
    workbook = openpyxl.load_workbook(output)
    rows = list(workbook.active.values)
    status_column = rows[0].index("Status")
    assert {row[status_column] for row in rows[1:]} == {"extraction_failed", "extracted"}
    workbook.close()


def test_repeated_extraction_failure_preserves_review_and_call_data(offline_ingest):
    incoming, _, failed, db_path, _, extractor, _ = offline_ingest
    path, resume_hash = _resume(incoming)
    db.init_db(db_path)
    db.upsert_candidate(Candidate(
        resume_hash=resume_hash, source_filename=path.name,
        status=CandidateStatus.NEEDS_REVIEW,
        extraction_notes="extraction error: old failure", full_name="Reviewed Name",
        call_attempts=2, call_status="failed",
    ), db_path)
    before = db.get_candidate(resume_hash, db_path)
    extractor.side_effect = ExtractionError("new failure")

    main.run_ingest()

    after = db.get_candidate(resume_hash, db_path)
    assert after.status.value == "extraction_failed"
    assert after.extraction_notes == "extraction error: new failure"
    assert after.full_name == before.full_name
    assert after.call_attempts == before.call_attempts
    assert after.call_status == before.call_status
    assert after.created_at == before.created_at
    assert (failed / path.name).exists()


def test_retry_in_mock_mode_stays_flagged_for_review(offline_ingest, monkeypatch):
    incoming, processed, _, db_path, _, extractor, client = offline_ingest
    path, resume_hash = _resume(incoming)
    db.init_db(db_path)
    db.upsert_candidate(Candidate(
        resume_hash=resume_hash, source_filename=path.name,
        status=CandidateStatus.NEEDS_REVIEW,
        extraction_notes="extraction error: old failure",
    ), db_path)
    monkeypatch.setattr(main, "EXTRACTION_MODE", "mock")

    main.run_ingest()

    after = db.get_candidate(resume_hash, db_path)
    assert after.full_name == "Jane Doe"
    assert after.status == CandidateStatus.NEEDS_REVIEW
    assert after.extraction_notes.startswith(main.MOCK_MODE_NOTE)
    assert (processed / path.name).exists()
    client.assert_not_called()
    extractor.assert_not_called()


def test_table_resume_reaches_database_and_export_without_live_extraction(
    offline_ingest, monkeypatch
):
    incoming, processed, failed, db_path, output, extractor, client = offline_ingest
    monkeypatch.setattr(main, "EXTRACTION_MODE", "mock")
    document = Document()
    table = document.add_table(rows=4, cols=1)
    for row, text in zip(table.rows, ["Jane Doe", "jane@example.com", "Skills", "Python, SQL"]):
        row.cells[0].text = text
    table_path = incoming / "a-table.docx"
    document.save(table_path)
    table_hash = resume_loader.hash_file(table_path)
    # A malformed file and a normal resume in the same batch must still follow
    # their existing failed/processed paths; no network client may be created.
    (incoming / "b-corrupt.docx").write_bytes(b"not a DOCX package")
    normal_path, _ = _resume(incoming, "c-normal.docx")

    main.run_ingest()

    candidate = db.get_candidate(table_hash, db_path)
    assert candidate is not None
    assert candidate.full_name == "Jane Doe"
    assert candidate.email == "jane@example.com"
    assert candidate.skills == ["Python", "SQL"]
    assert candidate.status == CandidateStatus.NEEDS_REVIEW
    assert len(db.get_all_candidates(db_path)) == 2
    assert (processed / table_path.name).exists()
    assert (processed / normal_path.name).exists()
    assert (failed / "b-corrupt.docx").exists()
    assert not (failed / table_path.name).exists()

    workbook = openpyxl.load_workbook(output)
    try:
        rows = list(workbook.active.values)
        headers = rows[0]
        table_row = next(row for row in rows[1:] if row[headers.index("Source File")] == table_path.name)
        assert table_row[headers.index("Email")] == "jane@example.com"
        assert table_row[headers.index("Skills")] == "Python, SQL"
        assert table_row[headers.index("Status")] == "needs_review"
    finally:
        workbook.close()
    client.assert_not_called()
    extractor.assert_not_called()
