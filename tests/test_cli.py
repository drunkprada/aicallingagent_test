import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cli(tmp_path):
    # Exercise the real entry point without touching the checkout's data.
    shutil.copytree(Path(__file__).resolve().parents[1] / "src", tmp_path / "src")

    def run(*args, mode="mock"):
        return subprocess.run(
            [sys.executable, *args], cwd=tmp_path,
            env={**os.environ, "EXTRACTION_MODE": mode},
            capture_output=True, text=True, timeout=20,
        )

    return run


@pytest.mark.parametrize("args, code", [
    (("-c", "import src.main"), 0),
    (("-m", "src.main", "--help"), 0),
    (("-m", "src.main", "ingest", "--help"), 0),
    (("-m", "src.main", "unknown"), 2),
])
def test_cli_inspection_does_not_need_writable_output_paths(cli, tmp_path, args, code):
    for name in ("data", "logs"):
        (tmp_path / name).write_text("unavailable directory")
    result = cli(*args)
    assert result.returncode == code, result.stderr
    if "--help" in args:
        assert "usage:" in result.stdout
    assert "Traceback" not in result.stderr


def test_invalid_ingest_mode_creates_no_files(cli, tmp_path):
    result = cli("-m", "src.main", "ingest", mode="typo")
    assert result.returncode == 2
    assert "Invalid EXTRACTION_MODE" in result.stderr
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "logs").exists()


@pytest.mark.parametrize("command", ["ingest", "export"])
def test_working_commands_still_create_export_and_log(cli, tmp_path, command):
    result = cli("-m", "src.main", command)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "data/exports/candidates.xlsx").is_file()
    assert "Excel export refreshed" in (tmp_path / "logs/app.log").read_text()
