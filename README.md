# AI Resume Screening & Calling Agent

Phase 1: resume ingestion, OpenAI-based structured extraction, SQLite storage, and an Excel export for HR.
Phase 2 (outbound AI calling) is scaffolded in `src/calling/` but not implemented yet — see that module's docstring for the design.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # then fill in OPENAI_API_KEY
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

Re-running `ingest` is safe — resumes are deduplicated by content hash, so
the same file is never processed twice.

## Tests

```bash
pytest
```

## Project layout

See the code comments in `src/calling/call_agent.py` for the Phase 2 plan
(Twilio outbound calling), and `src/calling/questions.py` for the
configurable question set it will ask candidates.
