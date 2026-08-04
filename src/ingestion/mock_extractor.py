"""Zero-cost, regex-based stand-in for the Claude extractor.

Used when EXTRACTION_MODE=mock (no ANTHROPIC_API_KEY / no API credits
required). This is deliberately crude -- it exists only to exercise the rest
of the pipeline (parsing, storage, Excel export) for free. Every candidate it
produces is force-flagged NEEDS_REVIEW in main.py because heuristic
extraction cannot be trusted the way Claude's structured extraction can.
Swap EXTRACTION_MODE back to "claude" once API credits are available -- no
other code changes needed.
"""

import re
from typing import List, Optional

from src.models.schema import ResumeExtraction

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Whitespace class excludes \n/\r deliberately -- a plain \s here lets the
# match span across blank lines and swallow unrelated digits (e.g. "7 years").
PHONE_RE = re.compile(r"(\+?\(?\d[\d\-\.\(\)\t ]{6,}\d)")
YEARS_RE = re.compile(r"(\d+)\+?\s*(?:years|yrs)\b", re.IGNORECASE)
SECTION_HEADER_RE = re.compile(
    r"^\s*(skills|technical skills|core competencies|education)\s*:?\s*$",
    re.IGNORECASE,
)


def _find_section(lines: List[str], header_pattern: str) -> Optional[str]:
    header_re = re.compile(rf"^\s*{header_pattern}\s*:?\s*$", re.IGNORECASE)
    for idx, line in enumerate(lines):
        if header_re.match(line):
            collected = []
            for following in lines[idx + 1 : idx + 6]:
                stripped = following.strip()
                if not stripped:
                    if collected:
                        break
                    continue
                if SECTION_HEADER_RE.match(stripped):
                    break
                collected.append(stripped)
            return "\n".join(collected) if collected else None
    return None


def _guess_full_name(lines: List[str]) -> Optional[str]:
    for line in lines[:3]:
        candidate = line.strip()
        if not candidate:
            continue
        if EMAIL_RE.search(candidate) or PHONE_RE.search(candidate):
            continue
        words = candidate.split()
        if 1 < len(words) <= 5 and not any(char.isdigit() for char in candidate):
            return candidate
        return None
    return None


def extract_candidate_mock(resume_text: str) -> ResumeExtraction:
    lines = resume_text.splitlines()

    email_match = EMAIL_RE.search(resume_text)
    phone_match = PHONE_RE.search(resume_text)
    years_match = YEARS_RE.search(resume_text)

    skills_blob = _find_section(lines, "skills|technical skills|core competencies")
    skills: List[str] = []
    if skills_blob:
        for chunk in re.split(r"[,;•\-\n]", skills_blob):
            item = chunk.strip(" \t.")
            if item:
                skills.append(item)

    education = _find_section(lines, "education")

    return ResumeExtraction(
        full_name=_guess_full_name(lines),
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0).strip() if phone_match else None,
        current_title=None,
        years_experience=float(years_match.group(1)) if years_match else None,
        skills=skills,
        education=education,
        location=None,
        current_salary=None,
    )
