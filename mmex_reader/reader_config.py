"""Configuration module for MMEX Reader."""

import os
from dataclasses import dataclass
from typing import Optional

from mmex_reader.error_handling import is_valid_date_format, is_valid_date_range


@dataclass
class MMEXReaderConfig:
    """Configuration class for MMEX Reader settings."""
    start_date: str = "2025-01-01"
    end_date: str = "2025-05-31"
    db_file_path: Optional[str] = None
    output_format: str = "console"
    max_sample_rows: int = 3
    show_schema: bool = True
    show_transactions: bool = True
    date_format: str = "%Y-%m-%d"
    
    VALID_OUTPUT_FORMATS = ('console', 'csv', 'json')
    
    def __post_init__(self) -> None:
        self.validate()
    
    def validate(self) -> None:
        self._validate_dates()
        self._validate_output_format()
        self._validate_sample_rows()
    
    def _validate_dates(self) -> None:
        if not is_valid_date_format(self.start_date, "start_date"):
            raise ValueError(f"Invalid start_date format: {self.start_date}")
        if not is_valid_date_format(self.end_date, "end_date"):
            raise ValueError(f"Invalid end_date format: {self.end_date}")
        if not is_valid_date_range(self.start_date, self.end_date):
            raise ValueError(f"Invalid date range")
    
    def _validate_output_format(self) -> None:
        if self.output_format not in self.VALID_OUTPUT_FORMATS:
            raise ValueError(f"Invalid output_format: {self.output_format}")
    
    def _validate_sample_rows(self) -> None:
        if self.max_sample_rows < 0:
            raise ValueError("max_sample_rows must be non-negative")
    
    @classmethod
    def from_env(cls) -> 'MMEXReaderConfig':
        try:
            return cls(
                start_date=os.getenv("MMEX_START_DATE", "2025-01-01"),
                end_date=os.getenv("MMEX_END_DATE", "2025-05-31"),
                db_file_path=os.getenv("DB_FILE_PATH"),
                output_format=os.getenv("MMEX_OUTPUT_FORMAT", "console"),
                max_sample_rows=int(os.getenv("MMEX_MAX_SAMPLE_ROWS", "3")),
                show_schema=os.getenv("MMEX_SHOW_SCHEMA", "true").lower() == "true",
                show_transactions=os.getenv("MMEX_SHOW_TRANSACTIONS", "true").lower() == "true"
            )
        except ValueError:
            return cls()
