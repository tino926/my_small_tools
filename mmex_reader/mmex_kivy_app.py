"""
A Kivy application for reading and displaying financial transactions
from an MMEX (MoneyManagerEx) database file.
"""

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window

# from kivy.uix.spinner import Spinner # Spinner not actively used currently
from kivy.uix.tabbedpanel import (
    TabbedPanel,
    TabbedPanelHeader,
)
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.widget import Widget  # For spacer
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle # Added for custom background
import os

import sqlite3
import pandas as pd

from dotenv import load_dotenv
from datetime import datetime
from datetime import timedelta

kivy.require("2.1.0")  # replace with your Kivy version if needed


# --- Script Directory ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Font Configuration ---
# Path to the Unicode font file. Ensure this font supports characters in your database.
UNICODE_FONT_PATH = "fonts/NotoSansCJKtc-Regular.otf"

# --- MMEX Database Schema Configuration ---
DB_TABLE_TRANSACTIONS = "CHECKINGACCOUNT_V1"
DB_TABLE_ACCOUNTS = "ACCOUNTLIST_V1"
DB_TABLE_PAYEES = "PAYEE_V1"
DB_TABLE_CATEGORIES = "CATEGORY_V1"
DB_FIELD_TRANS_ID = "TRANSID"
DB_FIELD_TRANS_DATE = "TRANSDATE"
DB_FIELD_TRANS_NOTES = "NOTES"
DB_FIELD_TRANS_AMOUNT = "TRANSAMOUNT"
DB_FIELD_TRANS_ACCOUNTID_FK = "ACCOUNTID"
DB_FIELD_TRANS_PAYEEID_FK = "PAYEEID"
DB_FIELD_TRANS_CATEGID_FK = "CATEGID"
DB_FIELD_ACCOUNT_ID_PK = "ACCOUNTID"
DB_FIELD_ACCOUNT_NAME = "ACCOUNTNAME"
DB_FIELD_ACCOUNT_INITIAL_BALANCE = "INITIALBAL"  # Initial balance for an account
DB_FIELD_PAYEE_ID_PK = "PAYEEID"
DB_FIELD_PAYEE_NAME = "PAYEENAME"
DB_FIELD_CATEGORY_ID_PK = "CATEGID"
DB_FIELD_CATEGORY_NAME = "CATEGNAME"
DB_TABLE_TAGS = "TAG_V1"  # Confirmed table name for tags
DB_TABLE_TRANSACTION_TAGS = (
    "TAGLINK_V1"  # Confirmed linking table for transactions and tags
)
DB_FIELD_TAG_ID_PK = "TAGID"
DB_FIELD_TAG_NAME = "TAGNAME"
DB_FIELD_TRANSTAG_TRANSID_FK = "REFID"  # FK in TAGLINK_V1 to CHECKINGACCOUNT_V1.TRANSID
DB_FIELD_TRANSTAG_TAGID_FK = "TAGID"  # FK in TAGLINK_V1 to TAG_V1.TAGID

# --- UI Color Constants ---
DEFAULT_TEXT_COLOR_ON_LIGHT_BG = (0, 0, 0, 1)  # Black text for light backgrounds
DEFAULT_TEXT_COLOR_ON_DARK_BG = (1, 1, 1, 1)   # White text for dark backgrounds
GRID_BACKGROUND_GREEN = (0.95, 0.95, 0.95, 1) # A moderately dark green for grid backgrounds


# --- Database Functions ---
def load_db_path():
    env_path = os.path.join(SCRIPT_DIR, ".env")
    load_dotenv(dotenv_path=env_path, override=True)
    db_file = os.getenv("DB_FILE_PATH")
    return db_file


