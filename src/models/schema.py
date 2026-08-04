from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CandidateStatus(str, Enum):
    EXTRACTED = "extracted"
    NEEDS_REVIEW = "needs_review"
    CALL_PENDING = "call_pending"
    CALL_COMPLETED = "call_completed"
    CALL_FAILED = "call_failed"


class ResumeExtraction(BaseModel):
    """Structured fields Claude extracts directly from resume text."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    education: Optional[str] = None
    location: Optional[str] = None
    current_salary: Optional[str] = None


class Candidate(BaseModel):
    """Full candidate record as stored in the database / exported to Excel."""

    resume_hash: str
    source_filename: str
    status: CandidateStatus = CandidateStatus.EXTRACTED
    extraction_notes: Optional[str] = None

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    education: Optional[str] = None
    location: Optional[str] = None
    current_salary: Optional[str] = None

    # Populated in Phase 2 by the calling agent.
    salary_expectation: Optional[str] = None
    nationality: Optional[str] = None
    notice_period: Optional[str] = None
    call_status: Optional[str] = None
    call_attempts: int = 0
    last_call_at: Optional[str] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CallResult(BaseModel):
    """Phase 2: outcome of a single outbound call attempt, before merging
    the collected answers back into a Candidate record."""

    resume_hash: str
    success: bool
    salary_expectation: Optional[str] = None
    nationality: Optional[str] = None
    notice_period: Optional[str] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    failure_reason: Optional[str] = None
    attempted_at: Optional[str] = None
