from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic
import pytest

from src.ingestion.extractor import ExtractionError, extract_candidate
from src.models.schema import ResumeExtraction


def _fake_client(parsed_output=None, stop_reason="end_turn", raise_api_error=False):
    client = MagicMock()
    if raise_api_error:
        client.messages.parse.side_effect = anthropic.APIError(
            message="boom", request=MagicMock(), body=None
        )
    else:
        client.messages.parse.return_value = SimpleNamespace(
            stop_reason=stop_reason, parsed_output=parsed_output
        )
    return clientsusuu


def test_extract_candidate_success():
    expected = ResumeExtraction(full_name="Jane Doe", email="jane@example.com", skills=["Python"])
    client = _fake_client(parsed_output=expected)

    result = extract_candidate("some resume text", client)

    assert result.full_name == "Jane Doe"
    assert result.skills == ["Python"]


def test_extract_candidate_refusal_raises():
    client = _fake_client(parsed_output=None, stop_reason="refusal")
    with pytest.raises(ExtractionError):
        extract_candidate("some resume text", client)


def test_extract_candidate_malformed_output_raises():
    # parsed_output is None even though stop_reason looks normal -- simulates
    # a response the SDK couldn't validate against the schema.
    client = _fake_client(parsed_output=None, stop_reason="end_turn")
    with pytest.raises(ExtractionError):
        extract_candidate("some resume text", client)


def test_extract_candidate_api_error_raises():
    client = _fake_client(raise_api_error=True)
    with pytest.raises(ExtractionError):
        extract_candidate("some resume text", client)
