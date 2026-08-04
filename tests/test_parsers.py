from pathlib import Path

import pytest
from docx import Document

from src.ingestion.parsers import ParserError, extract_text, extract_text_from_docx, extract_text_from_pdf


def test_extract_text_from_docx_real_file(tmp_path: Path):
    doc = Document()
    doc.add_paragraph("Jane Doe")
    doc.add_paragraph("Software Engineer, 5 years experience")
    path = tmp_path / "resume.docx"
    doc.save(path)

    text = extract_text_from_docx(path)
    assert "Jane Doe" in text
    assert "Software Engineer" in text


def test_extract_text_from_empty_docx_raises(tmp_path: Path):
    doc = Document()
    path = tmp_path / "empty.docx"
    doc.save(path)

    with pytest.raises(ParserError):
        extract_text_from_docx(path)


def test_extract_text_from_pdf_uses_pdfplumber(tmp_path: Path, monkeypatch):
    class FakePage:
        def extract_text(self):
            return "John Smith\nData Analyst"

    class FakePdf:
        pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_open(path):
        return FakePdf()

    monkeypatch.setattr("src.ingestion.parsers.pdfplumber.open", fake_open)

    path = tmp_path / "resume.pdf"
    path.write_bytes(b"%PDF-1.4 fake")
    text = extract_text_from_pdf(path)
    assert "John Smith" in text


def test_extract_text_unsupported_extension(tmp_path: Path):
    path = tmp_path / "resume.txt"
    path.write_text("hello")
    with pytest.raises(ParserError):
        extract_text(path)
