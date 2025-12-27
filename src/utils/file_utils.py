"""
File I/O utilities for JSON output.
"""
import json
from pathlib import Path
from typing import Any, TextIO
from datetime import datetime
import logging


class StreamingJSONWriter:
    """Write JSON data incrementally to avoid memory issues."""

    def __init__(self, output_path: str, indent: int = 2):
        """
        Initialize streaming JSON writer.

        Args:
            output_path: Path to output JSON file
            indent: JSON indentation spaces
        """
        self.output_path = Path(output_path)
        self.indent = indent
        self.logger = logging.getLogger(__name__)
        self.file_handle: TextIO = None
        self.first_item = True

        # Create output directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        """Context manager entry."""
        self.file_handle = open(self.output_path, 'w', encoding='utf-8')
        self.file_handle.write('{\n')
        self.file_handle.write(f'{" " * self.indent}"data": [\n')
        self.first_item = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.file_handle:
            self.file_handle.write('\n' + ' ' * self.indent + '],\n')
            self.file_handle.write(f'{" " * self.indent}"metadata": {{}}\n')
            self.file_handle.write('}\n')
            self.file_handle.close()

    def write_item(self, item: Any):
        """
        Write a single item to the JSON array.

        Args:
            item: Item to write (should be JSON-serializable)
        """
        if not self.file_handle:
            raise RuntimeError("Writer not opened. Use as context manager.")

        if not self.first_item:
            self.file_handle.write(',\n')

        # Serialize the item
        item_json = json.dumps(item, indent=self.indent)

        # Indent each line
        indented_lines = []
        for line in item_json.split('\n'):
            indented_lines.append(' ' * (self.indent * 2) + line)

        self.file_handle.write('\n'.join(indented_lines))
        self.first_item = False

    def write_metadata(self, metadata: dict):
        """
        Write metadata section (call before closing).

        Args:
            metadata: Metadata dictionary
        """
        # This will be called at the end to update metadata
        pass  # Metadata written in __exit__ for now


class JSONFileWriter:
    """Standard JSON file writer with backup support."""

    def __init__(self, create_backup: bool = True):
        """
        Initialize JSON file writer.

        Args:
            create_backup: Whether to backup existing files
        """
        self.create_backup = create_backup
        self.logger = logging.getLogger(__name__)

    def write(self, data: Any, output_path: str, indent: int = 2):
        """
        Write data to JSON file.

        Args:
            data: Data to write
            output_path: Output file path
            indent: JSON indentation
        """
        output_path = Path(output_path)

        # Create backup if file exists
        if self.create_backup and output_path.exists():
            backup_path = output_path.with_suffix(
                f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            self.logger.info(f"Creating backup: {backup_path.name}")
            output_path.rename(backup_path)

        # Write new file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            self.logger.info(f"Successfully wrote output to {output_path}")
        except Exception as e:
            self.logger.error(f"Error writing JSON file: {e}")
            raise


def backup_file(file_path: str) -> Path:
    """
    Create a timestamped backup of a file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file
    """
    path = Path(file_path)
    if not path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.stem}_backup_{timestamp}{path.suffix}")

    path.rename(backup_path)
    return backup_path
