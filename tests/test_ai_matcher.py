import pytest
from app.services.ai_matcher import (
    get_semantic_similarity,
    get_keyword_overlap,
    get_experience_score,
    compute_match,
)


class TestKeywordOverlap:
    def test_full_match(self):
        result = get_keyword_overlap("python, django, sql", "python, django, sql")
        assert result["score"] == 100.0
        assert set(result["matched"]) == {"python", "django", "sql"}
        assert result["missing"] == []

    def test_partial_match(self):
        result = get_keyword_overlap("python, django", "python, django, aws, docker")
        assert result["score"] == 50.0
        assert set(result["matched"]) == {"python", "django"}
        assert set(result["missing"]) == {"aws", "docker"}

    def test_no_match(self):
        result = get_keyword_overlap("java, spring", "python, django")
        assert result["score"] == 0.0
        assert result["matched"] == []

    def test_empty_required_skills(self):
        result = get_keyword_overlap("python, django", "")
        assert result["score"] == 0.0
        assert result["matched"] == []
        assert result["missing"] == []

    def test_empty_resume_skills(self):
        result = get_keyword_overlap("", "python, django")
        assert result["score"] == 0.0
        assert set(result["missing"]) == {"python", "django"}

    def test_case_insensitive(self):
        result = get_keyword_overlap("Python, Django", "python, django")
        assert result["score"] == 100.0


class TestExperienceScore:
    def test_meets_requirement_exactly(self):
        result = get_experience_score(candidate_years=3.0, required_years=3.0)
        assert result["score"] == 100.0

    def test_exceeds_requirement(self):
        result = get_experience_score(candidate_years=5.0, required_years=3.0)
        assert result["score"] == 100.0

    def test_below_requirement(self):
        result = get_experience_score(candidate_years=2.0, required_years=5.0)
        assert result["score"] == 40.0  # 2/5 * 100

    def test_no_experience_provided(self):
        result = get_experience_score(candidate_years=None, required_years=5.0)
        assert result["score"] == 0.0

    def test_no_requirement_specified(self):
        result = get_experience_score(candidate_years=1.0, required_years=None)
        assert result["score"] == 100.0

    def test_zero_requirement(self):
        result = get_experience_score(candidate_years=0.0, required_years=0)
        assert result["score"] == 100.0


class TestSemanticSimilarity:
    def test_identical_text_high_similarity(self):
        text = "Experienced Python developer with FastAPI and SQL skills"
        score = get_semantic_similarity(text, text)
        assert score > 95.0  # identical text should score near 100

    def test_related_text_moderate_similarity(self):
        resume = "Experienced backend developer skilled in Python, Django, and REST APIs"
        job = "Looking for a Python backend engineer with Django experience"
        score = get_semantic_similarity(resume, job)
        assert score > 50.0  # related content should score reasonably high

    def test_unrelated_text_low_similarity(self):
        resume = "Professional chef with 10 years of experience in Italian cuisine"
        job = "Looking for a Python backend engineer with Django experience"
        score = get_semantic_similarity(resume, job)
        assert score < 40.0  # unrelated content should score low

    def test_score_within_valid_range(self):
        score = get_semantic_similarity("some text", "other text")
        assert 0.0 <= score <= 100.0


class TestComputeMatch:
    def test_returns_expected_keys(self):
        result = compute_match(
            resume_text="Python developer with Django and SQL experience",
            resume_skills="python, django, sql",
            resume_experience_years=3.0,
            job_description="Looking for a Python developer",
            required_skills="python, django, aws",
            required_experience=2.0,
        )
        expected_keys = {
            "semantic_score", "keyword_score", "final_score",
            "explanation", "matched_skills", "missing_skills",
        }
        assert expected_keys.issubset(result.keys())

    def test_final_score_within_bounds(self):
        result = compute_match(
            resume_text="Python developer",
            resume_skills="python",
            resume_experience_years=1.0,
            job_description="Need a Python developer",
            required_skills="python, django, aws",
            required_experience=5.0,
        )
        assert 0.0 <= result["final_score"] <= 100.0

    def test_explanation_excludes_experience_mention(self):
        """Experience should influence the score but not appear in the explanation text."""
        result = compute_match(
            resume_text="Python developer",
            resume_skills="python",
            resume_experience_years=1.0,
            job_description="Need a Python developer",
            required_skills="python, django",
            required_experience=5.0,
        )
        assert "experience" not in result["explanation"].lower()
