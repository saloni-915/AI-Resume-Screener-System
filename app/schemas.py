from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------- User / Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ---------- Job ----------
class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: str
    experience: float
    education: str
    location: str
    salary: float


class JobOut(BaseModel):
    id: int
    title: str
    description: str
    required_skills: str
    experience: float
    education: str
    location: str
    salary: float
    recruiter_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Resume ----------
class ResumeOut(BaseModel):
    id: int
    job_id: int
    original_filename: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeDetailOut(ResumeOut):
    raw_text: Optional[str] = None


# ---------- ParsedResume ----------
class ParsedResumeOut(BaseModel):
    id: int
    resume_id: int
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    experience_years: Optional[float] = None
    parsed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- MatchResult ----------
class MatchResultOut(BaseModel):
    id: int
    job_id: int
    resume_id: int
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    final_score: Optional[float] = None
    explanation: Optional[str] = None
    matched_skills: Optional[str] = None
    missing_skills: Optional[str] = None
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateRanking(BaseModel):
    """Used for the ranking dashboard — combines resume + parsed + match info."""

    resume_id: int
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    final_score: Optional[float] = None
    explanation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
