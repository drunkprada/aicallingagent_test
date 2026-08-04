"""Phase 2 interface: dialing is not implemented yet. Text-to-speech is.

Design (dialing to be built once Twilio + telephony credentials are
available):

  Twilio Programmable Voice places the call and opens a <Stream> to a
  WebSocket server this app runs. Audio flows: caller -> Twilio -> our
  WebSocket -> speech-to-text -> OpenAI (dialogue state machine over the
  REQUIRED_CALL_QUESTIONS in questions.py) -> ElevenLabs text-to-speech
  (tts_agent.py) -> Twilio -> caller. After the call ends, the full
  transcript is re-run through OpenAI with a structured-extraction prompt
  (same pattern as src/ingestion/extractor.py) to produce a CallResult,
  which main.py then merges into the candidate's row via
  src/storage/db.py.

  The text-to-speech leg is already wired up below via TTSAgent -- see
  tts_agent.py and tts_dry_run.py to exercise it without a phone call.
  Speech-to-text and the Twilio dial/stream integration are still missing.

  Compliance requirements this must enforce before it can place real calls:
    - Recorded-call / AI-assistant disclosure at the very start of the call
      (CALL_DISCLOSURE in questions.py, already synthesized below).
    - Opt-out handling (candidate can ask to stop being called).
    - Business-hours-only dialing window (configurable per region).
    - A capped number of call attempts per candidate, with the candidate
      flagged for human follow-up after the cap is hit instead of retried
      indefinitely.
    - A dry-run mode that simulates the full flow (including transcript
      extraction) without dialing a real number, for safe testing.

  place_call() is the only entry point main.py will call in Phase 2.
"""

from typing import Dict, Optional

from src.calling.questions import CALL_DISCLOSURE, REQUIRED_CALL_QUESTIONS
from src.calling.tts_agent import TTSAgent, TTSError
from src.models.schema import Candidate, CallResult


class CallAgent:
    def __init__(self, tts: Optional[TTSAgent] = None):
        self.tts = tts or TTSAgent()

    def _synthesize_prompts(self) -> Dict[str, bytes]:
        """Synthesize the disclosure line and every required question into
        audio via ElevenLabs. Exercised independently of Twilio so the TTS
        leg of the pipeline works before dialing is wired up."""
        prompts = {"disclosure": CALL_DISCLOSURE}
        prompts.update({q["field"]: q["question"] for q in REQUIRED_CALL_QUESTIONS})
        return {field: self.tts.synthesize(text) for field, text in prompts.items()}

    def place_call(self, candidate: Candidate) -> CallResult:
        try:
            self._synthesize_prompts()
        except TTSError as exc:
            raise NotImplementedError(
                "Outbound calling is not implemented yet (Phase 2), and TTS "
                f"synthesis failed before reaching that point: {exc}"
            ) from exc

        raise NotImplementedError(
            "Outbound calling is not implemented yet (Phase 2): call prompts "
            "were synthesized to audio successfully, but there is no Twilio "
            "dial/stream integration to send them through yet. "
            "See the module docstring for the planned design."
        )
