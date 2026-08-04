from pathlib import Path

import openpyxl

from src.models.schema import Candidate, CandidateStatus
from src.storage import excel_export
from src.storage.db import init_db, upsert_candidate


def test_export_creates_expected_columns(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    monkeypatch.setattr("src.storage.excel_export.get_all_candidates", lambda: [
        Candidate(
            resume_hash="h1",
            source_filename="a.pdf",
            status=CandidateStatus.EXTRACTED,
            full_name="Alice",
            skills=["Go", "Rust"],
        )
    ])

    output_path = tmp_path / "candidates.xlsx"
    result_path = excel_export.export_candidates(output_path)

    assert result_path == output_path
    assert output_path.exists()

    workbook = openpyxl.load_workbook(output_path)
    sheet = workbook.active
    headers = [cell.value for cell in sheet[1]]
    assert "Name" in headers
    assert "Skills" in headers

    name_col = headers.index("Name") + 1
    skills_col = headers.index("Skills") + 1
    assert sheet.cell(row=2, column=name_col).value == "Alice"
    assert sheet.cell(row=2, column=skills_col).value == "Go, Rust"
