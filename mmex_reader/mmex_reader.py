"""MMEX Database Reader Module - Step 1 Refactor.

This step migrates transaction query logic to db_queries.py.
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

import pandas as pd
from dotenv import load_dotenv

from mmex_reader.db_utils import _connection_pool, load_db_path
from mmex_reader.error_handling import handle_database_query, is_valid_date_format, is_valid_date_range
from mmex_reader.db_queries import get_transactions_by_date_range as db_get_transactions_by_date_range
from mmex_reader.db_queries import count_transactions_by_date_range as db_count_transactions_by_date_range

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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

class MMEXReader:
    """Main class for reading and analyzing MMEX database files."""
    
    def __init__(self, config: Optional[MMEXReaderConfig] = None):
        load_dotenv()
        self.config = config or MMEXReaderConfig.from_env()
        self.connection: Optional[sqlite3.Connection] = None
        self.is_connected: bool = False
        self._set_working_directory()
    
    def _set_working_directory(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
    
    def _validate_database_path(self) -> None:
        if not self.config.db_file_path:
            raise ValueError("Database file path not configured")
        if not os.path.exists(self.config.db_file_path):
            raise FileNotFoundError(f"Database file not found: {self.config.db_file_path}")
    
    def connect(self) -> bool:
        try:
            self._validate_database_path()
            load_db_path(self.config.db_file_path)
            self.connection = _connection_pool.get_connection()
            if not self.connection:
                raise sqlite3.Error("Could not get a database connection")
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Error connecting: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        if self.connection and self.is_connected:
            _connection_pool.release_connection(self.connection)
            self.connection = None
            self.is_connected = False
    
    def _ensure_connected(self) -> None:
        if not self.is_connected or not self.connection:
            raise RuntimeError("Not connected to database")
            
    def get_schema_info(self) -> Dict[str, List[str]]:
        self._ensure_connected()
        schema_info = {}
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                schema_info[table_name] = [column[1] for column in columns]
            return schema_info
        except sqlite3.Error:
            raise
            
    def get_database_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        self._ensure_connected()
        schema_info = {}
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table_row in tables:
                table_name = table_row[0]
                cursor.execute(f"PRAGMA table_info('{table_name}');")
                columns_info = cursor.fetchall()
                schema_info[table_name] = [
                    {'name': col[1], 'type': col[2], 'notnull': bool(col[3]), 
                     'default_value': col[4], 'primary_key': bool(col[5])}
                    for col in columns_info
                ]
            return schema_info
        except sqlite3.Error:
            raise
    
    def get_sample_data(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        self._ensure_connected()
        limit = limit or self.config.max_sample_rows
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            if not cursor.fetchone():
                raise ValueError(f"Table '{table_name}' does not exist")
            query = f"SELECT * FROM '{table_name}' LIMIT {limit};"
            error, df = handle_database_query(self.connection, query)
            return df if not error else pd.DataFrame()
        except Exception:
            raise
    
    def get_transactions_by_date_range(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        self._ensure_connected()
        start = start_date if start_date is not None else self.config.start_date
        end = end_date if end_date is not None else self.config.end_date
        return db_get_transactions_by_date_range(self.connection, start, end)

    def count_transactions_by_date_range(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> int:
        self._ensure_connected()
        start = start_date if start_date is not None else self.config.start_date
        end = end_date if end_date is not None else self.config.end_date
        return db_count_transactions_by_date_range(self.connection, start, end)
    
    def display_schema_info(self) -> None:
        self._ensure_connected()
        try:
            schema_info = self.get_database_schema()
            print("\n=== DATABASE SCHEMA ===")
            for table_name, columns in schema_info.items():
                print(f"\nTable: {table_name}")
                for col in columns:
                    print(f"  - {col['name']} ({col['type']})")
                sample_df = self.get_sample_data(table_name)
                if not sample_df.empty:
                    print(f"Sample rows: {len(sample_df)}")
        except Exception as e:
            print(f"Error: {e}")
    
    def display_transactions(self, df: Optional[pd.DataFrame] = None) -> None:
        if df is None:
            df = self.get_transactions_by_date_range()
        if df.empty:
            print("No transactions found.")
            return
        print("\n=== TRANSACTIONS ===")
        print(df)
    
    def export_data(self, data: pd.DataFrame, filename: Optional[str] = None) -> bool:
        if data.empty: return False
        try:
            if not filename:
                filename = f"mmex_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if self.config.output_format == 'csv':
                data.to_csv(f"{filename}.csv", index=False)
            elif self.config.output_format == 'json':
                data.to_json(f"{filename}.json", orient='records', indent=2)
            else:
                print(data.to_string(index=False))
            return True
        except Exception:
            return False
    
    def run_analysis(self) -> None:
        try:
            if not self.connect(): return
            if self.config.show_schema: self.display_schema_info()
            if self.config.show_transactions: self.display_transactions()
        finally:
            self.disconnect()

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start-date', default="2025-01-01")
    parser.add_argument('--end-date', default="2025-05-31")
    parser.add_argument('--db-path', default=os.getenv("DB_FILE_PATH"))
    args = parser.parse_args()
    try:
        config = MMEXReaderConfig(start_date=args.start_date, end_date=args.end_date, db_file_path=args.db_path)
        reader = MMEXReader(config)
        reader.run_analysis()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
