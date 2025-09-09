import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime  # Import datetime
from db_utils import _connection_pool, load_db_path

# get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# change the working directory to the script directory
os.chdir(script_dir)

# Load environment variables from .env file
load_dotenv()

# --- Define Date Range --- Start
# You can modify the start and end dates here
# Date format: YYYY-MM-DD
START_DATE_STR = "2025-01-01"  # Example: Set start date
END_DATE_STR = "2025-05-31"  # Example: Set end date

# Validate date format (optional, but recommended)
try:
    datetime.strptime(START_DATE_STR, "%Y-%m-%d")
    datetime.strptime(END_DATE_STR, "%Y-%m-%d")
except ValueError:
    print(
        f"Error: Incorrect date format. Please use YYYY-MM-DD. Start date: {START_DATE_STR}, End date: {END_DATE_STR}"
    )
    exit()
# --- Define Date Range --- End

# Path to .mmb file, read from environment variable
db_file = os.getenv("DB_FILE_PATH")

if not db_file:
    print("Error: DB_FILE_PATH not found in .env file or environment variables.")
    exit()

try:
    # Initialize the connection pool with the database file
    # Note: If the .mmb file is encrypted (.emb), connecting directly with
    # sqlite3 will fail.
    # This is because the sqlite3 module does not support AES encryption. You
    # need to decrypt it first in MMEX or use other tools.
    load_db_path(db_file)
    
    # Get a connection from the pool
    conn = _connection_pool.get_connection()
    if not conn:
        print("Error: Could not get a database connection from the pool.")
        exit()
    cursor = conn.cursor()

    print(f"Successfully connected to {db_file}")

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\n--- Database Schema and Sample Data ---")
    if not tables:
        print("No tables found in the database.")
    else:
        print(f"Found {len(tables)} tables. Details below:")
        for table_row in tables:
            table_name = table_row[0]
            print(f"\n--- Table: {table_name} ---")

            # Get column information using PRAGMA table_info
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns_info = cursor.fetchall()
            if columns_info:
                print("Columns (name, type, notnull, default_value, pk):")
                for col in columns_info:
                    # col: (cid, name, type, notnull, dflt_value, pk)
                    print(f"  - {col[1]} ({col[2]}, {'NOT NULL' if col[3] else 'NULL'}, Default: {col[4]}, PK: {col[5]})")
            else:
                print("  No column information found for this table.")

            # Get a few sample rows
            try:
                cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 3;")
                sample_column_names = [description[0] for description in cursor.description]
                sample_rows = cursor.fetchall()
                if sample_rows:
                    print(f"Sample rows (first 3 rows, columns: {', '.join(sample_column_names)}):")
                    for row_idx, row_data in enumerate(sample_rows):
                        print(f"  Row {row_idx + 1}: {row_data}")
                else:
                    print("  No data in this table or table is empty.")
            except sqlite3.OperationalError as e_select:
                print(f"  Could not fetch sample rows: {e_select}")
    print("\n-------------------------------------------")

    # --- ADDED: Read, filter, and print income/expense records for the specified date range by time series --- Start
    print(f"\n--- Income/Expense records from {START_DATE_STR} to {END_DATE_STR} ---")
    try:
        # Assume date column is TRANSDATE, and amount column is TRANSAMOUNT
        # Assume CHECKINGACCOUNT_V1 has a CATEGID column to link to CATEGORY_V1
        query_transactions_by_date = f"""
            SELECT 
                ACCOUNTLIST_V1.ACCOUNTNAME, 
                CHECKINGACCOUNT_V1.TRANSDATE, 
                CHECKINGACCOUNT_V1.NOTES, 
                CHECKINGACCOUNT_V1.TRANSAMOUNT, 
                PAYEE_V1.PAYEENAME,
                CATEGORY_V1.CATEGNAME
            FROM CHECKINGACCOUNT_V1
            LEFT JOIN ACCOUNTLIST_V1 ON CHECKINGACCOUNT_V1.ACCOUNTID = ACCOUNTLIST_V1.ACCOUNTID
            LEFT JOIN PAYEE_V1 ON CHECKINGACCOUNT_V1.PAYEEID = PAYEE_V1.PAYEEID
            LEFT JOIN CATEGORY_V1 ON CHECKINGACCOUNT_V1.CATEGID = CATEGORY_V1.CATEGID  -- Assume CHECKINGACCOUNT_V1.CATEGID exists
            WHERE CHECKINGACCOUNT_V1.TRANSDATE BETWEEN '{START_DATE_STR}' AND '{END_DATE_STR}'
            ORDER BY CHECKINGACCOUNT_V1.TRANSDATE ASC, CHECKINGACCOUNT_V1.TRANSID ASC;
        """

        dated_transactions_df = pd.read_sql_query(query_transactions_by_date, conn)

        if not dated_transactions_df.empty:
            print(
                f"Found {len(dated_transactions_df)} records between {START_DATE_STR} and {END_DATE_STR}:"
            )
            for index, row in dated_transactions_df.iterrows():
                # Added category name to the output
                print(
                    f"{row['TRANSDATE']} | {row['ACCOUNTNAME']:<15} | {row['PAYEENAME'] if row['PAYEENAME'] else '':<20} | {row['CATEGNAME'] if row['CATEGNAME'] else '':<25} | {row['NOTES'] if row['NOTES'] else '':<30} | {row['TRANSAMOUNT']}"
                )
        else:
            print(
                f"No income/expense records found between {START_DATE_STR} and {END_DATE_STR}."
            )

    except pd.io.sql.DatabaseError as e:
        print(f"Error reading transaction records for the specified date range: {e}")
    except Exception as e:
        print(
            f"Error when querying transaction records for the specified date range: {e}. Please check SQL syntax and table/column names."
        )
    # --- ADDED: Read, filter, and print income/expense records for the specified date range by time series --- End

except Exception as e:
    print(f"Error connecting to database: {e}")
finally:
    # Release the connection back to the pool
    if 'conn' in locals() and conn:
        _connection_pool.release_connection(conn)
        print(f"\nConnection to {db_file} has been released back to the pool.")
