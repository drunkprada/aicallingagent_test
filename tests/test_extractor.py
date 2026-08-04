from types import SimpleNamespace
from unittest.mock import MagicMock

import openai
import pytest

from src.ingestion.extractor import ExtractionError, extract_candidate
from src.models.schema import ResumeExtraction


def _fake_client(parsed_output=None, finish_reason="stop", raise_api_error=False):
    client = MagicMock()
    if raise_api_error:
        client.chat.completions.parse.side_effect = openai.APIError(
            message="boom", request=MagicMock(), body=None
        )
    else:
        choice = SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(parsed=parsed_output))
        client.chat.completions.parse.return_value = SimpleNamespace(choices=[choice])
    return client


def test_extract_candidate_success():
    expected = ResumeExtraction(full_name="Jane Doe", email="jane@example.com", skills=["Python"])
    client = _fake_client(parsed_output=expected)

    result = extract_candidate("some resume text", client)

    assert result.full_name == "Jane Doe"
    assert result.skills == ["Python"]


def test_extract_candidate_refusal_raises():
    client = _fake_client(parsed_output=None, finish_reason="content_filter")
    with pytest.raises(ExtractionError):
        extract_candidate("some resume text", client)


def test_extract_candidate_malformed_output_raises():
    # parsed_output is None even though finish_reason looks normal -- simulates
    # a response the SDK couldn't validate against the schema.
    client = _fake_client(parsed_output=None, finish_reason="stop")
    with pytest.raises(ExtractionError):
        extract_candidate("some resume text", client)


def test_extract_candidate_api_error_raises():
    client = _fake_client(raise_api_error=True)
    with pytest.raises(ExtractionError):
        extract_candidate("some resume text", client)