def get_all_accounts(db_file):
    """Fetches all account names and IDs from the MMEX database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        query = (
            f"SELECT {DB_FIELD_ACCOUNT_ID_PK} AS ACCOUNTID, "
            f"{DB_FIELD_ACCOUNT_NAME} AS ACCOUNTNAME, "
            f"{DB_FIELD_ACCOUNT_INITIAL_BALANCE} AS INITIALBAL "
            f"FROM {DB_TABLE_ACCOUNTS} ORDER BY {DB_FIELD_ACCOUNT_NAME} ASC;"
        )
        df = pd.read_sql_query(query, conn)
        if df.empty:
            return "No accounts found.", None
        return None, df
    except sqlite3.Error as e:
        return f"Database Error fetching accounts: {e}", None
    except Exception as e:
        return f"An unexpected error occurred fetching accounts: {e}", None
    finally:
        if conn:
            conn.close()


def get_transactions(db_file, start_date_str, end_date_str, account_id=None):
    """
    Fetches transactions from the MMEX database within a given date range,
    optionally filtered by account_id.
    """
    try:
        datetime.strptime(start_date_str, "%Y-%m-%d")
        datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return (
            f"Error: Incorrect date format. Please use YYYY-MM-DD. "
            f"Start: {start_date_str}, End: {end_date_str}",
            None,
        )
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        query_parts = [
            f"SELECT acc.{DB_FIELD_ACCOUNT_NAME} AS ACCOUNTNAME,",
            f"trans.{DB_FIELD_TRANS_DATE} AS TRANSDATE,",
            f"trans.{DB_FIELD_TRANS_NOTES} AS NOTES,",
            f"trans.{DB_FIELD_TRANS_AMOUNT} AS TRANSAMOUNT,",
            f"payee.{DB_FIELD_PAYEE_NAME} AS PAYEENAME,",
            f"trans.{DB_FIELD_TRANS_ACCOUNTID_FK} AS TRANSACTION_ACCOUNTID,", # Added for robust filtering
            f"cat.{DB_FIELD_CATEGORY_NAME} AS CATEGNAME,",
            # Subquery to concatenate all tags for a transaction
            f"""(
                SELECT GROUP_CONCAT(tag.{DB_FIELD_TAG_NAME}, ', ')
                FROM {DB_TABLE_TAGS} AS tag
                JOIN {DB_TABLE_TRANSACTION_TAGS} AS tt ON tag.{DB_FIELD_TAG_ID_PK} = tt.{DB_FIELD_TRANSTAG_TAGID_FK}
                WHERE tt.{DB_FIELD_TRANSTAG_TRANSID_FK} = trans.{DB_FIELD_TRANS_ID} AND tt.REFTYPE = 'Transaction'
            ) AS TAGNAMES""",
            f"FROM {DB_TABLE_TRANSACTIONS} AS trans",
            f"LEFT JOIN {DB_TABLE_ACCOUNTS} AS acc ON trans.{DB_FIELD_TRANS_ACCOUNTID_FK} = acc.{DB_FIELD_ACCOUNT_ID_PK}",
            f"LEFT JOIN {DB_TABLE_PAYEES} AS payee ON trans.{DB_FIELD_TRANS_PAYEEID_FK} = payee.{DB_FIELD_PAYEE_ID_PK}",
            f"LEFT JOIN {DB_TABLE_CATEGORIES} AS cat ON trans.{DB_FIELD_TRANS_CATEGID_FK} = cat.{DB_FIELD_CATEGORY_ID_PK}",
            f"WHERE trans.{DB_FIELD_TRANS_DATE} < ? AND trans.{DB_FIELD_TRANS_DATE} >= ?",  # Corrected date range logic
        ]
        end_date_str_p1 = (
            datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        # Correct order for params based on the SQL:
        # SQL: ... trans.TRANSDATE < ? (upper bound, end_date_str_p1)
        #          AND trans.TRANSDATE >= ? (lower bound, start_date_str) ...
        params = [end_date_str_p1, start_date_str]
        if (
            account_id is not None
        ):  # Add condition to filter by account ID in the SQL query if provided.
            query_parts.append(f"AND trans.{DB_FIELD_TRANS_ACCOUNTID_FK} = ?")  # type: ignore
            params.append(account_id)
        query_parts.append(
            f"ORDER BY trans.{DB_FIELD_TRANS_DATE} ASC, trans.{DB_FIELD_TRANS_ID} ASC;"
        )
        query = " ".join(query_parts)
        df = pd.read_sql_query(query, conn, params=tuple(params))
        if df.empty:
            return (
                f"No income/expense records found between {start_date_str} "
                f"and {end_date_str}"
                + (f" for account ID {account_id}" if account_id else "")
                + ".",
                None,
            )
        return None, df
    except sqlite3.Error as e:
        return f"Database Error: {e}", None
    except pd.io.sql.DatabaseError as e:
        return f"Pandas SQL Error: {e}", None
    except Exception as e:
        return f"An unexpected error occurred: {e}", None
    finally:
        if conn:
            conn.close()


def get_balance_as_of_date(db_file, account_id, initial_balance, end_date_str):
    """
    Calculates the balance for an account as of a specific end date.
    The balance is initial_balance + sum of transactions up to and including end_date_str.
    """
    conn = None
    try:
        # Validate end_date_str format
        datetime.strptime(end_date_str, "%Y-%m-%d")

        # Calculate end_date + 1 day for query condition (TRANSDATE < end_date_plus_one_day)
        end_date_str_p1 = (
            datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        conn = sqlite3.connect(db_file)
        query = f"""
            SELECT SUM({DB_FIELD_TRANS_AMOUNT})
            FROM {DB_TABLE_TRANSACTIONS}
            WHERE {DB_FIELD_TRANS_ACCOUNTID_FK} = ?
            AND {DB_FIELD_TRANS_DATE} < ?
        """
        cursor = conn.cursor()
        cursor.execute(query, (account_id, end_date_str_p1))
        result = cursor.fetchone()

        sum_transactions = result[0] if result and result[0] is not None else 0.0
        balance = float(initial_balance) + float(sum_transactions)
        return None, balance
    except sqlite3.Error as e:
        return f"Database error calculating balance: {e}", None
    except ValueError: # Catches strptime error
        return f"Invalid date format for balance calculation: {end_date_str}", None
    except Exception as e:
        return f"Unexpected error calculating balance: {e}", None
    finally:
        if conn:
            conn.close()


class AccountTabContent(BoxLayout):
    """Content for each account tab. Now primarily for displaying filtered data."""

    account_id = ObjectProperty(None)
    account_name = StringProperty("")
    initial_balance = ObjectProperty(0.0)

    def __init__(self, account_id, account_name, initial_balance, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [5, 5, 5, 5]
        self.spacing = 5
        self.account_id = account_id
        self.account_name = account_name
        self.initial_balance = initial_balance

        # Layout for title and balance
        header_layout = BoxLayout(size_hint_y=None, height=30, spacing=10)
        self.results_label = Label( # This is the status label for transactions
            text=f"Transactions for {self.account_name}",
            size_hint_x=0.7,
            color=DEFAULT_TEXT_COLOR_ON_DARK_BG,
        )
        header_layout.add_widget(self.results_label)

        self.balance_label = Label(
            text="Balance: N/A",
            size_hint_x=0.3,
            color=DEFAULT_TEXT_COLOR_ON_DARK_BG,
        )
        header_layout.add_widget(self.balance_label)
        self.add_widget(header_layout)

        self.scroll_view = ScrollView()
        self.results_grid = GridLayout(
            cols=7, size_hint_y=None, spacing=2
        )  # Increased cols
        self.results_grid.bind(minimum_height=self.results_grid.setter("height"))

        with self.results_grid.canvas.before:
            Color(*GRID_BACKGROUND_GREEN)
            self.results_grid_bg = Rectangle(size=self.results_grid.size, pos=self.results_grid.pos)

        def update_results_grid_bg_rect(instance, value):
            self.results_grid_bg.pos = instance.pos
            self.results_grid_bg.size = instance.size
        self.results_grid.bind(pos=update_results_grid_bg_rect, size=update_results_grid_bg_rect)
        self.scroll_view.add_widget(self.results_grid)
        self.add_widget(self.scroll_view)


class MMEXAppLayout(BoxLayout):
    """Main layout for the MMEX Kivy application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [10, 10, 10, 10]
        self.spacing = 10
        self.all_transactions_df = None  # Store the globally queried DataFrame
        self.db_file_path = load_db_path()  # Load DB path once

        # --- Database Path Display ---
        self.db_path_label = Label(
            # text=f"DB: {load_db_path() or 'Not Set'}",
            text=f"DB: {self.db_file_path or 'Not Set'}",
            size_hint_y=None,
            height=40,
            # This label is on the main light grey background
            color=DEFAULT_TEXT_COLOR_ON_LIGHT_BG,
        )
        self.add_widget(self.db_path_label)

        # --- Global Date Inputs ---
        date_input_layout = GridLayout(cols=4, size_hint_y=None, height=40, spacing=10)
        date_input_layout.add_widget(
            Label(text="Start Date:", color=DEFAULT_TEXT_COLOR_ON_LIGHT_BG)
        )

        def get_first_day_of_last_month():
            today = datetime.now()
            first_day_of_current_month = today.replace(day=1)
            first_day_of_last_month = (
                first_day_of_current_month - timedelta(days=1)
            ).replace(day=1)
            return first_day_of_last_month.strftime("%Y-%m-%d")

        self.start_date_input = TextInput(
            text=get_first_day_of_last_month(), multiline=False
        )
        self.start_date_input.bind(
            on_text_validate=self.trigger_global_query_on_date_change
        )
        date_input_layout.add_widget(self.start_date_input)
        date_input_layout.add_widget(
            Label(text="End Date:", color=DEFAULT_TEXT_COLOR_ON_LIGHT_BG)
        )
        self.end_date_input = TextInput(
            text=datetime.now().strftime("%Y-%m-%d"), multiline=False
        )
        self.end_date_input.bind(
            on_text_validate=self.trigger_global_query_on_date_change
        )
        date_input_layout.add_widget(self.end_date_input)
        self.add_widget(date_input_layout)

        # --- Tabbed Panel for Accounts ---
        self.tab_panel = TabbedPanel(
            do_default_tab=False,
            tab_pos="top_mid",
            size_hint_y=0.7,  # Adjusted size_hint_y
        )
        self.tab_panel.bind(current_tab=self.on_tab_switch)
        self.add_widget(self.tab_panel)

        self._create_all_transactions_tab()  # Create the "All Transactions" tab first
        self.load_account_specific_tabs()  # Then load other account tabs

        # --- Exit Button ---
        exit_button_layout = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=40, spacing=10
        )
        spacer = Widget(size_hint_x=1)
        exit_button_layout.add_widget(spacer)
        self.exit_button = Button(text="Exit", size_hint_x=None, width=100)
        self.exit_button.bind(on_press=self.exit_app)  # type: ignore
        exit_button_layout.add_widget(self.exit_button)
        self.add_widget(exit_button_layout)

        # Automatically load data on startup
        self.run_global_query(None)  # Pass None as instance since no button is pressed

    def _create_all_transactions_tab(self):
        self.all_transactions_tab = TabbedPanelHeader(
            text="All"
        )  # Use TabbedPanelHeader

        all_trans_content = BoxLayout(orientation="vertical", spacing=5, padding=5)
        self.all_transactions_status_label = Label(
            text="Perform a query to see all transactions.",
            size_hint_y=None,
            height=30,
            color=(0, 0, 0, 1),
        )  # This will be updated to white text below
        all_trans_content.add_widget(self.all_transactions_status_label)

        scroll_view_all = ScrollView()
        self.all_transactions_grid = GridLayout(
            cols=7, size_hint_y=None, spacing=2
        )  # Increased cols
        self.all_transactions_grid.bind(
            minimum_height=self.all_transactions_grid.setter("height")
        )

        with self.all_transactions_grid.canvas.before:
            Color(*GRID_BACKGROUND_GREEN)
            self.all_transactions_grid_bg = Rectangle(size=self.all_transactions_grid.size, pos=self.all_transactions_grid.pos)

        def update_all_transactions_grid_bg_rect(instance, value):
            self.all_transactions_grid_bg.pos = instance.pos
            self.all_transactions_grid_bg.size = instance.size
        self.all_transactions_grid.bind(pos=update_all_transactions_grid_bg_rect, size=update_all_transactions_grid_bg_rect)

        scroll_view_all.add_widget(self.all_transactions_grid)
        all_trans_content.add_widget(scroll_view_all)

        self.all_transactions_tab.content = all_trans_content
        self.tab_panel.add_widget(self.all_transactions_tab)
        # Set text color for the status label inside the tab
        self.all_transactions_status_label.color = DEFAULT_TEXT_COLOR_ON_DARK_BG
        self.tab_panel.default_tab = self.all_transactions_tab  # Set as default

    def load_account_specific_tabs(self):
        if not self.db_file_path:
            # Error already shown by db_path_label or initial global query attempt
            return

        error_msg, accounts_df = get_all_accounts(self.db_file_path)
        if error_msg:
            self.show_popup("Error Loading Accounts", error_msg)
            return

        if accounts_df is not None and not accounts_df.empty:
            for index, row in accounts_df.iterrows():
                account_id = row["ACCOUNTID"]
                account_name = str(row["ACCOUNTNAME"])
                
                # Get initial balance robustly
                initial_balance = 0.0
                if DB_FIELD_ACCOUNT_INITIAL_BALANCE in accounts_df.columns:
                    raw_val = row[DB_FIELD_ACCOUNT_INITIAL_BALANCE]
                    if pd.notna(raw_val):
                        try:
                            initial_balance = float(raw_val)
                        except ValueError:
                            print(f"Warning: Could not convert INITIALBAL '{raw_val}' to float for account {account_name}. Defaulting to 0.0.")
                else:
                    print(f"Warning: '{DB_FIELD_ACCOUNT_INITIAL_BALANCE}' column not found in {DB_TABLE_ACCOUNTS}. Account balances might assume a zero initial balance.")

                # Use TabbedPanelHeader for consistency if you want to style headers
                tab_header = TabbedPanelHeader(
                    text=account_name[:25]
                )  # Truncate long names
                # Store account_id and name directly on the header for easy access
                tab_header.account_id = account_id
                tab_header.account_name_full = account_name
                # tab_header.initial_balance = initial_balance # Can store here if needed elsewhere
                # The content will be an AccountTabContent instance
                tab_content = AccountTabContent(
                    account_id=account_id, account_name=account_name, initial_balance=initial_balance
                )
                tab_header.content = tab_content
                self.tab_panel.add_widget(tab_header)
        # No "No Accounts" tab here, as "All Transactions" tab always exists.
        # If no accounts, only "All Transactions" tab will be effectively usable for data.

    def _populate_grid_with_dataframe(
        self, target_grid, df, status_label_widget, status_message_prefix=""
    ):
        """Helper function to populate a GridLayout with DataFrame data."""
        target_grid.clear_widgets()

        if df is None or df.empty:
            no_data_label = Label(
                text="No data to display for current selection.",
                size_hint_y=None,
                height=30,
                color=DEFAULT_TEXT_COLOR_ON_DARK_BG,
            )
            target_grid.add_widget(no_data_label)
            if status_label_widget:
                status_label_widget.text = f"{status_message_prefix} No records found."
            return

        target_grid.cols = 7  # Updated column count
        headers = [
            "Date",
            "Account",
            "Payee",
            "Category",
            "Notes",
            "Amount",
            "Tags",
        ]  # Added "Tags" header
        for header_text in headers:
            header_label = Label(
                text=f"[b]{header_text}[/b]",
                markup=True,
                size_hint_y=None,
                height=40,
                color=DEFAULT_TEXT_COLOR_ON_LIGHT_BG,
                halign="left",
                valign="middle",
            )
            header_label.bind(size=header_label.setter("text_size"))
            target_grid.add_widget(header_label)

        for index, row in df.iterrows():
            trans_date_full = str(row["TRANSDATE"])
            trans_date = (
                trans_date_full.split("T")[0]
                if "T" in trans_date_full
                else trans_date_full
            )
            row_data = [
                trans_date,
                str(row["ACCOUNTNAME"]) if pd.notna(row["ACCOUNTNAME"]) else "",
                str(row["PAYEENAME"]) if pd.notna(row["PAYEENAME"]) else "",
                str(row["CATEGNAME"]) if pd.notna(row["CATEGNAME"]) else "",
                str(row["NOTES"]) if pd.notna(row["NOTES"]) else "",
                str(row["TRANSAMOUNT"]),
                str(row["TAGNAMES"])
                if pd.notna(row["TAGNAMES"])
                else "",  # Added Tags data
            ]
            for item in row_data:
                cell_label = Label(
                    text=item,
                    size_hint_y=None,
                    height=30,
                    color=DEFAULT_TEXT_COLOR_ON_LIGHT_BG,
                    halign="left",
                    valign="middle",
                )
                cell_label.bind(size=cell_label.setter("text_size"))
                target_grid.add_widget(cell_label)
        if status_label_widget:
            status_label_widget.text = (
                f"{status_message_prefix} Found {len(df)} records."
            )

    def run_global_query(self, instance):
        """Handles the global query button press."""
        start_date = self.start_date_input.text
        end_date = self.end_date_input.text

        if not self.db_file_path:
            self.show_popup("Error", "Database path not configured in .env file.")
            self.all_transactions_status_label.text = "DB Error. Configure .env file."
            return

        self.all_transactions_status_label.text = "Status: Querying all transactions..."
        self.all_transactions_grid.clear_widgets()  # Clear previous global results

        # Fetch ALL transactions for the date range (account_id=None)
        error_message, df = get_transactions(
            self.db_file_path,
            start_date,
            end_date,
            account_id=None,
            # query_tags=True # Potentially add a flag if tag querying is optional
        )

        self.all_transactions_df = None  # Reset before assigning

        if error_message:
            self.all_transactions_df = None
            if "No income/expense records found" in error_message:
                self.all_transactions_status_label.text = (
                    "No records found for the selected period (all accounts)."
                )
                self._populate_grid_with_dataframe(
                    self.all_transactions_grid, None, None
                )
            else:
                print(f"Error fetching transactions: {error_message}")
                self.show_popup("Global Query Error", error_message)
                self.all_transactions_status_label.text = (
                    "Global Query failed. See popup."
                )
            return

        if df is not None and not df.empty:
            self.all_transactions_df = df
            self._populate_grid_with_dataframe(
                self.all_transactions_grid,
                self.all_transactions_df,
                self.all_transactions_status_label,
                "All Transactions:",
            )
        else:
            self.all_transactions_df = None  # Ensure it's None if query returned empty
            self._populate_grid_with_dataframe(
                self.all_transactions_grid,
                None,
                self.all_transactions_status_label,
                "All Transactions:",
            )

        # After global query, refresh the currently active tab if it's an account tab
        self.on_tab_switch(self.tab_panel, self.tab_panel.current_tab)

    def trigger_global_query_on_date_change(self, instance):
        """Called when date input fields are validated (Enter or focus loss)."""
        # The 'instance' is the TextInput widget that triggered the event.
        self.run_global_query(instance)

    def on_tab_switch(self, tab_panel_instance, current_tab_header):
        """Called when the current tab changes."""
        if not current_tab_header or not hasattr(current_tab_header, "content"):
            return  # No tab selected or tab has no content widget yet

        tab_content_widget = current_tab_header.content

        if current_tab_header == self.all_transactions_tab:
            # "All Transactions" tab is selected, ensure its grid is populated if data exists
            if self.all_transactions_df is not None:
                self._populate_grid_with_dataframe(
                    self.all_transactions_grid,
                    self.all_transactions_df,
                    self.all_transactions_status_label,
                    "All Transactions:",
                )
            else:
                self._populate_grid_with_dataframe(
                    self.all_transactions_grid,
                    None,
                    self.all_transactions_status_label,
                    "All Transactions:",
                )
                if not self.db_path_label.text.endswith(
                    "Not Set"
                ):  # Only show if DB is set
                    self.all_transactions_status_label.text = (
                        "Perform a global query to see all transactions."
                    )

        elif isinstance(tab_content_widget, AccountTabContent):
            # An account-specific tab is selected
            account_id_of_tab = tab_content_widget.account_id
            account_name_of_tab = tab_content_widget.account_name
            initial_balance_of_tab = tab_content_widget.initial_balance

            end_date_for_balance = self.end_date_input.text

            # Calculate and display balance
            if self.db_file_path:
                err_bal, balance = get_balance_as_of_date(
                    self.db_file_path,
                    account_id_of_tab,
                    initial_balance_of_tab,
                    end_date_for_balance
                )
                if err_bal:
                    tab_content_widget.balance_label.text = "Balance: Error"
                    print(f"Error calculating balance for {account_name_of_tab}: {err_bal}")
                elif balance is not None:
                    tab_content_widget.balance_label.text = f"Balance: {balance:,.0f}"
                else:
                    tab_content_widget.balance_label.text = "Balance: N/A"
            else:
                tab_content_widget.balance_label.text = "Balance: DB N/A"

            if self.all_transactions_df is None:
                tab_content_widget.results_label.text = (
                    f"Perform a global query first for {account_name_of_tab}."
                )
                self._populate_grid_with_dataframe(
                    tab_content_widget.results_grid, None, None
                )
            else:
                # Filter the global DataFrame for this specific account tab.
                # Filter using TRANSACTION_ACCOUNTID from the DataFrame and the tab's account_id.
                filtered_df = self.all_transactions_df[
                    self.all_transactions_df["TRANSACTION_ACCOUNTID"] == account_id_of_tab
                ]

                self._populate_grid_with_dataframe(
                    tab_content_widget.results_grid,
                    filtered_df,
                    tab_content_widget.results_label,
                    f"{account_name_of_tab}:",
                )
        else:
            # Some other type of tab content, or content not yet set
            pass

    def show_popup(self, title, message):
        """Displays a popup message to the user."""
        popup_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        # Popups usually have a light background, so black text is fine here.
        popup_label = Label(text=message, color=DEFAULT_TEXT_COLOR_ON_LIGHT_BG)
        close_button = Button(text="Close", size_hint_y=None, height=40)
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)  # type: ignore
        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def exit_app(self, instance):
        """Closes the application."""
        App.get_running_app().stop()


