"""Configurable question set for the Phase 2 outbound calling agent.

Kept as data (not hardcoded prompt strings) so the question set can be
edited without touching the dialogue-manager code that will consume it.
Each entry maps directly to a Candidate field name in src/models/schema.py.
"""

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
