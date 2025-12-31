"""
Text file reading utilities for .DAT files with the same interface as PDF reader.
"""
from typing import Generator, List
from pathlib import Path
import logging


class StreamingTextReader:
    """Read text files (.DAT) with the same interface as StreamingPDFReader."""

    def __init__(self, file_path: str, chunk_size: int = 1000):
        """
        Initialize text reader.

        Args:
            file_path: Path to text/DAT file
            chunk_size: Number of lines to process at once
        """
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

        if not self.file_path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

    def get_page_count(self) -> int:
        """
        Get estimated 'page count' for text files.
        Returns number of chunks (not actual pages).
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                total_lines = sum(1 for _ in f)
            # Return number of chunks
            return (total_lines // self.chunk_size) + 1
        except Exception as e:
            self.logger.error(f"Error reading text file line count: {e}")
            raise

    def read_pages_chunked(self) -> Generator[List[str], None, None]:
        """
        Read text file lines in chunks.

        Yields:
            List of text lines from each chunk
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                chunk_lines = []

                for line_num, line in enumerate(f, 1):
                    # Remove carriage returns and strip
                    line = line.replace('\r', '').rstrip('\n')
                    chunk_lines.append(line)

                    # Yield chunk when it reaches chunk_size
                    if len(chunk_lines) >= self.chunk_size:
                        self.logger.debug(f"Yielding chunk of {len(chunk_lines)} lines")
                        yield chunk_lines
                        chunk_lines = []

                # Yield any remaining lines
                if chunk_lines:
                    self.logger.debug(f"Yielding final chunk of {len(chunk_lines)} lines")
                    yield chunk_lines

        except Exception as e:
            self.logger.error(f"Error reading text file: {e}")
            raise

    def read_all_lines(self) -> List[str]:
        """
        Read all lines from text file at once.

        Returns:
            List of all text lines
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Remove carriage returns and strip newlines
                lines = [line.replace('\r', '').rstrip('\n') for line in f]

            self.logger.info(f"Read {len(lines)} lines from {self.file_path.name}")
            return lines

        except Exception as e:
            self.logger.error(f"Error reading all lines: {e}")
            raise


class TextFileInfo:
    """Utility class for getting text file information."""

    @staticmethod
    def get_info(file_path: str) -> dict:
        """
        Get information about a text file.

        Args:
            file_path: Path to text file

        Returns:
            Dictionary with file information
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        size_bytes = path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        # Count lines
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for _ in f)

        return {
            'filename': path.name,
            'path': str(path.absolute()),
            'size_bytes': size_bytes,
            'size_mb': size_mb,
            'line_count': line_count,
            'file_type': 'text/dat'
        }
