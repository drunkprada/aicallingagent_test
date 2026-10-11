from unittest.mock import MagicMock

import pytest

from src import main


def test_invalid_extraction_mode_fails_before_side_effects(monkeypatch):
    ensure_directories = MagicMock()
    init_db = MagicMock()
    openai_client = MagicMock()

    monkeypatch.setattr(main, "EXTRACTION_MODE", "typo")
    monkeypatch.setattr(main, "ensure_directories", ensure_directories)
    monkeypatch.setattr(main, "init_db", init_db)
    monkeypatch.setattr(main.openai, "OpenAI", openai_client)

    with pytest.raises(
        ValueError,
        match="Invalid EXTRACTION_MODE.*'openai' or 'mock'.*'typo'",
    ):
        main.run_ingest()

    ensure_directories.assert_not_called()
    init_db.assert_not_called()
    openai_client.assert_not_called()
