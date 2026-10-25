from enum import Enum
from math import isfinite
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CandidateStatus(str, Enum):
    EXTRACTED = "extracted"
    EXTRACTION_FAILED = "extraction_failed"
    NEEDS_REVIEW = "needs_review"
    CALL_PENDING = "call_pending"
    CALL_COMPLETED = "call_completed"
    CALL_FAILED = "call_failed"


class ResumeExtraction(BaseModel):
    """Validated fields extracted directly from resume text."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    education: Optional[str] = None
    location: Optional[str] = None
    current_salary: Optional[str] = None

    @field_validator(
        "full_name", "email", "phone", "current_title", "education", "location",
        "current_salary",
    )
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        return (value.strip() or None) if value is not None else None

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, values: List[str]) -> List[str]:
        return [skill.strip() for skill in values if skill.strip()]

    @field_validator("years_experience")
    @classmethod
    def validate_experience(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (not isfinite(value) or value < 0):
            raise ValueError("years_experience must be finite and non-negative")
        return value


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
