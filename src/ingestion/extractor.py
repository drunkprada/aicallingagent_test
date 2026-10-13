import logging

import openai
from pydantic import ValidationError

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
    """Raised when the model fails to produce a valid structured extraction."""


def extract_candidate(resume_text: str, client: openai.OpenAI) -> ResumeExtraction:
    try:
        completion = client.chat.completions.parse(
            model=EXTRACTION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(resume_text=resume_text),
                }
            ],
            response_format=ResumeExtraction,
        )
    except openai.LengthFinishReasonError as exc:
        raise ExtractionError("OpenAI extraction was truncated by the response length limit") from exc
    except openai.ContentFilterFinishReasonError as exc:
        raise ExtractionError("OpenAI refused to process this resume (content filter)") from exc
    except ValidationError as exc:
        raise ExtractionError("OpenAI returned invalid structured candidate fields") from exc
    except openai.APIError as exc:
        raise ExtractionError(f"OpenAI API error during extraction: {exc}") from exc

    if not completion.choices:
        raise ExtractionError("OpenAI returned no extraction choices")

    choice = completion.choices[0]
    if choice.finish_reason == "content_filter":
        raise ExtractionError("OpenAI refused to process this resume (content filter)")

    parsed = choice.message.parsed
    if parsed is None:
        raise ExtractionError("OpenAI did not return a structured extraction")

    return parsed
