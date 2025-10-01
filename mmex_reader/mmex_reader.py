"""MMEX Database Reader Module.

This module provides a comprehensive interface for reading and analyzing MMEX database files.
It includes functionality for database schema exploration, transaction analysis, and data export.

Classes:
    MMEXReader: Main class for interacting with MMEX databases.
    MMEXReaderConfig: Configuration class for reader settings.

Functions:
    main: Entry point for command-line usage.
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

import pandas as pd
from dotenv import load_dotenv

from db_utils import _connection_pool, load_db_path
from error_handling import handle_database_query, validate_date_format, validate_date_range

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        if not validate_date_format(self.start_date, "start_date"):
            raise ValueError(f"Invalid start_date format: {self.start_date}. Expected format: {self.date_format}")
        
        # Validate end date format
        if not validate_date_format(self.end_date, "end_date"):
            raise ValueError(f"Invalid end_date format: {self.end_date}. Expected format: {self.date_format}")
        
        # Validate date range
        if not validate_date_range(self.start_date, self.end_date):
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

class MMEXReader:
    """Main class for reading and analyzing MMEX database files.
    
    This class provides a comprehensive interface for interacting with MMEX databases,
    including schema exploration, transaction analysis, and data export functionality.
    
    Attributes:
        config: Configuration settings for the reader.
        connection: Database connection object.
        is_connected: Flag indicating if database connection is active.
    """
    
    def __init__(self, config: Optional[MMEXReaderConfig] = None):
        """Initialize the MMEX Reader.
        
        Args:
            config: Configuration settings. If None, loads from environment.
        """
        # Load environment variables first to ensure they're available for config
        load_dotenv()
        
        # Initialize configuration
        self.config = config or MMEXReaderConfig.from_env()
        self.connection: Optional[sqlite3.Connection] = None
        self.is_connected: bool = False
        
        # Set up working directory to ensure relative paths work correctly
        self._set_working_directory()
        
        logger.info(f"MMEXReader initialized with config: {self.config}")
    
    def _set_working_directory(self) -> None:
        """Set the working directory to the script directory."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        logger.debug(f"Working directory set to: {script_dir}")
    
    def _validate_database_path(self) -> None:
        """Validate that the database file exists.
        
        Raises:
            ValueError: If database path is not configured.
            FileNotFoundError: If database file doesn't exist.
        """
        if not self.config.db_file_path:
            raise ValueError("Database file path not configured. Set DB_FILE_PATH in .env file.")
        
        if not os.path.exists(self.config.db_file_path):
            raise FileNotFoundError(f"Database file not found: {self.config.db_file_path}")
    
    def connect(self) -> bool:
        """Establish connection to the MMEX database.
        
        Returns:
            bool: True if connection successful, False otherwise.
            
        Raises:
            FileNotFoundError: If database file doesn't exist.
            sqlite3.Error: If database connection fails.
        """
        try:
            # Validate database path before attempting connection
            self._validate_database_path()
            
            # Initialize the connection pool
            load_db_path(self.config.db_file_path)
            
            # Get a connection from the pool
            self.connection = _connection_pool.get_connection()
            if not self.connection:
                raise sqlite3.Error("Could not get a database connection from the pool")
            
            self.is_connected = True
            logger.info(f"Successfully connected to {self.config.db_file_path}")
            return True
            
        except (ValueError, FileNotFoundError, sqlite3.Error) as e:
            # Log specific error types with appropriate messages
            logger.error(f"Error connecting to database: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error connecting to database: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Release the database connection back to the pool."""
        if self.connection and self.is_connected:
            _connection_pool.release_connection(self.connection)
            self.connection = None
            self.is_connected = False
            logger.info("Database connection released back to the pool")
    
    def get_schema_info(self) -> Dict[str, List[str]]:
        """Get schema information for all tables in the database.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping table names to column lists.
            
        Raises:
            RuntimeError: If not connected to database.
            sqlite3.Error: If a database error occurs.
        """
        self._ensure_connected()
        
        schema_info = {}
        try:
            cursor = self.connection.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Get columns for each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]
                schema_info[table_name] = column_names
                
            logger.debug(f"Retrieved schema info for {len(tables)} tables")
            return schema_info
            
        except sqlite3.Error as e:
            logger.error(f"SQLite error getting schema info: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting schema info: {e}")
            return {}
            
    def _ensure_connected(self) -> None:
        """Ensure database connection is established.
        
        Raises:
            RuntimeError: If not connected to database.
        """
        if not self.is_connected or not self.connection:
            raise RuntimeError("Not connected to database. Call connect() first.")
            
    def get_database_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve complete database schema information.
        
        Returns:
            Dict containing table names and their column information.
            
        Raises:
            RuntimeError: If not connected to database.
        """
        self._ensure_connected()
        
        schema_info = {}
        cursor = self.connection.cursor()
        
        try:
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            logger.info(f"Found {len(tables)} tables in database")
            
            for table_row in tables:
                table_name = table_row[0]
                
                # Get column information
                cursor.execute(f"PRAGMA table_info('{table_name}');")
                columns_info = cursor.fetchall()
                
                schema_info[table_name] = [
                    {
                        'name': col[1],
                        'type': col[2],
                        'notnull': bool(col[3]),
                        'default_value': col[4],
                        'primary_key': bool(col[5])
                    }
                    for col in columns_info
                ]
            
            return schema_info
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving database schema: {e}")
            raise
    
    def get_sample_data(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Get sample data from a specific table.
        
        Args:
            table_name: Name of the table to sample.
            limit: Maximum number of rows to return. Uses config default if None.
            
        Returns:
            DataFrame containing sample data.
            
        Raises:
            RuntimeError: If not connected to database.
            ValueError: If table_name is invalid.
        """
        self._ensure_connected()
        
        limit = limit or self.config.max_sample_rows
        
        try:
            # Validate table exists
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            if not cursor.fetchone():
                raise ValueError(f"Table '{table_name}' does not exist in the database")
            
            query = f"SELECT * FROM '{table_name}' LIMIT {limit};"
            error, df = handle_database_query(self.connection, query)
            
            if error:
                logger.error(f"Error getting sample data from {table_name}: {error}")
                return pd.DataFrame()
            
            logger.info(f"Retrieved {len(df)} sample rows from {table_name}")
            return df
            
        except (sqlite3.Error, ValueError) as e:
            logger.error(f"Error getting sample data from {table_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting sample data from {table_name}: {e}")
            return pd.DataFrame()
    
    def get_transactions_by_date_range(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get transactions within a specified date range.
        
        Args:
            start_date: Start date for transaction range (inclusive).
                        If None, uses config.start_date.
            end_date: End date for transaction range (inclusive).
                      If None, uses config.end_date.
                      
        Returns:
            pd.DataFrame: DataFrame containing transaction data.
            
        Raises:
            RuntimeError: If not connected to database.
        """
        self._ensure_connected()
        
        # Use configured dates if none provided
        start = start_date if start_date is not None else self.config.start_date
        end = end_date if end_date is not None else self.config.end_date
        
        query = """
            SELECT 
                CHECKINGACCOUNT_V1.TRANSDATE AS Date,
                CHECKINGACCOUNT_V1.TRANSCODE AS Type,
                CATEGORY_V1.CATEGNAME AS Category,
                SUBCATEGORY_V1.SUBCATEGNAME AS Subcategory,
                CHECKINGACCOUNT_V1.TRANSAMOUNT AS Amount,
                CHECKINGACCOUNT_V1.NOTES AS Notes,
                PAYEE_V1.PAYEENAME AS Payee,
                ACCOUNTLIST_V1.ACCOUNTNAME AS Account
            FROM CHECKINGACCOUNT_V1
            LEFT JOIN CATEGORY_V1 ON CHECKINGACCOUNT_V1.CATEGID = CATEGORY_V1.CATEGID
            LEFT JOIN SUBCATEGORY_V1 ON CHECKINGACCOUNT_V1.SUBCATEGID = SUBCATEGORY_V1.SUBCATEGID
            LEFT JOIN PAYEE_V1 ON CHECKINGACCOUNT_V1.PAYEEID = PAYEE_V1.PAYEEID
            LEFT JOIN ACCOUNTLIST_V1 ON CHECKINGACCOUNT_V1.ACCOUNTID = ACCOUNTLIST_V1.ACCOUNTID
            WHERE CHECKINGACCOUNT_V1.TRANSDATE BETWEEN ? AND ?
            ORDER BY CHECKINGACCOUNT_V1.TRANSDATE DESC
        """
        
        try:
            error, df = handle_database_query(self.connection, query, params=(start, end))
            
            if error:
                logger.error(f"Error retrieving transactions: {error}")
                return pd.DataFrame()
                
            # Convert date strings to datetime objects
            if not df.empty and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                
            logger.info(f"Retrieved {len(df)} transactions between {start} and {end}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting transactions by date range: {e}")
            return pd.DataFrame()
    
    def display_schema_info(self) -> None:
        """Display database schema information in a formatted table."""
        self._ensure_connected()
        
        try:
            schema_info = self.get_database_schema()
            
            print("\n=== DATABASE SCHEMA ===")
            if not schema_info:
                print("No tables found in the database.")
                return
            
            print(f"Found {len(schema_info)} tables. Details below:")
            
            for table_name, columns in schema_info.items():
                print(f"\nTable: {table_name}")
                print("-" * (len(table_name) + 7))
                
                if columns:
                    print("Columns (name, type, notnull, default_value, pk):")
                    for col in columns:
                        null_str = 'NOT NULL' if col['notnull'] else 'NULL'
                        print(f"  - {col['name']} ({col['type']}, {null_str}, "
                              f"Default: {col['default_value']}, PK: {col['primary_key']})")
                else:
                    print("  No column information found for this table.")
                
                # Display sample data
                sample_df = self.get_sample_data(table_name)
                if not sample_df.empty:
                    print(f"Sample rows (first {len(sample_df)} rows):")
                    for idx, row in sample_df.iterrows():
                        print(f"  Row {idx + 1}: {dict(row)}")
                else:
                    print("  No data in this table or table is empty.")
            
            logger.info("Schema information displayed successfully")
            
        except Exception as e:
            logger.error(f"Error displaying schema info: {e}")
            print(f"Error displaying schema info: {e}")
    
    def display_transactions(self, df: Optional[pd.DataFrame] = None) -> None:
        """Display transaction data in a formatted table.
        
        Args:
            df: DataFrame containing transaction data.
                If None, retrieves transactions using get_transactions_by_date_range().
        """
        try:
            # Get transactions if not provided
            if df is None:
                df = self.get_transactions_by_date_range()
                
            if df.empty:
                print("No transactions found for the specified date range.")
                return
                
            # Format the display
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            pd.set_option('display.colheader_justify', 'center')
            
            print("\n=== TRANSACTIONS ===")
            print(df)
            print(f"\nTotal transactions: {len(df)}")
            
            logger.info(f"Displayed {len(df)} transactions")
            
        except Exception as e:
            logger.error(f"Error displaying transactions: {e}")
            print(f"Error displaying transactions: {e}")
    
    def export_data(self, data: pd.DataFrame, filename: Optional[str] = None) -> bool:
        """Export data to file based on configured output format.
        
        Args:
            data: DataFrame to export.
            filename: Base filename (without extension). If None, generates a name based on config.
            
        Returns:
            bool: True if export successful, False otherwise.
        """
        if data.empty:
            logger.warning("Cannot export empty DataFrame")
            return False
            
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"mmex_export_{timestamp}"
                
            if self.config.output_format == 'csv':
                filepath = f"{filename}.csv"
                data.to_csv(filepath, index=False)
                logger.info(f"Data exported to {filepath}")
                
            elif self.config.output_format == 'json':
                filepath = f"{filename}.json"
                data.to_json(filepath, orient='records', indent=2)
                logger.info(f"Data exported to {filepath}")
                
            else:  # console output
                print(data.to_string(index=False))
                logger.info("Data displayed to console")
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
    
    def run_analysis(self) -> None:
        """Run complete database analysis based on configuration."""
        try:
            if not self.connect():
                print("Failed to connect to database. Exiting.")
                return
            
            if self.config.show_schema:
                self.display_schema_info()
            
            if self.config.show_transactions:
                self.display_transactions()
                
                # Export transactions if format is not console
                if self.config.output_format != 'console':
                    transactions_df = self.get_transactions_by_date_range()
                    if not transactions_df.empty:
                        self.export_data(transactions_df, f"transactions_{self.config.start_date}_to_{self.config.end_date}")
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            print(f"Error during analysis: {e}")
        
        finally:
            self.disconnect()


def main() -> None:
    """Main entry point for command-line usage."""
    try:
        # Create configuration from environment
        config = MMEXReaderConfig.from_env()
        
        # Validate database file path
        if not config.db_file_path:
            print("Error: DB_FILE_PATH not found in .env file or environment variables.")
            return
        
        # Create and run reader
        reader = MMEXReader(config)
        reader.run_analysis()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
