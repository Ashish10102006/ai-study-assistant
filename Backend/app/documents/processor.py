import os
import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from app.config.settings import get_settings

logger = logging.getLogger("ai_study_assistant.documents")


class DocumentProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.chunk_size = 1000
        self.chunk_overlap = 150

    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """Validates file extension and size constraints."""
        allowed_exts = {".pdf", ".txt", ".md"}
        ext = Path(filename).suffix.lower()

        if ext not in allowed_exts:
            return False, f"Unsupported file type '{ext}'. Supported formats are: PDF, TXT, and MD."

        max_bytes = self.settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, f"File exceeds maximum allowed size of {self.settings.MAX_FILE_SIZE_MB}MB."

        if file_size == 0:
            return False, "Uploaded file is empty."

        return True, ""

    def extract_text(self, file_path: Path, file_type: str) -> List[Dict[str, Any]]:
        """
        Extracts textual content from PDF, TXT, or MD files.
        Returns a list of dictionaries with content and page/section metadata.
        """
        extracted_sections: List[Dict[str, Any]] = []

        if file_type == "application/pdf" or file_path.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(str(file_path))
                for page_idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    clean_text = " ".join(text.split())
                    if clean_text:
                        extracted_sections.append({
                            "page": page_idx + 1,
                            "text": clean_text
                        })
            except Exception as e:
                logger.error(f"Error extracting PDF text from {file_path}: {e}")
                raise ValueError(f"Could not read PDF document: {e}")

        elif file_path.suffix.lower() in {".txt", ".md"}:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    clean_text = " ".join(content.split())
                    if clean_text:
                        extracted_sections.append({
                            "page": 1,
                            "text": clean_text
                        })
            except Exception as e:
                logger.error(f"Error reading text document from {file_path}: {e}")
                raise ValueError(f"Could not read text file: {e}")

        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        return extracted_sections

    def chunk_document(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Splits extracted sections into structured overlapping chunks.
        """
        chunks: List[Dict[str, Any]] = []

        for section in sections:
            text = section["text"]
            page = section.get("page", 1)

            if len(text) <= self.chunk_size:
                chunks.append({
                    "content": text,
                    "metadata": {"page": page, "char_length": len(text)}
                })
                continue

            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                chunks.append({
                    "content": chunk_text,
                    "metadata": {"page": page, "start_char": start, "end_char": end}
                })
                start += (self.chunk_size - self.chunk_overlap)

        return chunks


_doc_processor: DocumentProcessor = DocumentProcessor()

def get_document_processor() -> DocumentProcessor:
    return _doc_processor
