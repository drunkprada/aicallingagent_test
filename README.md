# AI Resume Screening & Calling Agent

Phase 1: resume ingestion, OpenAI-based structured extraction, SQLite storage, and an Excel export for HR.
Phase 2 (outbound AI calling): the ElevenLabs text-to-speech leg is implemented (`src/calling/tts_agent.py`); Twilio dialing/streaming and speech-to-text are not yet — see `src/calling/call_agent.py`'s docstring for the design.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # then fill in OPENAI_API_KEY and (for Phase 2 TTS) ELEVENLABS_API_KEY
```

## Usage

### Dry run (single resume, no DB, no side effects)

To check the API key and extraction prompt against one resume without
touching the database, `data/incoming_resumes/`, or the Excel export:

```bash
python -m src.dry_run path/to/resume.pdf
```

This prints the extracted fields as JSON and exits.

### Full pipeline

1. Drop resume files (`.pdf` or `.docx`) into `data/incoming_resumes/`.
2. Run the ingest pipeline:

   ```bash
   python -m src.main ingest
   ```

   This parses each resume, extracts structured fields via OpenAI, stores the
   result in `data/app.db` (SQLite — the source of truth), moves the file to
   `data/processed/` (or `data/processed/failed/` if parsing/extraction
   failed), and regenerates `data/exports/candidates.xlsx`.

3. To regenerate the Excel export without re-ingesting anything:

   ```bash
   python -m src.main export
   ```

Candidate text is exported as literal text, including values beginning with
`=` and strings such as `#N/A`; it is never treated as an Excel formula or
error. Characters that cannot be represented in worksheet XML are replaced
with `�` in the export only. SQLite retains the original values.

Export refreshes are staged in a temporary file and replace `candidates.xlsx`
only after saving succeeds. A failed save or locked destination keeps the
previous spreadsheet intact and reports the error. Close the workbook or fix
the filesystem problem, then run `export` again; stored candidates do not need
to be re-ingested.

Successfully extracted resumes are deduplicated by content hash, including
records flagged `needs_review` for missing fields or mock extraction.

If extraction fails, the candidate is marked `extraction_failed` in SQLite and
the Excel export, and the resume is moved to `data/processed/failed/`. API
errors, truncated or filtered responses, invalid structured fields, and empty
responses follow this path so the rest of the batch can continue.

After resolving the cause, move the failed resume back to
`data/incoming_resumes/` and run `ingest` again. Extraction is retried in the
same candidate record, preserving its original creation time and existing call
answers/history. Older `needs_review` records with an `extraction error:` note
are also recognised as retryable failures; other reviewed records remain
deduplicated. Failed files are not retried automatically while they remain in
the failed folder. Mock-mode retries still require manual review.

### TTS dry run (Phase 2, no phone call)

To check the ElevenLabs API key and voice against a line of text, saving the
result as a local audio file (no Twilio, no dialing):

```bash
python -m src.calling.tts_dry_run "Hello, this is a test call" out.mp3
```

`CallAgent.place_call()` already synthesizes the call disclosure and every
question in `src/calling/questions.py` to audio this way before failing with
`NotImplementedError`, since there's no Twilio integration yet to send that
audio through.

## Tests

```bash
pytest
```

## Project layout

See the code comments in `src/calling/call_agent.py` for the Phase 2 plan
(Twilio outbound calling), `src/calling/tts_agent.py` for the ElevenLabs
text-to-speech wrapper, and `src/calling/questions.py` for the configurable
question set and call disclosure it will speak to candidates.
