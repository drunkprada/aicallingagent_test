from pathlib import Path

from src.models.schema import Candidate, CandidateStatus
from src.storage.db import candidate_exists, get_all_candidates, get_candidate, init_db, upsert_candidate


def test_upsert_and_dedupe(tmp_path: Path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    candidate = Candidate(
        resume_hash="abc123",
        source_filename="resume.pdf",
        status=CandidateStatus.EXTRACTED,
        full_name="Jane Doe",
        email="jane@example.com",
        skills=["Python", "SQL"],
    )

    assert not candidate_exists("abc123", db_path)
    upsert_candidate(candidate, db_path)
    assert candidate_exists("abc123", db_path)

    fetched = get_candidate("abc123", db_path)
    assert fetched is not None
    assert fetched.full_name == "Jane Doe"
    assert fetched.skills == ["Python", "SQL"]

    # Re-inserting the same hash updates in place rather than duplicating.
    candidate.status = CandidateStatus.CALL_COMPLETED
    upsert_candidate(candidate, db_path)

    all_candidates = get_all_candidates(db_path)
    assert len(all_candidates) == 1
    assert all_candidates[0].status == CandidateStatus.CALL_COMPLETED
