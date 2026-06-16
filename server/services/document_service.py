from pathlib import Path

from docx import Document
from pypdf import PdfReader


class DocumentService:

    def extract_text(
        self,
        file_path: str
    ) -> str:

        suffix = (
            Path(
                file_path
            )
            .suffix
            .lower()
        )

        if suffix == ".pdf":

            return self._read_pdf(
                file_path
            )

        elif suffix == ".docx":

            return self._read_docx(
                file_path
            )

        elif suffix == ".txt":

            return self._read_txt(
                file_path
            )

        raise ValueError(
            "Unsupported file type"
        )

    def _read_pdf(
        self,
        file_path: str
    ) -> str:

        reader = PdfReader(
            file_path
        )

        text = ""

        for page in reader.pages:

            text += (
                page.extract_text()
                or ""
            )

        return text

    def _read_docx(
        self,
        file_path: str
    ) -> str:

        document = Document(
            file_path
        )

        return "\n".join(
            paragraph.text
            for paragraph
            in document.paragraphs
        )

    def _read_txt(
        self,
        file_path: str
    ) -> str:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            return f.read()