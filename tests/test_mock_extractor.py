import pytest

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


@pytest.mark.parametrize("heading", ["Skills", " TECHNICAL SKILLS: ", "Core Competencies"])
def test_skills_require_a_whole_heading_and_keep_the_complete_section(heading):
    text = f"""Jane Doe
jane@example.com
Skills developed while mentoring colleagues
Not a skill section
My technical skills include Python
Also not a skill section
{heading}
Python
SQL
Docker
Git
Linux
React
TypeScript
Projects
Built a recruitment portal
"""
    assert extract_candidate_mock(text).skills == [
        "Python", "SQL", "Docker", "Git", "Linux", "React", "TypeScript",
    ]


@pytest.mark.parametrize("heading", [
    "Experience", "Work Experience:", "Professional Experience", "Projects", "Certifications",
])
def test_sections_stop_before_unrelated_resume_content(heading):
    text = f"""Jane Doe
jane@example.com
Skills
Python, SQL
{heading}
Unrelated work or qualifications
Education
BSc Computer Science
{heading}
More unrelated details
"""
    result = extract_candidate_mock(text)
    assert result.skills == ["Python", "SQL"]
    assert result.education == "BSc Computer Science"


def test_skill_bullets_preserve_hyphenated_names():
    result = extract_candidate_mock("""Jane Doe
Skills
- scikit-learn, CI/CD
• problem-solving; Python
- Cross-platform development

Education
Example University
""")
    assert result.skills == [
        "scikit-learn", "CI/CD", "problem-solving", "Python", "Cross-platform development",
    ]


def test_empty_section_does_not_consume_the_next_heading():
    result = extract_candidate_mock("Skills\n\nProjects\nExample project\nEducation\n\nExperience\nEngineer")
    assert result.skills == []
    assert result.education is None
