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
   DOCX extraction reads body paragraphs and table cells in document order,
   including nested tables. Merged cells are read once; separate cells with
   matching text are retained. Headers, footers, text boxes and image-only
   content are not extracted. Blank or malformed documents follow the failed
   file path rather than producing empty candidate records.
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

If an incoming file is locked, unreadable or removed after scanning, ingestion
logs the read error and continues with the remaining resumes and the export.
A file that still exists stays in the incoming folder; unlock it or restore
read permissions, then run `ingest` again. It is not archived and no candidate
record is created until its bytes can be read.

If a file cannot be moved into the processed or failed archive, ingestion logs
the destination and filesystem error, continues with the other resumes, and
refreshes the export. Any candidate already saved in SQLite remains intact.
Resolve the archive permissions or lock, then rerun `ingest` for files still in
the incoming folder. Successfully extracted records are only archived on retry;
they are not extracted again. Failed extraction records still follow the retry
rules below, so an unarchived failed resume may trigger another extraction on
the next run.

Successfully extracted resumes are deduplicated by content hash, including
records flagged `needs_review` for missing fields or mock extraction.

In OpenAI mode, the API client is opened only after a new or retryable resume
has been parsed successfully. Empty, duplicate-only and malformed-file batches
can therefore archive files and refresh the export without an API key. When
extraction is needed, missing credentials still stop the run and leave that
resume in the incoming folder for retry. One client is reused for the batch
and closed on both normal completion and processing errors.

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

`CallAgent.place_call()` fails before constructing an API client or
synthesizing audio while dialing and its required safeguards remain
unimplemented. This prevents an unfinished call attempt from spending TTS
credits or contacting an external service. Use the explicit TTS dry run above
when you intentionally want to test ElevenLabs without placing a phone call.

## Tests

```bash
python -m pytest
```

GitHub Actions runs the suite on pushes and pull requests. Tests block outbound
socket connections and use mocked API transports; no service credentials or
live calling integrations are used.

## Project layout

See the code comments in `src/calling/call_agent.py` for the Phase 2 plan
(Twilio outbound calling), `src/calling/tts_agent.py` for the ElevenLabs
text-to-speech wrapper, and `src/calling/questions.py` for the configurable
question set and call disclosure it will speak to candidates.
