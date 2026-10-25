import pytest
from pydantic import ValidationError

from src.models.schema import ResumeExtraction


def test_blank_extraction_text_is_missing_and_empty_skills_are_removed():
    extraction = ResumeExtraction(
        full_name=" \t", email="\n", phone=" ",
        current_title=" ", education="\t", location="\n", current_salary=" ",
        skills=["", " ", " Python ", "C++", "  Data analysis  "],
    )
    for field in ("full_name", "email", "phone", "current_title", "education",
                  "location", "current_salary"):
        assert getattr(extraction, field) is None
    assert extraction.skills == ["Python", "C++", "Data analysis"]


def test_normalization_preserves_unicode_and_meaningful_text():
    extraction = ResumeExtraction(
        full_name="  Zoë 李  ", email="  zoe@example.com ", phone=" +44 (0)20 1234 5678 ",
        education="  University A\nUniversity B  ",
        skills=["C/C++", ".NET", "機械学習"],
        years_experience=0,
    )
    assert extraction.full_name == "Zoë 李"
    assert extraction.email == "zoe@example.com"
    assert extraction.phone == "+44 (0)20 1234 5678"
    assert extraction.education == "University A\nUniversity B"
    assert extraction.skills == ["C/C++", ".NET", "機械学習"]
    assert extraction.years_experience == 0
    assert ResumeExtraction(years_experience=2.5).years_experience == 2.5
    assert ResumeExtraction().years_experience is None


@pytest.mark.parametrize("years", [-0.5, float("nan"), float("inf"), -float("inf")])
def test_invalid_experience_is_rejected(years):
    with pytest.raises(ValidationError, match="finite and non-negative"):
        ResumeExtraction(years_experience=years)
