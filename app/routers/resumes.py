import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth.dependencies import get_current_user, get_db
from app.routers.jobs import _get_owned_job_or_404
from app.services.resume_parser import extract_text_from_file, parse_resume

router = APIRouter(prefix="/jobs/{job_id}/resumes", tags=["Resumes"])

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post(
    "/", response_model=schemas.ParsedResumeOut, status_code=status.HTTP_201_CREATED
)
def upload_resume(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Ownership check — job must belong to this recruiter
    job = _get_owned_job_or_404(db, job_id, current_user.id)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, detail=f"Only {ALLOWED_EXTENSIONS} files are allowed"
        )

    # Unique filename taaki collisions na ho
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        raw_text = extract_text_from_file(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail=f"Could not extract text: {str(e)}")

    resume = models.Resume(
        job_id=job.id,
        original_filename=file.filename,
        file_path=file_path,
        raw_text=raw_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    parsed_fields = parse_resume(raw_text)
    parsed = models.ParsedResume(resume_id=resume.id, **parsed_fields)

    # ---------------- Duplicate Check ----------------
    email = parsed_fields.get("candidate_email")
    phone = parsed_fields.get("candidate_phone")

    duplicate_query = (
        db.query(models.ParsedResume)
        .join(models.Resume)
        .filter(models.Resume.job_id == job.id)
    )

    if email:
        duplicate_query = duplicate_query.filter(
            models.ParsedResume.candidate_email == email
        )
    elif phone:
        duplicate_query = duplicate_query.filter(
            models.ParsedResume.candidate_phone == phone
        )
    else:
        duplicate_query = None

    if duplicate_query:
        existing = duplicate_query.first()
        if existing:
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail="This candidate has already been uploaded for this job.",
            )
    # -------------------------------------------------

    db.add(parsed)
    db.commit()
    db.refresh(parsed)

    return parsed


@router.get("/", response_model=List[schemas.ParsedResumeOut])
def list_resumes(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job_or_404(db, job_id, current_user.id)
    return (
        db.query(models.ParsedResume)
        .join(models.Resume)
        .filter(models.Resume.job_id == job.id)
        .all()
    )


@router.get("/{resume_id}", response_model=schemas.ResumeDetailOut)
def get_resume_detail(
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
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
