"""
Logging configuration with colored console output and file logging.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


class ParserLogger:
    """Custom logger for pairing parser."""

    def __init__(
        self,
        name: str = "PairingParser",
        level: str = "INFO",
        log_dir: Optional[str] = None,
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers.clear()

        # Console handler with colors
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))

            if COLORLOG_AVAILABLE:
                console_formatter = colorlog.ColoredFormatter(
                    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )

            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if file_output and log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_path / "pairing_parser.log",
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file

            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        return self.logger


def get_logger(
    name: str = "PairingParser",
    config: Optional[dict] = None
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name
        config: Configuration dict with logging settings

    Returns:
        Configured logger instance
    """
    if config is None:
        config = {
            'level': 'INFO',
            'console_output': True,
            'file_output': True,
            'log_dir': 'logs'
        }

    parser_logger = ParserLogger(
        name=name,
        level=config.get('level', 'INFO'),
        log_dir=config.get('log_dir', 'logs'),
        console_output=config.get('console_output', True),
        file_output=config.get('file_output', True),
        max_bytes=config.get('max_log_size_mb', 10) * 1024 * 1024,
        backup_count=config.get('backup_count', 5)
    )

    return parser_logger.get_logger()
