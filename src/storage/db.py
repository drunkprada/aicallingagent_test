import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List, Optional

from src.config import DB_PATH
from src.models.schema import Candidate, CandidateStatus

SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    resume_hash TEXT PRIMARY KEY,
    source_filename TEXT NOT NULL,
    status TEXT NOT NULL,
    extraction_notes TEXT,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    current_title TEXT,
    years_experience REAL,
    skills TEXT NOT NULL DEFAULT '[]',
    education TEXT,
    location TEXT,
    current_salary TEXT,
    salary_expectation TEXT,
    nationality TEXT,
    notice_period TEXT,
    call_status TEXT,
    call_attempts INTEGER NOT NULL DEFAULT 0,
    last_call_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(SCHEMA)


def candidate_exists(resume_hash: str, db_path: Path = DB_PATH) -> bool:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM candidates WHERE resume_hash = ?", (resume_hash,)
        ).fetchone()
        return row is not None


def upsert_candidate(candidate: Candidate, db_path: Path = DB_PATH) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO candidates (
                resume_hash, source_filename, status, extraction_notes,
                full_name, email, phone, current_title, years_experience,
                skills, education, location, current_salary,
                salary_expectation, nationality, notice_period,
                call_status, call_attempts, last_call_at,
                created_at, updated_at
            ) VALUES (
                :resume_hash, :source_filename, :status, :extraction_notes,
                :full_name, :email, :phone, :current_title, :years_experience,
                :skills, :education, :location, :current_salary,
                :salary_expectation, :nationality, :notice_period,
                :call_status, :call_attempts, :last_call_at,
                :created_at, :updated_at
            )
            ON CONFLICT(resume_hash) DO UPDATE SET
                source_filename=excluded.source_filename,
                status=excluded.status,
                extraction_notes=excluded.extraction_notes,
                full_name=excluded.full_name,
                email=excluded.email,
                phone=excluded.phone,
                current_title=excluded.current_title,
                years_experience=excluded.years_experience,
                skills=excluded.skills,
                education=excluded.education,
                location=excluded.location,
                current_salary=excluded.current_salary,
                salary_expectation=excluded.salary_expectation,
                nationality=excluded.nationality,
                notice_period=excluded.notice_period,
                call_status=excluded.call_status,
                call_attempts=excluded.call_attempts,
                last_call_at=excluded.last_call_at,
                updated_at=excluded.updated_at
            """,
            {
                "resume_hash": candidate.resume_hash,
                "source_filename": candidate.source_filename,
                "status": candidate.status.value,
                "extraction_notes": candidate.extraction_notes,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "current_title": candidate.current_title,
                "years_experience": candidate.years_experience,
                "skills": json.dumps(candidate.skills),
                "education": candidate.education,
                "location": candidate.location,
                "current_salary": candidate.current_salary,
                "salary_expectation": candidate.salary_expectation,
                "nationality": candidate.nationality,
                "notice_period": candidate.notice_period,
                "call_status": candidate.call_status,
                "call_attempts": candidate.call_attempts,
                "last_call_at": candidate.last_call_at,
                "created_at": candidate.created_at or now,
                "updated_at": now,
            },
        )


def _row_to_candidate(row: sqlite3.Row) -> Candidate:
    data = dict(row)
    data["skills"] = json.loads(data["skills"] or "[]")
    data["status"] = CandidateStatus(data["status"])
    return Candidate(**data)


def get_all_candidates(db_path: Path = DB_PATH) -> List[Candidate]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM candidates ORDER BY created_at ASC"
        ).fetchall()
        return [_row_to_candidate(row) for row in rows]


def get_candidate(resume_hash: str, db_path: Path = DB_PATH) -> Optional[Candidate]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM candidates WHERE resume_hash = ?", (resume_hash,)
        ).fetchone()
        return _row_to_candidate(row) if row else None
