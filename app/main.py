from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, jobs, matching, resumes

app = FastAPI(title="SmartHire API")

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(matching.router)


@app.get("/")
def read_root():
    return {"message": "SmartHire API is running"}
