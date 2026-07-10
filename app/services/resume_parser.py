import os
import re

import docx
import pdfplumber
import spacy

from app.services.skill_keywords import SKILL_KEYWORDS

nlp = spacy.load("en_core_web_sm")


EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(\+?\d{1,3}[\s-]?)?(\d[\s-]?){9,10}\d"
EXPERIENCE_REGEX = r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience"


def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from a PDF or DOCX file."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    elif ext == ".docx":
        document = docx.Document(file_path)
        return "\n".join(para.text for para in document.paragraphs if para.text.strip())

    else:
        raise ValueError(
            f"Unsupported file type: {ext}. Only .pdf and .docx are supported."
        )


def clean_text(raw_text: str) -> str:
    """Normalize whitespace, remove excessive blank lines."""
    lines = [line.strip() for line in raw_text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def extract_email(text: str) -> str | None:
    match = re.search(EMAIL_REGEX, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = re.search(PHONE_REGEX, text)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(0).strip())


def extract_name(text: str) -> str | None:
    """Uses spaCy NER — assumes candidate's name appears in the first few lines."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    first_chunk = "\n".join(lines[:5])
    # First try spaCy
    doc = nlp(first_chunk)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    # Fallback: first line as name
    if lines:
        first_line = lines[0]

        if (
            "@" not in first_line
            and "phone" not in first_line.lower()
            and "mobile" not in first_line.lower()
            and len(first_line.split()) <= 4
        ):
            return first_line

    return None


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        # Escape special regex characters (important for skills like "c++", "c#")
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def extract_experience_years(text: str) -> float | None:
    match = re.search(EXPERIENCE_REGEX, text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def extract_education(text: str) -> str | None:
    """Simple heuristic — looks for common degree keywords, captures full line."""
    degree_patterns = [
        r"B\.?Tech\.?[^\n]*",
        r"M\.?Tech\.?[^\n]*",
        r"Bachelor[^\n]*",
        r"Master[^\n]*",
        r"B\.?Sc\.?[^\n]*",
        r"M\.?Sc\.?[^\n]*",
        r"MBA[^\n]*",
        r"Ph\.?D\.?[^\n]*",
    ]
    for pattern in degree_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def parse_resume(raw_text: str) -> dict:
    """Runs all extractors and returns a structured dict, matching ParsedResume fields."""
    cleaned = clean_text(raw_text)
    skills = extract_skills(cleaned)

    return {
        "candidate_name": extract_name(cleaned),
        "candidate_email": extract_email(cleaned),
        "candidate_phone": extract_phone(cleaned),
        "skills": ", ".join(skills) if skills else None,
        "education": extract_education(cleaned),
        "experience_years": extract_experience_years(cleaned),
    }
