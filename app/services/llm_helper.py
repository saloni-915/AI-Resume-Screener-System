from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

_MODEL_NAME = "google/flan-t5-base"
_tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
_model = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_NAME)


def generate_candidate_summary(
    candidate_name: str | None,
    skills: str | None,
    experience_years: float | None,
    education: str | None,
    matched_skills: str | None,
    missing_skills: str | None,
) -> str:
    """
    Uses a local open-source LLM (FLAN-T5) to generate a short, human-readable
    paragraph summarizing a candidate's fit — no external API call required.
    """
    name = candidate_name or "This candidate"

    def _top_n(skill_str: str | None, n: int = 5) -> str:
        if not skill_str:
            return "none"
        items = [s.strip() for s in skill_str.split(",") if s.strip()]
        return ", ".join(items[:n])

    prompt = (
        f"Summarize this job candidate's profile in 2 short sentences, "
        f"in a professional recruiter tone:\n"
        f"{name} has {experience_years or 0} years of experience and key skills in "
        f"{_top_n(skills)}. "
        f"They match required skills: {_top_n(matched_skills)}. "
        f"They are missing: {_top_n(missing_skills)}."
    )

    inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    outputs = _model.generate(
        **inputs,
        max_new_tokens=100,
        min_new_tokens=20,
        num_beams=4,
        no_repeat_ngram_size=3,
        do_sample=False,
    )
    summary = _tokenizer.decode(outputs[0], skip_special_tokens=True)
    return summary.strip()
