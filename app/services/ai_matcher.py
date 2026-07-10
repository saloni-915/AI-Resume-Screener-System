from sentence_transformers import SentenceTransformer, util

_model = SentenceTransformer("all-MiniLM-L6-v2")

SEMANTIC_WEIGHT = 0.50
KEYWORD_WEIGHT = 0.35
EXPERIENCE_WEIGHT = 0.15


def get_semantic_similarity(resume_text: str, job_description: str) -> float:
    """Returns cosine similarity between resume and JD embeddings, scaled 0-100."""
    embeddings = _model.encode([resume_text, job_description], convert_to_tensor=True)
    similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
    # cos_sim can be slightly negative in theory; clamp to 0-1 range then scale
    similarity = max(0.0, min(1.0, similarity))
    return round(similarity * 100, 2)


def get_keyword_overlap(resume_skills: str, required_skills: str) -> dict:
    """
    Compares resume's extracted skills against job's required skills.
    Returns matched skills, missing skills, and an overlap score (0-100).
    """
    resume_skill_set = (
        {s.strip().lower() for s in resume_skills.split(",") if s.strip()}
        if resume_skills
        else set()
    )
    required_skill_set = (
        {s.strip().lower() for s in required_skills.split(",") if s.strip()}
        if required_skills
        else set()
    )

    if not required_skill_set:
        return {"matched": [], "missing": [], "score": 0.0}

    matched = sorted(resume_skill_set & required_skill_set)
    missing = sorted(required_skill_set - resume_skill_set)

    score = round((len(matched) / len(required_skill_set)) * 100, 2)
    return {"matched": matched, "missing": missing, "score": score}


def get_experience_score(
    candidate_years: float | None, required_years: float | None
) -> dict:
    """
    Scores how well candidate's experience matches the requirement.
    - Meets or exceeds requirement -> 100
    - Falls short -> proportional score (e.g. 2/5 years = 40%)
    """
    if not required_years or required_years <= 0:
        return {"score": 100.0, "note": "No specific experience requirement"}

    candidate_years = candidate_years or 0.0

    if candidate_years >= required_years:
        return {
            "score": 100.0,
            "note": f"Meets requirement ({candidate_years} yrs vs {required_years} yrs required)",
        }

    score = round((candidate_years / required_years) * 100, 2)
    return {
        "score": score,
        "note": f"Below requirement ({candidate_years} yrs vs {required_years} yrs required)",
    }


def generate_explanation(
    matched_skills: list[str],
    missing_skills: list[str],
    final_score: float,
) -> str:
    """Builds a short human-readable explanation combining all factors."""
    if matched_skills:
        strengths = ", ".join(skill.title() for skill in matched_skills[:5])
        strengths_text = f"Strong match on {strengths}."
    else:
        strengths_text = "No significant skill overlap found."

    if missing_skills:
        gaps = ", ".join(skill.title() for skill in missing_skills[:5])
        gaps_text = f" Missing: {gaps}."
    else:
        gaps_text = " No major skill gaps identified."

    return f"Match Score: {final_score}% — {strengths_text}{gaps_text}."


def compute_match(
    resume_text: str,
    resume_skills: str,
    resume_experience_years: float | None,
    job_description: str,
    required_skills: str,
    required_experience: float | None,
) -> dict:
    """Main entry point — combines semantic + keyword + experience scoring."""
    semantic_score = get_semantic_similarity(resume_text, job_description)
    keyword_result = get_keyword_overlap(resume_skills, required_skills)
    experience_result = get_experience_score(
        resume_experience_years, required_experience
    )

    final_score = round(
        (semantic_score * SEMANTIC_WEIGHT)
        + (keyword_result["score"] * KEYWORD_WEIGHT)
        + (experience_result["score"] * EXPERIENCE_WEIGHT),
        2,
    )

    explanation = generate_explanation(
        keyword_result["matched"],
        keyword_result["missing"],
        final_score,
    )

    return {
        "semantic_score": semantic_score,
        "keyword_score": keyword_result["score"],
        "final_score": final_score,
        "explanation": explanation,
        "matched_skills": (
            ", ".join(keyword_result["matched"]) if keyword_result["matched"] else None
        ),
        "missing_skills": (
            ", ".join(keyword_result["missing"]) if keyword_result["missing"] else None
        ),
    }
