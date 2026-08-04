"""Phase 2 interface: not implemented yet.

Design (to be built once Twilio + telephony credentials are available):

  Twilio Programmable Voice places the call and opens a <Stream> to a
  WebSocket server this app runs. Audio flows: caller -> Twilio -> our
  WebSocket -> speech-to-text -> Claude (dialogue state machine over the
  REQUIRED_CALL_QUESTIONS in questions.py) -> text-to-speech -> Twilio ->
  caller. After the call ends, the full transcript is re-run through Claude
  with a structured-extraction prompt (same pattern as
  src/ingestion/extractor.py) to produce a CallResult, which main.py then
  merges into the candidate's row via src/storage/db.py.

  Compliance requirements this must enforce before it can place real calls:
    - Recorded-call / AI-assistant disclosure at the very start of the call.
    - Opt-out handling (candidate can ask to stop being called).
    - Business-hours-only dialing window (configurable per region).
    - A capped number of call attempts per candidate, with the candidate
      flagged for human follow-up after the cap is hit instead of retried
      indefinitely.
    - A dry-run mode that simulates the full flow (including transcript
      extraction) without dialing a real number, for safe testing.

  place_call() is the only entry point main.py will call in Phase 2.
"""

from src.models.schema import Candidate, CallResult


class CallAgent:
    def place_call(self, candidate: Candidate) -> CallResult:
        raise NotImplementedError(
            "Outbound calling is not implemented yet (Phase 2). "
            "See the module docstring for the planned design."
        )
