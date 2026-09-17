import os
import io
import re
import zipfile
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
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
        allowed_exts = {".pdf", ".txt", ".md", ".docx"}
        ext = Path(filename).suffix.lower()

        if ext not in allowed_exts:
            return False, f"Unsupported file type '{ext}'. Supported formats are: PDF, TXT, MD, and DOCX."

        max_bytes = self.settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, f"File exceeds maximum allowed size of {self.settings.MAX_FILE_SIZE_MB}MB."

        if file_size == 0:
            return False, "Uploaded file is empty."

        return True, ""

    def extract_text(self, file_path: Path, file_type: str) -> List[Dict[str, Any]]:
        """
        Extracts textual content from PDF, TXT, MD, or DOCX files.
        Returns a list of dictionaries with content, page, and detected section metadata.
        """
        extracted_sections: List[Dict[str, Any]] = []
        ext = file_path.suffix.lower()

        # 1. PDF Processing
        if file_type == "application/pdf" or ext == ".pdf":
            try:
                reader = PdfReader(str(file_path))
                for page_idx, page in enumerate(reader.pages):
                    raw_text = page.extract_text() or ""
                    clean_text = " ".join(raw_text.split())
                    if clean_text:
                        section_name = self._detect_section_title(raw_text)
                        extracted_sections.append({
                            "page": page_idx + 1,
                            "section": section_name,
                            "text": clean_text
                        })
            except Exception as e:
                logger.error(f"Error extracting PDF text from {file_path}: {e}")
                raise ValueError(f"Could not read PDF document: {e}")

        # 2. Text / Markdown Processing
        elif ext in {".txt", ".md"}:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_content = f.read()

                # In markdown/text, split into logical sections by headings if present
                lines = raw_content.splitlines()
                current_section = "Introduction"
                current_buffer: List[str] = []
                current_page = 1
                page_char_count = 0

                for line in lines:
                    stripped = line.strip()
                    # Check for markdown heading (# Heading) or Section/Chapter
                    if stripped.startswith("#") or re.match(r"^(Chapter|Section|Module)\s+\d+", stripped, re.IGNORECASE):
                        if current_buffer:
                            text_block = " ".join(" ".join(current_buffer).split())
                            if text_block:
                                extracted_sections.append({
                                    "page": current_page,
                                    "section": current_section,
                                    "text": text_block
                                })
                            current_buffer = []
                        current_section = stripped.lstrip("#").strip()
                    else:
                        if stripped:
                            current_buffer.append(stripped)
                            page_char_count += len(stripped)
                            # Approximate page progression every ~3000 characters
                            if page_char_count >= 3000:
                                current_page += 1
                                page_char_count = 0

                if current_buffer:
                    text_block = " ".join(" ".join(current_buffer).split())
                    if text_block:
                        extracted_sections.append({
                            "page": current_page,
                            "section": current_section,
                            "text": text_block
                        })

                # Fallback if no sections were parsed
                if not extracted_sections and raw_content.strip():
                    extracted_sections.append({
                        "page": 1,
                        "section": "Main",
                        "text": " ".join(raw_content.split())
                    })

            except Exception as e:
                logger.error(f"Error reading text document from {file_path}: {e}")
                raise ValueError(f"Could not read text file: {e}")

        # 3. DOCX Processing (Native via zipfile & XML)
        elif ext == ".docx":
            try:
                paragraphs = self._extract_docx_paragraphs(file_path)
                full_text = " ".join(paragraphs)
                clean_text = " ".join(full_text.split())
                if clean_text:
                    extracted_sections.append({
                        "page": 1,
                        "section": "Document Content",
                        "text": clean_text
                    })
            except Exception as e:
                logger.error(f"Error reading DOCX document from {file_path}: {e}")
                raise ValueError(f"Could not read DOCX file: {e}")

        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return extracted_sections

    def chunk_document(
        self,
        sections: List[Dict[str, Any]],
        doc_title: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Splits extracted sections into structure-aware overlapping chunks.
        Preserves page, section, and character metadata.
        """
        chunks: List[Dict[str, Any]] = []

        for section_info in sections:
            text = section_info["text"]
            page = section_info.get("page", 1)
            section = section_info.get("section") or "General"

            if len(text) <= self.chunk_size:
                chunks.append({
                    "content": text,
                    "metadata": {
                        "page": page,
                        "section": section,
                        "doc_title": doc_title or "",
                        "char_length": len(text)
                    }
                })
                continue

            start = 0
            while start < len(text):
                end = start + self.chunk_size

                # Avoid breaking in the middle of a sentence if punctuation is nearby
                if end < len(text):
                    last_period = text.rfind(".", start + self.chunk_size - 120, end + 50)
                    if last_period != -1 and last_period > start:
                        end = last_period + 1

                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {
                            "page": page,
                            "section": section,
                            "doc_title": doc_title or "",
                            "start_char": start,
                            "end_char": end,
                            "char_length": len(chunk_text)
                        }
                    })

                start += (self.chunk_size - self.chunk_overlap)

        return chunks

    def _detect_section_title(self, raw_page_text: str) -> str:
        """Detects the likely chapter or section header from page text."""
        lines = [line.strip() for line in raw_page_text.splitlines() if line.strip()]
        for line in lines[:5]:
            # Matches "Chapter 1: Intro", "1.2 Architecture", or all-caps short title
            if re.match(r"^(Chapter|Section|Module|Unit)\s+\d+.*", line, re.IGNORECASE):
                return line[:80]
            if re.match(r"^\d+(\.\d+)*\s+[A-Z].*", line):
                return line[:80]
            if len(line) < 60 and line.isupper() and len(line.split()) <= 6:
                return line
        return ""

    def _extract_docx_paragraphs(self, file_path: Path) -> List[str]:
        """Reads paragraph text from DOCX document.xml using python standard library."""
        paragraphs: List[str] = []
        with zipfile.ZipFile(str(file_path)) as docx_zip:
            if "word/document.xml" not in docx_zip.namelist():
                raise ValueError("Invalid DOCX format: missing word/document.xml")
            xml_content = docx_zip.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            # Namespace for wordprocessingml
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            for p in tree.findall(".//w:p", ns):
                texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
                if texts:
                    paragraphs.append("".join(texts))
        return paragraphs


_doc_processor: DocumentProcessor = DocumentProcessor()


def get_document_processor() -> DocumentProcessor:
    return _doc_processor
