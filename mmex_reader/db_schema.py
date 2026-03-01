"""Database schema constants for the MMEX application."""

from typing import Dict

# MMEX database schema constants - Table names
CATEGORY_TABLE: str = "CATEGORY_V1"
SUBCATEGORY_TABLE: str = "SUBCATEGORY_V1"
ACCOUNT_TABLE: str = "ACCOUNTLIST_V1"
TRANSACTION_TABLE: str = "CHECKINGACCOUNT_V1"
PAYEE_TABLE: str = "PAYEE_V1"
TAG_TABLE: str = "TAG_V1"
TAGLINK_TABLE: str = "TAGLINK_V1"

# MMEX database schema constants - Account table columns
ACCOUNT_COLS: Dict[str, str] = {
    "id": "ACCOUNTID",
    "name": "ACCOUNTNAME",
    "type": "ACCOUNTTYPE",
    "initial_balance": "INITIALBAL",
    "is_favorite": "FAVORITEACCT",
    "currency_id": "CURRENCYID",
    "status": "STATUS",
    "notes": "NOTES",
    "held_at": "HELDAT",
    "website": "WEBSITE",
    "contact_info": "CONTACTINFO",
    "access_info": "ACCESSINFO",
    "statement_locked": "STATEMENTLOCKED",
    "statement_date": "STATEMENTDATE",
    "min_balance": "MINIMUMBALANCE",
    "credit_limit": "CREDITLIMIT",
    "interest_rate": "INTERESTRATE",
    "payment_due_date": "PAYMENTDUEDATE",
    "min_payment": "MINIMUMPAYMENT"
}
