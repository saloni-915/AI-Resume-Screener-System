from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=False)
    experience = Column(Float, nullable=False)
    education = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    salary = Column(Float, nullable=False)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recruiter = relationship("User", back_populates="jobs")
    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")
    match_results = relationship(
        "MatchResult", back_populates="job", cascade="all, delete-orphan"
    )


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    raw_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="resumes")
    parsed_data = relationship(
        "ParsedResume",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    match_results = relationship(
        "MatchResult", back_populates="resume", cascade="all, delete-orphan"
    )


class ParsedResume(Base):
    __tablename__ = "parsed_resumes"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), unique=True, nullable=False)
    candidate_name = Column(String(100), nullable=True)
    candidate_email = Column(String(100), nullable=True)
    candidate_phone = Column(String(100), nullable=True)
    skills = Column(Text, nullable=True)  # comma-separated or JSON string
    education = Column(String(100), nullable=True)
    experience_years = Column(Float, nullable=True)
    parsed_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="parsed_data")


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    semantic_score = Column(Float, nullable=True)  # embeddings-based similarity
    keyword_score = Column(Float, nullable=True)  # keyword overlap score
    final_score = Column(Float, nullable=True)  # combined weighted score
    explanation = Column(Text, nullable=True)  # strengths/gaps summary
    matched_skills = Column(Text, nullable=True)
    missing_skills = Column(Text, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="match_results")
    resume = relationship("Resume", back_populates="match_results")
