"""Database utility functions for the MMEX Kivy application.

This module provides functions for interacting with the MMEX SQLite database,
including loading the database path, retrieving accounts and transactions,
and calculating account balances.
"""

import os
import sqlite3
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# MMEX database schema constants
CHECKING_ACCOUNT_TYPE = "'Checking Account'"
TERMDEPOSIT_ACCOUNT_TYPE = "'Term Deposit'"
INVESTMENT_ACCOUNT_TYPE = "'Investment Account'"
STOCK_ACCOUNT_TYPE = "'Stock'"
MONEY_ACCOUNT_TYPE = "'Money'"
CREDIT_CARD_ACCOUNT_TYPE = "'Credit Card'"
LOAN_ACCOUNT_TYPE = "'Loan'"
ASSET_ACCOUNT_TYPE = "'Asset'"

CATEGORY_TABLE = "CATEGORY_V1"
SUBCATEGORY_TABLE = "SUBCATEGORY_V1"
ACCOUNT_TABLE = "ACCOUNTLIST_V1"
TRANSACTION_TABLE = "CHECKINGACCOUNT_V1"
PAYEE_TABLE = "PAYEE_V1"
TAG_TABLE = "TAG_V1"
TAGLINK_TABLE = "TAGLINK_V1"


def load_db_path():
    """Load the MMEX database path from the .env file or use a default path.

    Returns:
        str: Path to the MMEX database file

    Raises:
        FileNotFoundError: If the database file doesn't exist at the specified or default path
    """
    try:
        load_dotenv()
        db_path = os.getenv("MMEX_DB_PATH")

        if not db_path:
            # Default path if not specified in .env
            db_path = os.path.join(
                os.path.expanduser("~"), "Documents", "MoneyManagerEx", "data.mmb"
            )

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")

        return db_path

    except Exception as e:
        print(f"Error loading database path: {e}")
        raise


def get_all_accounts(db_path):
    """Get all accounts from the MMEX database.

    Args:
        db_path (str): Path to the MMEX database file

    Returns:
        tuple: (error_message, accounts_dataframe)
            - error_message (str or None): Error message if any, None if successful
            - accounts_dataframe (DataFrame): DataFrame containing account information
    """
    if not db_path or not os.path.exists(db_path):
        return "Database file not found", pd.DataFrame()

    try:
        with sqlite3.connect(db_path) as conn:
            query = f"SELECT ACCOUNTID, ACCOUNTNAME, ACCOUNTTYPE, INITIALBAL, STATUS FROM {ACCOUNT_TABLE}"
            accounts_df = pd.read_sql_query(query, conn)
            return None, accounts_df
    except sqlite3.Error as e:
        return f"Database error: {e}", pd.DataFrame()
    except Exception as e:
        return f"Unexpected error: {e}", pd.DataFrame()


