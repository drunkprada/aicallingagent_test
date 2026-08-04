from src.ingestion.mock_extractor import extract_candidate_mock

SAMPLE_RESUME = """Jane Doe
jane.doe@example.com
(415) 555-0134

5 years of experience as a backend engineer.

SKILLS
Python, PostgreSQL, Docker
Kubernetes

EDUCATION
B.S. Computer Science, State University, 2018
"""


def test_extract_candidate_mock_pulls_expected_fields():
    result = extract_candidate_mock(SAMPLE_RESUME)

    assert result.full_name == "Jane Doe"
    assert result.email == "jane.doe@example.com"
    assert result.phone is not None
    assert result.years_experience == 5.0
    assert "Python" in result.skills
    assert "Docker" in result.skills
    assert result.education is not None
    assert "State University" in result.education


def test_extract_candidate_mock_handles_sparse_text():
    result = extract_candidate_mock("Not much here, no contact info.")
    assert result.email is None
    assert result.phone is None
    assert result.skills == []
