import fitz  # PyMuPDF
from io import BytesIO
import re
import asyncio

class PDFExtractor:
    @staticmethod
    async def extract(file_bytes: bytes) -> dict:
        """Extract and clean text from PDF"""
        def _sync_extract():
            try:
                with fitz.open(stream=BytesIO(file_bytes)) as doc:
                    print(f"[DEBUG] Opened PDF with {len(doc)} pages")
                    raw_text = ""
                    for i, page in enumerate(doc):
                        page_text = page.get_text()
                        if not page_text.strip():
                            print(f"[WARNING] Page {i+1} has no extractable text")
                        raw_text += page_text + "\n"
                    
                    if not raw_text.strip():
                        print("[WARNING] No text could be extracted from the PDF")
                        return {
                            "raw_text": "",
                            "is_scanned": True
                        }
                    
                    cleaned_text = PDFExtractor._clean_text(raw_text)
                    print(f"[DEBUG] Extracted {len(cleaned_text)} characters of text")
                    return {
                        "raw_text": cleaned_text,
                        "is_scanned": not any(page.get_text() for page in doc)
                    }
            except Exception as e:
                print(f"[ERROR] Error extracting text from PDF: {str(e)}")
                return {
                    "raw_text": "",
                    "is_scanned": True,
                    "error": str(e)
                }
        
        return await asyncio.to_thread(_sync_extract)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove excessive whitespace but preserve structure"""
        # Replace 3+ newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Fix hyphenated words
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        return text.strip()