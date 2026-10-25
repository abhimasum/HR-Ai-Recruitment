import io

from docx import Document
from pypdf import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs).strip()
    if name.endswith(".txt"):
        return content.decode("utf-8", errors="ignore").strip()
    raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")
