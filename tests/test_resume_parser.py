import pytest
from app.services.resume_parser import (
    clean_text,
    extract_email,
    extract_phone,
    extract_skills,
    extract_experience_years,
    extract_education,
    parse_resume,
)


class TestCleanText:
    def test_removes_blank_lines(self):
        raw = "Line one\n\n\nLine two\n   \nLine three"
        result = clean_text(raw)
        assert result == "Line one\nLine two\nLine three"

    def test_strips_whitespace_from_lines(self):
        raw = "   Hello   \n   World   "
        result = clean_text(raw)
        assert result == "Hello\nWorld"


class TestExtractEmail:
    def test_finds_standard_email(self):
        text = "Contact me at priya.sharma@email.com for more details"
        assert extract_email(text) == "priya.sharma@email.com"

    def test_finds_email_with_plus_and_dots(self):
        text = "Reach out: john.doe+work@company.co.in"
        assert extract_email(text) == "john.doe+work@company.co.in"

    def test_returns_none_when_no_email(self):
        text = "No contact information provided here"
        assert extract_email(text) is None


class TestExtractPhone:
    def test_finds_indian_format_with_country_code(self):
        text = "Contact: +91 98765 43210 for interview"
        result = extract_phone(text)
        assert result is not None
        assert "98765" in result
        assert "43210" in result

    def test_finds_phone_without_country_code(self):
        text = "Phone: 9876543210"
        result = extract_phone(text)
        assert result is not None

    def test_finds_phone_with_dashes(self):
        text = "Call at 987-654-3210"
        result = extract_phone(text)
        assert result is not None

    def test_returns_none_when_no_phone(self):
        text = "No phone number mentioned anywhere in this text"
        assert extract_phone(text) is None


class TestExtractSkills:
    def test_finds_exact_skill_matches(self):
        text = "Experienced in Python, Django, and SQL development"
        skills = extract_skills(text)
        assert "python" in skills
        assert "django" in skills
        assert "sql" in skills

    def test_does_not_false_match_substring_inside_word(self):
        """Regression test: 'go' should NOT match inside 'Django'."""
        text = "Backend developer with Django experience"
        skills = extract_skills(text)
        assert "go" not in skills
        assert "django" in skills

    def test_handles_special_characters_in_skill_names(self):
        text = "Proficient in C++ and C# programming"
        skills = extract_skills(text)
        assert "c++" in skills
        assert "c#" in skills

    def test_case_insensitive_matching(self):
        text = "Skilled in PYTHON and Django"
        skills = extract_skills(text)
        assert "python" in skills

    def test_no_skills_found_returns_empty_list(self):
        text = "This resume mentions cooking, painting, and gardening"
        skills = extract_skills(text)
        assert skills == []

    def test_returns_sorted_unique_list(self):
        text = "Python python PYTHON Django"
        skills = extract_skills(text)
        assert skills.count("python") == 1  # no duplicates


class TestExtractExperienceYears:
    def test_finds_years_of_experience_pattern(self):
        text = "I have 3 years of experience in backend development"
        assert extract_experience_years(text) == 3.0

    def test_finds_decimal_years(self):
        text = "2.5 years of experience building APIs"
        assert extract_experience_years(text) == 2.5

    def test_finds_yrs_abbreviation(self):
        text = "5+ yrs experience in Python"
        assert extract_experience_years(text) == 5.0

    def test_returns_none_when_not_mentioned(self):
        text = "Skilled Python developer with strong fundamentals"
        assert extract_experience_years(text) is None


class TestExtractEducation:
    def test_finds_full_btech_line_no_truncation(self):
        """Regression test: education should not be cut off mid-word at 40 chars."""
        text = "Education\nB.Tech in Computer Science, Rajasthan Technical University, 2022"
        result = extract_education(text)
        assert result is not None
        assert "Rajasthan Technical University" in result
        assert "2022" in result

    def test_finds_bachelor_degree(self):
        text = "Bachelor of Science in Computer Engineering"
        result = extract_education(text)
        assert "Bachelor" in result

    def test_finds_masters_degree(self):
        text = "Master of Technology in Data Science"
        result = extract_education(text)
        assert "Master" in result

    def test_returns_none_when_no_education_mentioned(self):
        text = "Experienced professional with strong leadership skills"
        assert extract_education(text) is None


class TestParseResume:
    def test_returns_all_expected_keys(self):
        text = (
            "Priya Sharma\n"
            "priya.sharma@email.com | +91 98765 43210\n"
            "B.Tech in Computer Science, 2022\n"
            "Skills: Python, Django, SQL\n"
            "3 years of experience"
        )
        result = parse_resume(text)
        expected_keys = {
            "candidate_name", "candidate_email", "candidate_phone",
            "skills", "education", "experience_years",
        }
        assert expected_keys.issubset(result.keys())

    def test_extracts_email_and_skills_together(self):
        text = "test@example.com\nSkills: Python, FastAPI"
        result = parse_resume(text)
        assert result["candidate_email"] == "test@example.com"
        assert "python" in result["skills"]

