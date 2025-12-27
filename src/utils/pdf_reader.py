"""
PDF reading utilities with streaming and chunking support.
"""
import pdfplumber
from typing import Generator, List
from pathlib import Path
import logging


class StreamingPDFReader:
    """Read PDF files in chunks to manage memory efficiently."""

    def __init__(self, file_path: str, chunk_size: int = 10):
        """
        Initialize PDF reader.

        Args:
            file_path: Path to PDF file
            chunk_size: Number of pages to process at once
        """
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

    def get_page_count(self) -> int:
        """Get total number of pages in PDF."""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            self.logger.error(f"Error reading PDF page count: {e}")
            raise

    def read_pages_chunked(self) -> Generator[List[str], None, None]:
        """
        Read PDF pages in chunks, yielding lines of text.

        Yields:
            List of text lines from each chunk of pages
        """
        try:
            with pdfplumber.open(self.file_path) as pdf:
                total_pages = len(pdf.pages)
                self.logger.info(f"Processing {total_pages} pages from {self.file_path.name}")

                for start_idx in range(0, total_pages, self.chunk_size):
                    end_idx = min(start_idx + self.chunk_size, total_pages)
                    chunk_lines = []

                    self.logger.debug(f"Reading pages {start_idx + 1}-{end_idx}")

                    for page_num in range(start_idx, end_idx):
                        try:
                            page = pdf.pages[page_num]
                            text = page.extract_text() or ""
                            lines = text.splitlines()
                            chunk_lines.extend(lines)
                        except Exception as e:
                            self.logger.warning(
                                f"Error extracting text from page {page_num + 1}: {e}"
                            )
                            continue

                    if chunk_lines:
                        yield chunk_lines

        except Exception as e:
            self.logger.error(f"Error reading PDF file: {e}")
            raise

    def read_all_lines(self) -> List[str]:
        """
        Read all lines from PDF at once.
        Use only for smaller files.

        Returns:
            List of all text lines
        """
        all_lines = []
        for chunk in self.read_pages_chunked():
            all_lines.extend(chunk)
        return all_lines


class PDFInfo:
    """Get metadata about PDF file."""

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get PDF file size in MB."""
        path = Path(file_path)
        return path.stat().st_size / (1024 * 1024)

    @staticmethod
    def get_info(file_path: str) -> dict:
        """
        Get comprehensive PDF information.

        Returns:
            Dictionary with file metadata
        """
        path = Path(file_path)
        info = {
            'filename': path.name,
            'size_mb': PDFInfo.get_file_size_mb(file_path),
            'exists': path.exists()
        }

        try:
            with pdfplumber.open(file_path) as pdf:
                info['page_count'] = len(pdf.pages)
                info['metadata'] = pdf.metadata
        except Exception as e:
            info['error'] = str(e)

        return info
