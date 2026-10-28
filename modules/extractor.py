import os
import re
from typing import Dict, Any, Tuple

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class ResumeExtractor:
    """Extracts and normalizes text and metadata from PDF resumes using PyMuPDF."""

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
    ALLOWED_EXTENSIONS = {'.pdf'}

    @staticmethod
    def validate_file(file_storage) -> Tuple[bool, str]:
        """
        Validates the uploaded file for format, existence, and size.
        Returns (is_valid, error_message).
        """
        if not file_storage or file_storage.filename == '':
            return False, "No file was selected for upload."

        filename = file_storage.filename.lower()
        _, ext = os.path.splitext(filename)
        if ext not in ResumeExtractor.ALLOWED_EXTENSIONS:
            return False, f"Invalid file format '{ext}'. Only standard PDF (.pdf) documents are supported."

        # Check file size by seeking
        file_storage.seek(0, os.SEEK_END)
        size = file_storage.tell()
        file_storage.seek(0)  # Reset pointer to start

        if size == 0:
            return False, "The uploaded PDF file is empty (0 bytes)."

        if size > ResumeExtractor.MAX_FILE_SIZE_BYTES:
            max_mb = ResumeExtractor.MAX_FILE_SIZE_BYTES // (1024 * 1024)
            return False, f"File size exceeds the {max_mb} MB limit. Please upload a smaller document."

        return True, ""

    @classmethod
    def extract_from_stream(cls, stream_or_bytes) -> Dict[str, Any]:
        """
        Extracts readable text, page structure, and metadata from PDF bytes or stream.
        """
        if fitz is None:
            return {
                "success": False,
                "text": "",
                "error": "PyMuPDF library is not installed on the server."
            }

        try:
            # If it's a file storage or stream, read bytes
            if hasattr(stream_or_bytes, 'read'):
                stream_or_bytes.seek(0)
                pdf_data = stream_or_bytes.read()
            else:
                pdf_data = stream_or_bytes

            doc = fitz.open(stream=pdf_data, filetype="pdf")

            if doc.is_encrypted:
                return {
                    "success": False,
                    "text": "",
                    "error": "This PDF is password-protected or encrypted. Please upload an unprotected copy."
                }

            page_count = len(doc)
            if page_count == 0:
                return {
                    "success": False,
                    "text": "",
                    "error": "The PDF does not contain any pages."
                }

            extracted_pages = []
            raw_text_parts = []

            for page_idx in range(page_count):
                page = doc.load_page(page_idx)
                text = page.get_text("text") or ""
                extracted_pages.append({
                    "page_number": page_idx + 1,
                    "text": text.strip(),
                    "char_count": len(text.strip())
                })
                raw_text_parts.append(text)

            metadata = doc.metadata or {}
            doc.close()

            full_raw_text = "\n\n".join(raw_text_parts)
            clean_text = cls.clean_text(full_raw_text)

            word_count = len(clean_text.split())
            char_count = len(clean_text)

            # Detect if PDF might be a scanned image without selectable text
            is_scanned = (char_count < 80 and page_count >= 1)

            if is_scanned:
                return {
                    "success": False,
                    "text": clean_text,
                    "is_scanned": True,
                    "error": "Extracted insufficient readable text. The PDF appears to be a scanned image or raster graphic without a selectable text layer."
                }

            return {
                "success": True,
                "text": clean_text,
                "raw_text": full_raw_text,
                "page_count": page_count,
                "word_count": word_count,
                "char_count": char_count,
                "pages": extracted_pages,
                "metadata": {
                    "title": metadata.get("title", "") or "",
                    "author": metadata.get("author", "") or "",
                    "producer": metadata.get("producer", "") or "",
                    "creation_date": metadata.get("creationDate", "") or ""
                },
                "is_scanned": False,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": f"Failed to parse PDF document: {str(e)}"
            }

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans and normalizes extracted resume text.
        Removes odd control characters, fixes broken hyphenations, collapses multiple spaces.
        """
        if not text:
            return ""

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Fix hyphenated words broken across lines (e.g. "experi-\nence" -> "experience")
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

        # Replace non-breaking spaces and tabs
        text = text.replace('\u00a0', ' ').replace('\t', ' ')

        # Remove control characters except newlines
        text = re.sub(r'[\x00-\x09\x0b-\x1f\x7f-\x9f]', '', text)

        # Collapse excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Collapse excessive horizontal spaces
        text = re.sub(r'[ ]{2,}', ' ', text)

        return text.strip()
