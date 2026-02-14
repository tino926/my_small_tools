"""Configuration module for MMEX Reader."""

import os
import logging
from dataclasses import dataclass
from typing import Optional

from .error_handling import is_valid_date_format, is_valid_date_range

logger = logging.getLogger(__name__)


@dataclass
class MMEXReaderConfig:
    """Configuration class for MMEX Reader settings.
    
    Attributes:
        start_date: Start date for transaction queries (YYYY-MM-DD format).
        end_date: End date for transaction queries (YYYY-MM-DD format).
        db_file_path: Path to the MMEX database file.
        output_format: Output format for data export ('console', 'csv', 'json').
        max_sample_rows: Maximum number of sample rows to display for each table.
        show_schema: Whether to display database schema information.
        show_transactions: Whether to display transaction data.
        date_format: Format string for date parsing and formatting.
    """
    # Default configuration values
    start_date: str = "2025-01-01"
    end_date: str = "2025-05-31"
    db_file_path: Optional[str] = None
    output_format: str = "console"
    max_sample_rows: int = 3
    show_schema: bool = True
    show_transactions: bool = True
    date_format: str = "%Y-%m-%d"
    
    # Valid output formats
    VALID_OUTPUT_FORMATS = ('console', 'csv', 'json')
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate the configuration settings.
        
        Raises:
            ValueError: If any configuration setting is invalid.
        """
        self._validate_dates()
        self._validate_output_format()
        self._validate_sample_rows()
    
    def _validate_dates(self) -> None:
        """Validate date formats and ranges."""
        # Validate start date format
        if not is_valid_date_format(self.start_date, "start_date"):
            raise ValueError(f"Invalid start_date format: {self.start_date}. Expected format: {self.date_format}")
        
        # Validate end date format
        if not is_valid_date_format(self.end_date, "end_date"):
            raise ValueError(f"Invalid end_date format: {self.end_date}. Expected format: {self.date_format}")
        
        # Validate date range
        if not is_valid_date_range(self.start_date, self.end_date):
            raise ValueError(f"Invalid date range: start date {self.start_date} must be before or equal to end date {self.end_date}")
    
    def _validate_output_format(self) -> None:
        """Validate output format."""
        if self.output_format not in self.VALID_OUTPUT_FORMATS:
            raise ValueError(f"Invalid output_format: {self.output_format}. Must be one of {self.VALID_OUTPUT_FORMATS}")
    
    def _validate_sample_rows(self) -> None:
        """Validate max_sample_rows."""
        if self.max_sample_rows < 0:
            raise ValueError("max_sample_rows must be non-negative")
    
    @classmethod
    def from_env(cls) -> 'MMEXReaderConfig':
        """Create configuration from environment variables.
        
        Returns:
            MMEXReaderConfig: Configuration instance with values from environment.
        """
        try:
            # Get environment variables with defaults
            return cls(
                start_date=os.getenv("MMEX_START_DATE", "2025-01-01"),
                end_date=os.getenv("MMEX_END_DATE", "2025-05-31"),
                db_file_path=os.getenv("DB_FILE_PATH"),
                output_format=os.getenv("MMEX_OUTPUT_FORMAT", "console"),
                max_sample_rows=int(os.getenv("MMEX_MAX_SAMPLE_ROWS", "3")),
                show_schema=os.getenv("MMEX_SHOW_SCHEMA", "true").lower() == "true",
                show_transactions=os.getenv("MMEX_SHOW_TRANSACTIONS", "true").lower() == "true"
            )
        except ValueError as e:
            # Handle conversion errors (e.g., non-integer max_sample_rows)
            logger.error(f"Error parsing environment variables: {e}")
            logger.info("Using default configuration values")
            return cls()

__all__ = ["MMEXReaderConfig"]
