from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException
)

import os
import tempfile

from services.ranking_service import RankingService


router = APIRouter()


@router.post("/")
async def rank_candidates(

    jd_file: UploadFile = File(...),

    candidates_file: UploadFile = File(...),

    top_k: int = Form(100)

):
    
    print("\n========== NEW REQUEST ==========")
    try:
        print(f"JD file received: {jd_file.filename}") 
        print(f"Candidates file received: {candidates_file.filename}") 
        print(f"Top K requested: {top_k}")

        #
        # Save JD file
        #

        print("\nSaving JD file...")

        jd_suffix = os.path.splitext(
            jd_file.filename
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=jd_suffix
        ) as temp_jd:

            temp_jd.write(
                await jd_file.read()
            )

            jd_path = temp_jd.name

        print(f"JD saved to {jd_path}")

        #
        # Save candidates.jsonl
        #

        print("\nSaving candidates file...")

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jsonl"
        ) as temp_candidates:

            temp_candidates.write(
                await candidates_file.read()
            )

            candidates_path = temp_candidates.name

        print(f"Candidates saved to {candidates_path}")
        #
        # Run ranking pipeline
        #
        print("\nInitializing RankingService...")

        ranking_service = RankingService()

        results = ranking_service.rank(

            jd_path=jd_path,

            candidates_path=candidates_path,

            top_k=top_k

        )

        print("Ranking completed successfully.") 
        print(f"Returned {len(results)} candidates.")

        #
        # Remove temp files
        #
        print("\nCleaning temporary files...")

        os.remove(jd_path)
        os.remove(candidates_path)

        print("Temporary files deleted.") 
        print("\n========== REQUEST COMPLETED ==========\n")

        return {

            "top_k": top_k,

            "num_results": len(results),

            "results": results

        }

    except Exception as e:
        print("\n========== REQUEST FAILED ==========") 
        print(f"ERROR: {str(e)}")

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )