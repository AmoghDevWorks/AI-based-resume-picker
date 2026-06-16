from fastapi import FastAPI

from routes.ranking import (
    router as ranking_router
)

app = FastAPI(
    title="Redrob Candidate Ranking System"
)


@app.get("/")
async def root():

    return {
        "message": "API is running"
    }


app.include_router(
    ranking_router,
    prefix="/ranking",
    tags=["Ranking"]
)