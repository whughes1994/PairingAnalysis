#!/usr/bin/env python3
"""
Main entry point for the Pairing Parser.
Processes airline pairing PDF files into structured JSON.
"""
import sys
import time
from pathlib import Path
from typing import Optional
import yaml
import click
from tqdm import tqdm

from .utils import get_logger, StreamingPDFReader, PDFInfo, StreamingTextReader, TextFileInfo, JSONFileWriter
from .parsers import PairingParser, PairingValidator
from .models import MasterData


def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "parser_config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        return get_default_config()

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_default_config() -> dict:
    """Get default configuration."""
    return {
        'processing': {
            'page_chunk_size': 10,
            'skip_on_error': True
        },
        'output': {
            'format': 'json',
            'indent': 2,
            'create_backup': True
        },
        'validation': {
            'enabled': True,
            'strict_mode': False
        },
        'logging': {
            'level': 'INFO',
            'console_output': True,
            'file_output': True,
            'log_dir': 'logs'
        },
        'parser': {
            'leg_columns': {},
            'patterns': {}
        }
    }


def process_single_file(
    input_path: str,
    output_path: str,
    config: dict,
    logger
) -> bool:
    """
    Process a single PDF or DAT file.

    Args:
        input_path: Path to input PDF or DAT file
        output_path: Path to output JSON
        config: Configuration dictionary
        logger: Logger instance

    Returns:
        True if successful
    """
    start_time = time.time()

    try:
        # Detect file type and get info
        input_file = Path(input_path)
        file_ext = input_file.suffix.lower()

        if file_ext == '.dat':
            # Process .DAT text file
            file_info = TextFileInfo.get_info(input_path)
            logger.info(f"Processing DAT file: {file_info['filename']}")
            logger.info(f"  Size: {file_info['size_mb']:.2f} MB")
            logger.info(f"  Lines: {file_info.get('line_count', 'unknown')}")

            # Initialize parser
            parser = PairingParser(config)

            # Read and parse text file in chunks
            text_reader = StreamingTextReader(
                input_path,
                chunk_size=1000  # Lines per chunk
            )

            total_chunks = text_reader.get_page_count()
            line_number = 0

            # Create progress bar
            with tqdm(total=total_chunks, desc="Processing chunks", unit="chunk") as pbar:
                for chunk_lines in text_reader.read_pages_chunked():
                    for line in chunk_lines:
                        line_number += 1
                        parser.parse_line(line, line_number)

                    pbar.update(1)

        elif file_ext == '.pdf':
            # Process PDF file
            file_info = PDFInfo.get_info(input_path)
            logger.info(f"Processing PDF: {file_info['filename']}")
            logger.info(f"  Size: {file_info['size_mb']:.2f} MB")
            logger.info(f"  Pages: {file_info.get('page_count', 'unknown')}")

            # Initialize parser
            parser = PairingParser(config)

            # Read and parse PDF in chunks
            pdf_reader = StreamingPDFReader(
                input_path,
                chunk_size=config['processing']['page_chunk_size']
            )

            total_pages = pdf_reader.get_page_count()
            line_number = 0

            # Create progress bar
            with tqdm(total=total_pages, desc="Processing pages", unit="page") as pbar:
                for chunk_lines in pdf_reader.read_pages_chunked():
                    for line in chunk_lines:
                        line_number += 1
                        parser.parse_line(line, line_number)

                    pbar.update(config['processing']['page_chunk_size'])

        else:
            logger.error(f"Unsupported file type: {file_ext}. Supported types: .pdf, .dat")
            return False

        # Finalize parsing
        master_data = parser.finalize()

        # Add metadata
        processing_time = time.time() - start_time
        master_data.add_metadata(
            source_file=file_info['filename'],
            page_count=file_info.get('page_count', file_info.get('line_count', 0)),
            processing_time=processing_time
        )

        # Validate if enabled
        if config['validation']['enabled']:
            logger.info("Validating parsed data...")
            validator = PairingValidator(
                strict_mode=config['validation']['strict_mode']
            )

            for bid_period in master_data.data:
                validator.validate_bid_period(bid_period)

        # Write output
        logger.info(f"Writing output to: {output_path}")
        writer = JSONFileWriter(
            create_backup=config['output']['create_backup']
        )

        # Convert to dict for JSON serialization
        output_data = master_data.model_dump()

        writer.write(
            output_data,
            output_path,
            indent=config['output']['indent']
        )

        # Print statistics
        stats = parser.get_stats()
        logger.info("=" * 60)
        logger.info("Processing Complete!")
        logger.info(f"  Total lines processed: {stats['total_lines']}")
        logger.info(f"  Pairings parsed: {stats['pairings_parsed']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info(f"  Processing time: {processing_time:.2f}s")
        logger.info(f"  Output file: {output_path}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Failed to process {input_path}: {e}", exc_info=True)
        return False


def process_directory(
    input_dir: str,
    output_dir: str,
    config: dict,
    logger
) -> dict:
    """
    Process all PDF files in a directory.

    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        config: Configuration dictionary
        logger: Logger instance

    Returns:
        Dictionary with processing results
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Find all PDF files
    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return {'success': 0, 'failed': 0}

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    results = {'success': 0, 'failed': 0, 'files': []}

    for pdf_file in pdf_files:
        output_file = output_path / f"{pdf_file.stem}.json"

        logger.info(f"\n{'=' * 60}")
        success = process_single_file(
            str(pdf_file),
            str(output_file),
            config,
            logger
        )

        if success:
            results['success'] += 1
        else:
            results['failed'] += 1

        results['files'].append({
            'input': str(pdf_file),
            'output': str(output_file),
            'success': success
        })

    return results


@click.command()
@click.option(
    '--input',
    '-i',
    'input_file',
    type=click.Path(exists=True),
    help='Input PDF file path'
)
@click.option(
    '--output',
    '-o',
    'output_file',
    type=click.Path(),
    help='Output JSON file path'
)
@click.option(
    '--input-dir',
    type=click.Path(exists=True),
    help='Input directory containing PDF files'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    help='Output directory for JSON files'
)
@click.option(
    '--config',
    '-c',
    type=click.Path(exists=True),
    help='Configuration YAML file'
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def main(input_file, output_file, input_dir, output_dir, config, verbose):
    """
    Airline Pairing Parser - Convert pairing PDFs to structured JSON.

    Examples:

        # Process single file
        python main.py -i "Pairing Source Docs/ORDDSL.pdf" -o "output/ORDDSL.json"

        # Process entire directory
        python main.py --input-dir "Pairing Source Docs" --output-dir "output"

        # Use custom config
        python main.py -i input.pdf -o output.json -c custom_config.yaml
    """
    # Load configuration
    cfg = load_config(config)

    # Override log level if verbose
    if verbose:
        cfg['logging']['level'] = 'DEBUG'

    # Setup logger
    logger = get_logger("PairingParser", cfg['logging'])

    logger.info("Airline Pairing Parser Starting...")

    # Validate arguments
    if input_file and output_file:
        # Single file mode
        success = process_single_file(input_file, output_file, cfg, logger)
        sys.exit(0 if success else 1)

    elif input_dir and output_dir:
        # Directory mode
        results = process_directory(input_dir, output_dir, cfg, logger)

        logger.info("\n" + "=" * 60)
        logger.info("Batch Processing Complete!")
        logger.info(f"  Successful: {results['success']}")
        logger.info(f"  Failed: {results['failed']}")
        logger.info("=" * 60)

        sys.exit(0 if results['failed'] == 0 else 1)

    else:
        logger.error("Must specify either --input/--output or --input-dir/--output-dir")
        click.echo(click.get_current_context().get_help())
        sys.exit(1)


if __name__ == '__main__':
    main()