def get_transactions(db_path, start_date_str=None, end_date_str=None, account_id=None):
    """Get transactions from the MMEX database.

    Args:
        db_path (str): Path to the MMEX database file
        start_date_str (str, optional): Start date string in YYYY-MM-DD format
        end_date_str (str, optional): End date string in YYYY-MM-DD format
        account_id (int, optional): Account ID to filter transactions

    Returns:
        tuple: (error_message, transactions_dataframe)
            - error_message (str or None): Error message if any, None if successful
            - transactions_dataframe (DataFrame): DataFrame containing transaction information
    """
    if not db_path or not os.path.exists(db_path):
        return "Database file not found", pd.DataFrame()

    # Validate date strings
    start_date = None
    end_date = None

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        except ValueError:
            return f"Invalid start date format: {start_date_str}", pd.DataFrame()

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            return f"Invalid end date format: {end_date_str}", pd.DataFrame()

    if start_date and end_date and start_date > end_date:
        return "Start date cannot be after end date", pd.DataFrame()

    try:
        with sqlite3.connect(db_path) as conn:
            # Base query
            query = f"""
            SELECT t.TRANSID, t.ACCOUNTID, t.TRANSCODE, t.TRANSAMOUNT, 
                   t.TRANSACTIONNUMBER, t.NOTES, t.TRANSDATE, t.FOLLOWUPID, 
                   t.TOTRANSAMOUNT, t.TOSPLITCATEGORY, t.CATEGID, t.SUBCATEGID, 
                   t.TRANSACTIONDATE, t.DELETEDTIME, t.PAYEEID,
                   a.ACCOUNTNAME, c.CATEGNAME, s.SUBCATEGNAME, p.PAYEENAME
            FROM {TRANSACTION_TABLE} t
            LEFT JOIN {ACCOUNT_TABLE} a ON t.ACCOUNTID = a.ACCOUNTID
            LEFT JOIN {CATEGORY_TABLE} c ON t.CATEGID = c.CATEGID
            LEFT JOIN {SUBCATEGORY_TABLE} s ON t.SUBCATEGID = s.SUBCATEGID
            LEFT JOIN {PAYEE_TABLE} p ON t.PAYEEID = p.PAYEEID
            WHERE t.DELETEDTIME = ''
            """

            # Add filters
            params = []
            if account_id is not None:
                query += " AND t.ACCOUNTID = ?"
                params.append(account_id)

            if start_date:
                query += " AND t.TRANSDATE >= ?"
                params.append(start_date.strftime("%Y-%m-%d"))

            if end_date:
                query += " AND t.TRANSDATE <= ?"
                params.append(end_date.strftime("%Y-%m-%d"))

            query += " ORDER BY t.TRANSDATE DESC"

            # Execute query
            transactions_df = pd.read_sql_query(query, conn, params=params)

            # Add tags column
            transactions_df["TAGS"] = ""

            # Get tags for each transaction
            for idx, row in transactions_df.iterrows():
                tag_query = f"""
                SELECT t.TAGNAME 
                FROM {TAG_TABLE} t
                JOIN {TAGLINK_TABLE} tl ON t.TAGID = tl.TAGID
                WHERE tl.REFID = ? AND tl.REFTYPE = 'Transaction'
                """
                tags_df = pd.read_sql_query(tag_query, conn, params=[row["TRANSID"]])
                if not tags_df.empty:
                    transactions_df.at[idx, "TAGS"] = ", ".join(
                        tags_df["TAGNAME"].tolist()
                    )

            return None, transactions_df

    except sqlite3.Error as e:
        return f"Database error: {e}", pd.DataFrame()
    except Exception as e:
        return f"Unexpected error: {e}", pd.DataFrame()


def calculate_balance_for_account(db_path, account_id, date=None):
    """Calculate the balance for a specific account up to a given date.

    Args:
        db_path: Path to the MMEX database file
        account_id: Account ID to calculate balance for
        date: Optional date to calculate balance up to

    Returns:
        tuple: (error_message, balance) where error_message is None on success
    """
    # Validate inputs
    if not db_path or not os.path.exists(db_path):
        return "Database file does not exist", None

    if not account_id:
        return "Account ID is required", None

    try:
        with sqlite3.connect(db_path) as conn:
            # Get account initial balance
            query = f"SELECT INITIALBAL FROM {ACCOUNT_TABLE} WHERE ACCOUNTID = ?"
            cursor = conn.cursor()
            cursor.execute(query, (account_id,))
            result = cursor.fetchone()

            if not result:
                return f"Account with ID {account_id} not found", None

            initial_balance = result[0] or 0

            # Get all transactions for this account up to the specified date
            query = f"""
            SELECT TRANSCODE, TRANSAMOUNT 
            FROM {TRANSACTION_TABLE} 
            WHERE ACCOUNTID = ? AND DELETEDTIME = ''
            """

            params = [account_id]

            if date:
                query += " AND TRANSDATE <= ?"
                params.append(date.strftime("%Y-%m-%d"))

            cursor.execute(query, params)
            transactions = cursor.fetchall()

            # Calculate balance
            balance = initial_balance
            for trans_type, amount in transactions:
                if trans_type == "Withdrawal":
                    balance -= amount
                elif trans_type == "Deposit":
                    balance += amount
                # Handle transfers if needed

            return None, balance
    except sqlite3.Error as e:
        return f"Database error: {e}", None
    except Exception as e:
        return f"Unexpected error calculating balance: {e}", None
