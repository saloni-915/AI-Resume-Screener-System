import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth.dependencies import get_current_user, get_db

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", response_model=schemas.JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = models.Job(
        title=job_in.title,
        description=job_in.description,
        required_skills=job_in.required_skills,
        experience=job_in.experience,
        education=job_in.education,
        location=job_in.location,
        salary=job_in.salary,
        recruiter_id=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/", response_model=List[schemas.JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Only shows jobs created by the logged-in recruiter."""
    return (
        db.query(models.Job)
        .filter(models.Job.recruiter_id == current_user.id)
        .order_by(models.Job.created_at.desc())
        .all()
    )


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user.id)
    logger = logging.getLogger(__name__)
    logger.info(f"Job {job.id} created by recruiter {current_user.id}")
    return job


@router.put("/{job_id}", response_model=schemas.JobOut)
def update_job(
    job_id: int,
    job_in: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user.id)
    job.title = job_in.title
    job.description = job_in.description
    job.required_skills = job_in.required_skills
    job.experience = job_in.experience
    job.education = job_in.education
    job.location = job_in.location
    job.salary = job_in.salary
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user.id)
    db.delete(job)
    db.commit()
    {"message": "Job deleted successfully."}


def _get_owned_job_or_404(db: Session, job_id: int, recruiter_id: int) -> models.Job:
    """Ensures the job exists AND belongs to the requesting recruiter."""
    job = (
        db.query(models.Job)
        .filter(models.Job.id == job_id, models.Job.recruiter_id == recruiter_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
