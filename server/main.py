from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Redrob Candidate Ranking API is running"}


@app.post("/rank")
async def rank_candidates(
    jd: UploadFile = File(...),
    candidates: UploadFile = File(...),
    top_k: int = Form(...)
):
    return {
        "jd_filename": jd.filename,
        "candidates_filename": candidates.filename,
        "top_k": top_k,
        "message": "Files received successfully"
    }