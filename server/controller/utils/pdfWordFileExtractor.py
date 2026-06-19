# controller/utils/pdfWordFileExtractor.py
"""
File-extraction layer — purely I/O, no scoring logic. Turns uploaded
files into plain Python data (text / dicts) for the scoring engine
(utils/scoring.py) to work with.
"""

import json
from io import BytesIO
from typing import List, Tuple

from docx import Document
from fastapi import UploadFile
# pyrefly: ignore [missing-import]
from pypdf import PdfReader


async def extract_text(file: UploadFile) -> str:
    """
    Extract raw text from an uploaded PDF or DOCX file. Used for the JD.

    Args:
        file: FastAPI UploadFile object

    Returns:
        str: Extracted text
    """
    extension = file.filename.split(".")[-1].lower()
    content = await file.read()

    if extension == "pdf":
        pdf = PdfReader(BytesIO(content))

        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text

    elif extension == "docx":
        doc = Document(BytesIO(content))

        text = "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
        )

        return text

    else:
        raise ValueError(
            f"Unsupported JD file format: '.{extension}'. Expected .pdf or .docx"
        )


async def extract_jsonl_records(file: UploadFile) -> Tuple[List[dict], int]:
    """
    Extract candidate records from an uploaded JSONL file — one JSON
    object per line, same schema the resume matcher used
    (profile / skills / redrob_signals / career_history / education /
    certifications).

    Malformed lines are skipped rather than raised, so one bad row in a
    multi-thousand-row upload doesn't fail the whole request.

    Args:
        file: FastAPI UploadFile object (.jsonl)

    Returns:
        (records, skipped_count)
    """
    extension = file.filename.split(".")[-1].lower()
    if extension not in ("jsonl", "ndjson", "json"):
        raise ValueError(
            f"Unsupported candidates file format: '.{extension}'. Expected .jsonl"
        )

    content = await file.read()
    text = content.decode("utf-8")

    records: List[dict] = []
    skipped = 0

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            skipped += 1

    return records, skipped