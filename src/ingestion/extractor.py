import logging

import anthropic

from src.config import EXTRACTION_MODEL
from src.models.schema import ResumeExtraction

logger = logging.getLogger("resume_agent")

EXTRACTION_PROMPT = (
    "Extract structured candidate information from the resume text below. "
    "Only use information explicitly present in the text -- if a field isn't "
    "stated, leave it null (or an empty list for skills). Do not guess or "
    "infer values that aren't written in the resume.\n\n"
    "RESUME TEXT:\n{resume_text}"
)


class ExtractionError(Exception):
    """Raised when Claude fails to produce a valid structured extraction."""


def extract_candidate(resume_text: str, client: anthropic.Anthropic) -> ResumeExtraction:
    try:
        response = client.messages.parse(
            model=EXTRACTION_MODEL,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(resume_text=resume_text),
                }
            ],
            output_format=ResumeExtraction,
        )
    except anthropic.APIError as exc:
        raise ExtractionError(f"Claude API error during extraction: {exc}") from exc

    if response.stop_reason == "refusal":
        raise ExtractionError("Claude refused to process this resume")

    parsed = response.parsed_output
    if parsed is None:
        raise ExtractionError("Claude did not return a structured extraction")

    return parsed
