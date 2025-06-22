import fitz
from docx import Document

def extract_pdf(path):
    return "\n".join([page.get_text() for page in fitz.open(path)])

def extract_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])
