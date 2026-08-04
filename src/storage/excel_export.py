from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from src.config import EXCEL_EXPORT_PATH
from src.models.schema import Candidate
from src.storage.db import get_all_candidates

COLUMNS = [
    ("full_name", "Name"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("current_title", "Current Title"),
    ("years_experience", "Years Experience"),
    ("skills", "Skills"),
    ("education", "Education"),
    ("location", "Location"),
    ("current_salary", "Current Salary"),
    ("salary_expectation", "Salary Expectation"),
    ("nationality", "Nationality"),
    ("notice_period", "Notice Period"),
    ("status", "Status"),
    ("call_status", "Call Status"),
    ("call_attempts", "Call Attempts"),
    ("last_call_at", "Last Call At"),
    ("extraction_notes", "Extraction Notes"),
    ("source_filename", "Source File"),
    ("created_at", "Added On"),
]


def _cell_value(candidate: Candidate, field: str):
    value = getattr(candidate, field)
    if field == "skills":
        return ", ".join(value) if value else ""
    if field == "status":
        return value.value if value else ""
    return value if value is not None else ""


def export_candidates(output_path: Path = EXCEL_EXPORT_PATH) -> Path:
    candidates = get_all_candidates()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Candidates"

    for col_idx, (_, header) in enumerate(COLUMNS, start=1):
        cell = sheet.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)

    for row_idx, candidate in enumerate(candidates, start=2):
        for col_idx, (field, _) in enumerate(COLUMNS, start=1):
            sheet.cell(row=row_idx, column=col_idx, value=_cell_value(candidate, field))

    for col_idx, (field, header) in enumerate(COLUMNS, start=1):
        sheet.column_dimensions[get_column_letter(col_idx)].width = max(
            len(header) + 2, 14
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    return output_path
