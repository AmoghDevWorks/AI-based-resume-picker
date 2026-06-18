# job : manages everything -> from here we call for each candidate
from fastapi import UploadFile

async def rank_candidates(
    jd: UploadFile,
    candidates: UploadFile,
    top_k: int
):
    # Put your ranking logic here

    return {
        "jd_filename": jd.filename,
        "candidates_filename": candidates.filename,
        "top_k": top_k,
        "message": "Files received successfully"
    }