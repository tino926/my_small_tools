import sqlite3
import pandas as pd  # Recommended to use pandas for convenient table data processing
import os
from dotenv import load_dotenv

# get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# change the working directory to the script directory
os.chdir(script_dir)

# Load environment variables from .env file
load_dotenv()

# Path to .mmb file, read from environment variable
db_file = os.getenv("DB_FILE_PATH")

if not db_file:
    print("Error: DB_FILE_PATH not found in .env file or environment variables.")
    exit()

try:
    # Establish connection to the database
    # Note: If the .mmb file is encrypted (.emb), connecting directly with 
    # sqlite3 will fail.
    # This is because the sqlite3 module does not support AES encryption. You 
    # need to decrypt it first in MMEX or use other tools.
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    print(f"Successfully connected to {db_file}")

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\nTables in the database:")
    for table in tables:
        print(f"- {table[0]}")

    # -----------------------------------------------------------
    # Example: Read all data from 'ACCOUNTS' table
    print("\n--- Data examples from ACCOUNTLIST_V1 table ---") # Updated print statement
    try:
        cursor.execute("SELECT * FROM ACCOUNTLIST_V1;") # Changed ACCOUNTS to ACCOUNTLIST_V1
        # Get column names
        column_names = [description[0] for description in cursor.description]
        print(f"Columns: {column_names}")

        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(row)
        else:
            print("No data in ACCOUNTLIST_V1 table.") # Updated print statement
    except sqlite3.OperationalError as e:
        print(f"Unable to read ACCOUNTLIST_V1 table: {e}") # Updated print statement
    # -----------------------------------------------------------

    # -----------------------------------------------------------
    # Example: Use pandas to read 'TRANSACTIONS' table (usually what you're most 
    # interested in)
    print("\n--- Data examples from CHECKINGACCOUNT_V1 table (using pandas) ---") # Updated print statement
    try:
        # Using pandas' read_sql_query is more convenient
        transactions_df = pd.read_sql_query("SELECT * FROM CHECKINGACCOUNT_V1;", conn) # Changed TRANSACTIONS
        if not transactions_df.empty:
            print(transactions_df.head())  # Display first few rows
            print(f"\nCHECKINGACCOUNT_V1 table has {len(transactions_df)} records.") # Updated print statement
        else:
            print("No data in CHECKINGACCOUNT_V1 table.") # Updated print statement
    except pd.io.sql.DatabaseError as e:
        print(f"Unable to read CHECKINGACCOUNT_V1 table using pandas: {e}") # Updated print statement
    # -----------------------------------------------------------

    # -----------------------------------------------------------
    # Example: Read transaction records for a specific account (assuming you 
    # know the account name and ID)
    # First, let's find an account ID for an account named 'Cash'
    print("\n--- Query transaction records for a specific account ---")
    try:
        cursor.execute(
            "SELECT ACCOUNTID, ACCOUNTNAME FROM ACCOUNTLIST_V1 WHERE ACCOUNTNAME = '現金';" # Changed 'Cash' to '現金'
        )
        cash_account = cursor.fetchone()

        if cash_account:
            cash_account_id = cash_account[0]
            cash_account_name = cash_account[1]
            print(f"Found account '{cash_account_name}' (ID: {cash_account_id})")

            # Query all transactions for this account
            transactions_for_cash_df = pd.read_sql_query(
                f"SELECT * FROM CHECKINGACCOUNT_V1 WHERE ACCOUNTID = {cash_account_id};", conn # Changed TRANSACTIONS
            )
            if not transactions_for_cash_df.empty:
                print(
                    f"\nTransaction records for account '{cash_account_name}' (first few rows):"
                )
                print(transactions_for_cash_df.head())
            else:
                print(f"Account '{cash_account_name}' has no transaction records.")
        else:
            print("Could not find an account named 'Cash'.")
    except sqlite3.OperationalError as e:
        print(f"Error occurred when querying specific account transactions: {e}")
    # -----------------------------------------------------------

except sqlite3.Error as e:
    print(f"Error connecting to database: {e}")

finally:
    # Ensure connection is closed
    if "conn" in locals() and conn:
        conn.close()
        print(f"\nConnection to {db_file} has been closed.")
