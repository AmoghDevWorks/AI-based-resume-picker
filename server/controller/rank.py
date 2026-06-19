# job : manages everything -> from here we call for each candidate
from fastapi import UploadFile

from .utils.pdfWordFileExtractor import extract_text
from .utils.embedding import get_embedding
from .utils.vectorDB import VectorDB

# Create a single VectorDB object
db = VectorDB(
    embedding_dim=384,
    session_id="user_123"
)

async def rank_candidates(
    jd: UploadFile,
    candidates: UploadFile,
    top_k: int
):
    # Parsing the JD Data and storing

    # Getting the text from the JD
    jd_text = extract_text(jd)

    # getting embeddings of jd_text
    jd_embedding = get_embedding(jd_text)

    # Store embedding in FAISS
    db.insert([jd_embedding], ids=["candidate_1"])
    db.save()




    # After processing is complete - DELETE that instance
    db.delete()

    return {
        "jd_filename": jd.filename,
        "candidates_filename": candidates.filename,
        "top_k": top_k,
        "message": "Files received successfully"
    }