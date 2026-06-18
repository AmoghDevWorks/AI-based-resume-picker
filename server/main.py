import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.ranking import router as ranking_router

app = FastAPI(title="Redrob Candidate Ranking System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "API is running"}


app.include_router(ranking_router, prefix="/ranking", tags=["Ranking"])