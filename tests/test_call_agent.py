from unittest.mock import MagicMock

import pytest

from src.calling.call_agent import CallAgent
from src.calling.questions import CALL_DISCLOSURE, REQUIRED_CALL_QUESTIONS
from src.models.schema import Candidate


def test_place_call_fails_before_constructing_tts_or_contacting_services(monkeypatch):
    tts_factory = MagicMock(side_effect=AssertionError("TTS client must not be created"))
    monkeypatch.setattr("src.calling.call_agent.TTSAgent", tts_factory)
    candidate = Candidate(resume_hash="abc", source_filename="resume.pdf")

    with pytest.raises(NotImplementedError, match="Outbound calling is disabled"):
        CallAgent().place_call(candidate)

    tts_factory.assert_not_called()


def test_prompt_synthesis_remains_available_as_an_explicit_operation():
    tts = MagicMock()
    tts.synthesize.side_effect = lambda text: ("audio:" + text).encode()
    agent = CallAgent(tts)

    audio = agent._synthesize_prompts()

    expected_prompts = {
        "disclosure": CALL_DISCLOSURE,
        **{question["field"]: question["question"] for question in REQUIRED_CALL_QUESTIONS},
    }
    assert audio == {
        field: ("audio:" + prompt).encode()
        for field, prompt in expected_prompts.items()
    }
    assert [call.args[0] for call in tts.synthesize.call_args_list] == list(
        expected_prompts.values()
    )
