"""MMEX Database Reader Module - Entry Point.

This script serves as the main entry point for the MMEX Reader analysis.
It parses command-line arguments, initializes the configuration, and runs the analysis.
"""

import argparse
import logging
import os

from mmex_reader.reader_config import MMEXReaderConfig
from mmex_reader.reader_main import MMEXReader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main() -> None:
    """Main function to run the MMEX analysis."""
    parser = argparse.ArgumentParser(description="MMEX Database Reader and Analyzer.")
    parser.add_argument('--start-date', default=os.getenv("MMEX_START_DATE", "2025-01-01"), help="Start date for transaction analysis (YYYY-MM-DD).")
    parser.add_argument('--end-date', default=os.getenv("MMEX_END_DATE", "2025-05-31"), help="End date for transaction analysis (YYYY-MM-DD).")
    parser.add_argument('--db-path', default=os.getenv("DB_FILE_PATH"), help="Path to the MMEX database file.")
    parser.add_argument('--output', default=os.getenv("MMEX_OUTPUT_FORMAT", "console"), choices=MMEXReaderConfig.VALID_OUTPUT_FORMATS, help="Output format.")
    
    args = parser.parse_args()
    
    try:
        config = MMEXReaderConfig(
            start_date=args.start_date,
            end_date=args.end_date,
            db_file_path=args.db_path,
            output_format=args.output
        )
        reader = MMEXReader(config)
        reader.run_analysis()
    except (ValueError, FileNotFoundError) as e:
        logging.error(f"Configuration or file error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