class MMEXKivyApp(App):
    """The main Kivy application class."""

    def build(self):
        Window.clearcolor = (0.99, 0.99, 0.99, 1)
        actual_font_path = UNICODE_FONT_PATH
        if not os.path.isabs(actual_font_path):
            actual_font_path = os.path.join(SCRIPT_DIR, actual_font_path)
        try:
            if not os.path.exists(actual_font_path):
                print(
                    f"Warning: Font file '{actual_font_path}' not found. "
                    "Kivy will use its default font."
                )
                print(
                    f"Please ensure you have placed a font file supporting "
                    f"non-English characters at '{SCRIPT_DIR}' or provide "
                    "the correct UNICODE_FONT_PATH."
                )
            else:
                kv_font_path = actual_font_path.replace("\\", "\\\\")
                kv_string = f"""
<Label>:
    font_name: '{kv_font_path}'
<TextInput>:
    font_name: '{kv_font_path}'
<Button>:
    font_name: '{kv_font_path}'
<TabbedPanelHeader>:
    font_name: '{kv_font_path}'
"""
                Builder.load_string(kv_string)
                print(f"Successfully set default font to: {actual_font_path}")
        except Exception as e:
            print(
                f"Error setting global font '{actual_font_path}': {e}. "
                "Kivy will use its default font."
            )
        return MMEXAppLayout()


if __name__ == "__main__":
    print("--- MMEX Database Schema Configuration ---")
    for name, value in globals().copy().items():
        if name.startswith("DB_TABLE_") or name.startswith("DB_FIELD_"):
            # print(f"Global var: {name} = {value}")
            print(f"{name}: {value}")
    print("----------------------------------------")

    os.chdir(SCRIPT_DIR)
    MMEXKivyApp().run()
