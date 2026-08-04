"""Configurable question set for the Phase 2 outbound calling agent.

Kept as data (not hardcoded prompt strings) so the question set can be
edited without touching the dialogue-manager code that will consume it.
Each entry maps directly to a Candidate field name in src/models/schema.py.
"""

# Compliance: must be spoken at the very start of every call, before any
# question is asked. See call_agent.py module docstring.
CALL_DISCLOSURE = (
    "Hi, this is an AI assistant calling on behalf of the hiring team. "
    "This call is being recorded. If you'd like to opt out of future calls, "
    "just let me know at any point."
)

REQUIRED_CALL_QUESTIONS = [
    {
        "field": "salary_expectation",
        "question": "What is your expected salary or compensation range for this role?",
    },
    {
        "field": "nationality",
        "question": "What is your nationality, and are you legally authorized to work in this country?",
    },
    {
        "field": "notice_period",
        "question": "What is your current notice period, or when would you be available to start?",
    },
]
