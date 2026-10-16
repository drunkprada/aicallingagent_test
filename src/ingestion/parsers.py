from pathlib import Path
from typing import Iterator

import pdfplumber
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


class ParserError(Exception):
    """Raised when a resume file cannot be parsed into text."""


def extract_text_from_pdf(path: Path) -> str:
    try:
        with pdfplumber.open(path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:  # pdfplumber raises varied underlying errors
        raise ParserError(f"Failed to read PDF {path.name}: {exc}") from exc

    text = "\n".join(pages).strip()
    if not text:
        raise ParserError(f"No extractable text found in {path.name}")
    return text


def _docx_text_blocks(container) -> Iterator[str]:
    """Read body/cell paragraphs and tables in their stored document order."""
    for block in container.iter_inner_content():
        if isinstance(block, Paragraph):
            yield block.text
        elif isinstance(block, Table):
            seen_cells = set()
            for row in block.rows:
                for cell in row.cells:
                    # The layout grid repeats a merged cell at each occupied
                    # position. Deduplicate by its XML element, not its text:
                    # different cells can legitimately have identical content.
                    if cell._tc in seen_cells:
                        continue
                    seen_cells.add(cell._tc)
                    yield from _docx_text_blocks(cell)


def extract_text_from_docx(path: Path) -> str:
    try:
        document = Document(path)
        text = "\n".join(_docx_text_blocks(document)).strip()
    except Exception as exc:
        raise ParserError(f"Failed to read DOCX {path.name}: {exc}") from exc

    if not text:
        raise ParserError(f"No extractable text found in {path.name}")
    return text


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    raise ParserError(f"Unsupported file type: {suffix}")
