from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# managing import
from controller.rank import rank_candidates

#for docker
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.get("/")
# async def root():
#     return {"message": "Redrob Candidate Ranking API is running"}

#for docker
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
@app.get("/")
async def serve_react():
    return FileResponse("static/index.html")


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