from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# managing import
from controller.rank import rank_candidates

load_dotenv()

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173/")

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
async def rank(
    jd: UploadFile = File(...),
    candidates: UploadFile = File(...),
    top_k: int = Form(...)
):
    return await rank_candidates(
        jd=jd,
        candidates=candidates,
        top_k=top_k
    )