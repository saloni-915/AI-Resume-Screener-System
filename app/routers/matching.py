from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.auth.dependencies import get_current_user, get_db
from app.routers.jobs import _get_owned_job_or_404
from app.services.ai_matcher import compute_match
from app.services.llm_helper import generate_candidate_summary

router = APIRouter(prefix="/jobs/{job_id}", tags=["Matching"])


@router.post(
    "/resumes/{resume_id}/match",
    response_model=schemas.MatchResultOut,
    status_code=status.HTTP_201_CREATED,
)
def match_resume_to_job(
    job_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user.id)

    resume = (
        db.query(models.Resume)
        .filter(models.Resume.id == resume_id, models.Resume.job_id == job.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found for this job")

    if not resume.raw_text:
        raise HTTPException(
            status_code=422, detail="Resume has no extracted text to match against"
        )

    parsed = resume.parsed_data

    if not parsed:
        raise HTTPException(status_code=422, detail="Resume has not been parsed yet.")
    resume_skills = parsed.skills or ""
    resume_experience = parsed.experience_years

    result = compute_match(
        resume_text=resume.raw_text,
        resume_skills=resume_skills,
        resume_experience_years=resume_experience,
        job_description=job.description,
        required_skills=job.required_skills,
        required_experience=job.experience,
    )

    # Agar pehle se match result exist karta hai is resume+job ke liye, to update karo (re-match support)
    existing = (
        db.query(models.MatchResult)
        .filter(
            models.MatchResult.job_id == job.id,
            models.MatchResult.resume_id == resume.id,
        )
        .first()
    )

    try:
        if existing:
            for key, value in result.items():
                setattr(existing, key, value)

            db.commit()
            db.refresh(existing)
            return existing

        match_result = models.MatchResult(job_id=job.id, resume_id=resume.id, **result)

        db.add(match_result)
        db.commit()
        db.refresh(match_result)

        return match_result

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save match result.")


@router.get("/rankings", response_model=List[schemas.CandidateRanking])
def get_rankings(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Returns all matched candidates for a job, sorted best-match first."""
    job = _get_owned_job_or_404(db, job_id, current_user.id)

    results = (
        db.query(models.MatchResult)
        .options(
            joinedload(models.MatchResult.resume).joinedload(models.Resume.parsed_data)
        )
        .filter(models.MatchResult.job_id == job.id)
        .order_by(models.MatchResult.final_score.desc())
        .all()
    )

    rankings = []
    for match in results:
        parsed = match.resume.parsed_data
        rankings.append(
            schemas.CandidateRanking(
                resume_id=match.resume_id,
                candidate_name=parsed.candidate_name if parsed else None,
                candidate_email=parsed.candidate_email if parsed else None,
                final_score=match.final_score,
                explanation=match.explanation,
            )
        )
    return rankings


@router.get("/resumes/{resume_id}/summary")
def get_candidate_summary(
    job_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user.id)

    resume = (
        db.query(models.Resume)
        .options(
        joinedload(models.Resume.parsed_data)
        )
        .filter(
            models.Resume.id == resume_id,
            models.Resume.job_id == job.id,
            )
            .first()
            )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found for this job")

    parsed = resume.parsed_data

    if not parsed:
        raise HTTPException(
            status_code=422,
            detail="Resume has not been parsed yet."
            )
    match = (
        db.query(models.MatchResult)
        .filter(models.MatchResult.job_id == job.id, models.MatchResult.resume_id == resume.id)
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Candidate has not been matched yet."
            )

    summary = generate_candidate_summary(
        candidate_name=parsed.candidate_name if parsed else None,
        skills=parsed.skills if parsed else None,
        experience_years=parsed.experience_years if parsed else None,
        education=parsed.education if parsed else None,
        matched_skills=match.matched_skills if match else None,
        missing_skills=match.missing_skills if match else None,
    )

    return {"resume_id": resume.id, "summary": summary}
