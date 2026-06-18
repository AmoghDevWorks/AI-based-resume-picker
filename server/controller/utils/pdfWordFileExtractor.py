# utils/extract_text.py

from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document


async def extract_text(file):
    """
    Extract text from PDF or DOCX files.

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
            f"Unsupported file format: {extension}"
        )