import pytest
from pathlib import Path
from app.documents.processor import DocumentProcessor


def test_document_validation():
    processor = DocumentProcessor()
    # Allowed files
    valid, msg = processor.validate_file("notes.pdf", 1024)
    assert valid is True

    valid, msg = processor.validate_file("lecture.txt", 500)
    assert valid is True

    # Disallowed extension
    valid, msg = processor.validate_file("script.exe", 1024)
    assert valid is False
    assert "Unsupported file type" in msg

    # Empty file
    valid, msg = processor.validate_file("empty.pdf", 0)
    assert valid is False
    assert "empty" in msg


def test_document_chunking():
    processor = DocumentProcessor()
    sections = [
        {"page": 1, "text": "This is a sentence about Operating Systems scheduling and CPU queues. " * 30}
    ]
    chunks = processor.chunk_document(sections)
    assert len(chunks) >= 1
    assert "Operating Systems" in chunks[0]["content"]
    assert chunks[0]["metadata"]["page"] == 1
