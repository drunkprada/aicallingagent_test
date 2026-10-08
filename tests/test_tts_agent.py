import json

import httpx
import pytest
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError

from src.calling.tts_agent import TTSAgent, TTSError
from src.config import AUDIO_OUTPUT_FORMAT, ELEVENLABS_MODEL, ELEVENLABS_VOICE_ID


def test_synthesize_uses_sdk_and_returns_audio_without_network():
    requests = []

    def handle_request(request):
        requests.append(request)
        return httpx.Response(200, content=b"mock audio")

    with httpx.Client(transport=httpx.MockTransport(handle_request)) as http_client:
        client = ElevenLabs(api_key="test-key", httpx_client=http_client)
        result = TTSAgent(client).synthesize("Hello")

    assert result == b"mock audio"
    assert len(requests) == 1
    request = requests[0]
    assert request.url.path == f"/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    assert request.url.params["output_format"] == AUDIO_OUTPUT_FORMAT
    body = json.loads(request.content)
    assert body["text"] == "Hello"
    assert body["model_id"] == ELEVENLABS_MODEL


def test_synthesize_wraps_api_errors_from_audio_stream():
    def handle_request(request):
        return httpx.Response(401, json={"detail": "Invalid API key"})

    with httpx.Client(transport=httpx.MockTransport(handle_request)) as http_client:
        client = ElevenLabs(api_key="test-key", httpx_client=http_client)
        with pytest.raises(TTSError, match="ElevenLabs TTS failed") as error:
            TTSAgent(client).synthesize("Hello")

    assert isinstance(error.value.__cause__, ApiError)
