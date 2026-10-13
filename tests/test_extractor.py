from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
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


@pytest.mark.parametrize("case", ["length", "content_filter", "invalid_fields", "empty_choices"])
def test_sdk_parse_failures_become_extraction_errors(case):
    response = {
        "id": "offline-completion", "object": "chat.completion", "created": 0,
        "model": "gpt-4o",
        "choices": [{
            "index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": '{"full_name":"Jane Doe"}'},
        }],
    }
    if case in {"length", "content_filter"}:
        response["choices"][0]["finish_reason"] = case
    elif case == "invalid_fields":
        response["choices"][0]["message"]["content"] = '{"years_experience":"not a number"}'
    else:
        response["choices"] = []

    requests = []

    def handle_request(request):
        requests.append(request)
        return httpx.Response(200, json=response)

    with httpx.Client(transport=httpx.MockTransport(handle_request)) as http_client:
        client = openai.OpenAI(api_key="offline-test-key", http_client=http_client)
        with pytest.raises(ExtractionError):
            extract_candidate("some resume text", client)

    assert len(requests) == 1
