from fastapi import FastAPI
from app.database import Base, engine
from app.routers import auth



app = FastAPI(title="SmartHire API")

app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "SmartHire API is running"}
