"""
A Kivy application for reading and displaying financial transactions
from an MMEX (MoneyManagerEx) database file.
"""

import kivy

kivy.require("2.1.0")  # replace with your Kivy version if needed

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget  # For spacer
from kivy.lang import Builder  # Changed from kivy.factory import Factory
import os

import sqlite3
import pandas as pd

# import os # Removed duplicate import
from dotenv import load_dotenv
from datetime import datetime

# --- Script Directory ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Font Configuration ---
# IMPORTANT: Replace 'YourUnicodeFont.ttf' with the actual font file name you are
# using. This font file should support the non-English characters that might be
# present in your database.
# For example, for Chinese/Japanese/Korean, you might use
# "NotoSansCJKsc-Regular.otf" or a similar Unicode font.
# For broader Unicode support, "NotoSans-Regular.ttf" could be an option.
# Place the font file in the same directory as this script, in a specified
# subdirectory (e.g., 'fonts'), or provide an absolute path.
UNICODE_FONT_PATH = "fonts/NotoSansCJKtc-Regular.otf"  # Example: Using a font from the 'fonts' subdirectory.

# --- MMEX Database Schema Configuration (Example - adapt to your target MMEX version) ---
# You would ideally load these from a config file or detect them.
# For simplicity, defined as constants here.
DB_TABLE_TRANSACTIONS = "CHECKINGACCOUNT_V1"
DB_TABLE_ACCOUNTS = "ACCOUNTLIST_V1"
DB_TABLE_PAYEES = "PAYEE_V1"
DB_TABLE_CATEGORIES = "CATEGORY_V1"

# Field names for Transactions table
DB_FIELD_TRANS_ID = "TRANSID"
DB_FIELD_TRANS_DATE = "TRANSDATE"
DB_FIELD_TRANS_NOTES = "NOTES"
DB_FIELD_TRANS_AMOUNT = "TRANSAMOUNT"
DB_FIELD_TRANS_ACCOUNTID_FK = "ACCOUNTID" # Foreign key to Accounts table
DB_FIELD_TRANS_PAYEEID_FK = "PAYEEID"     # Foreign key to Payees table
DB_FIELD_TRANS_CATEGID_FK = "CATEGID"     # Foreign key to Categories table

DB_FIELD_ACCOUNT_ID_PK = "ACCOUNTID" # Primary key in Accounts table
DB_FIELD_ACCOUNT_NAME = "ACCOUNTNAME"
# ... Add other field name constants for Payees and Categories tables as needed for joins
DB_FIELD_PAYEE_ID_PK = "PAYEEID"
DB_FIELD_PAYEE_NAME = "PAYEENAME"
DB_FIELD_CATEGORY_ID_PK = "CATEGID"
DB_FIELD_CATEGORY_NAME = "CATEGNAME"

# --- Database Functions (adapted from mmex_reader.py) ---
def load_db_path():
    env_path = os.path.join(SCRIPT_DIR, ".env")
    load_dotenv(dotenv_path=env_path, override=True)  # Load .env from script directory
    db_file = os.getenv("DB_FILE_PATH")
    if not db_file:
        return None
    return db_file


def get_transactions(db_file, start_date_str, end_date_str):
    """
    Fetches transactions from the MMEX database within a given date range."""
    if not db_file:
        return "Error: DB_FILE_PATH not found.", None

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
        query = f"""
            SELECT
                acc.{DB_FIELD_ACCOUNT_NAME} AS ACCOUNTNAME,
                trans.{DB_FIELD_TRANS_DATE} AS TRANSDATE,
                trans.{DB_FIELD_TRANS_NOTES} AS NOTES,
                trans.{DB_FIELD_TRANS_AMOUNT} AS TRANSAMOUNT,
                payee.{DB_FIELD_PAYEE_NAME} AS PAYEENAME,
                cat.{DB_FIELD_CATEGORY_NAME} AS CATEGNAME
            FROM {DB_TABLE_TRANSACTIONS} AS trans
            LEFT JOIN {DB_TABLE_ACCOUNTS} AS acc
                ON trans.{DB_FIELD_TRANS_ACCOUNTID_FK} = acc.{DB_FIELD_ACCOUNT_ID_PK}
            LEFT JOIN {DB_TABLE_PAYEES} AS payee
                ON trans.{DB_FIELD_TRANS_PAYEEID_FK} = payee.{DB_FIELD_PAYEE_ID_PK}
            LEFT JOIN {DB_TABLE_CATEGORIES} AS cat
                ON trans.{DB_FIELD_TRANS_CATEGID_FK} = cat.{DB_FIELD_CATEGORY_ID_PK}
            WHERE trans.{DB_FIELD_TRANS_DATE} BETWEEN ? AND ?
            ORDER BY trans.{DB_FIELD_TRANS_DATE} ASC, trans.{DB_FIELD_TRANS_ID} ASC;
        """
        # The aliases (AS ACCOUNTNAME, AS TRANSDATE, etc.) ensure the DataFrame columns
        # match what the _display_dataframe method expects.
        df = pd.read_sql_query(query, conn, params=(start_date_str, end_date_str))
        if df.empty:
            return (
                f"No income/expense records found between {start_date_str} "
                f"and {end_date_str}.",
                None,
            )
        return None, df  # Return None for error, and df for data

    except sqlite3.Error as e:
        return f"Database Error: {e}", None
    except pd.io.sql.DatabaseError as e:
        return f"Pandas SQL Error: {e}", None
    except Exception as e:
        return f"An unexpected error occurred: {e}", None
    finally:
        if conn:
            conn.close()


class MMEXAppLayout(BoxLayout):
    """Main layout for the MMEX Kivy application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [10, 10, 10, 10]
        self.spacing = 10
        self.last_df_data = None  # Stores the last successfully fetched DataFrame

        default_text_color = (0, 0, 0, 1)

        # --- Font Selector ---
        font_selector_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        font_selector_layout.add_widget(
            Label(text="Select Font:", color=default_text_color)
        )

        # --- Database Path Display ---
        self.db_path_label = Label(
            text=f"DB: {load_db_path() or 'Not Set'}",
            size_hint_y=None,
            # Adjusted height for potentially longer font names or CJK characters
            height=40,
            color=default_text_color,
        )
        self.add_widget(self.db_path_label)

        # --- Date Inputs ---
        input_layout = GridLayout(cols=2, size_hint_y=None, height=70, spacing=10)
        self.start_date_label = Label(
            text="Start Date (YYYY-MM-DD):", color=default_text_color
        )
        input_layout.add_widget(
            Label(text="Start Date (YYYY-MM-DD):", color=default_text_color)
        )
        self.start_date_input = TextInput(text="2025-01-01", multiline=False)
        input_layout.add_widget(self.start_date_input)

        self.end_date_label = Label(
            text="End Date (YYYY-MM-DD):", color=default_text_color
        )
        input_layout.add_widget(
            Label(text="End Date (YYYY-MM-DD):", color=default_text_color)
        )
        self.end_date_input = TextInput(text="2025-05-31", multiline=False)
        input_layout.add_widget(self.end_date_input)
        self.add_widget(input_layout)

        # --- Query Button ---
        self.query_button = Button(
            text="Query Transactions", size_hint_y=None, height=40
        )
        self.query_button.bind(on_press=self.run_query)
        self.add_widget(self.query_button)

        # --- Results Area ---
        self.results_label = Label(
            text="Results will appear here.",
            size_hint_y=None,
            height=30,
            color=default_text_color,
        )
        self.add_widget(self.results_label)

        self.scroll_view = ScrollView()
        # self.results_text will be replaced by a GridLayout for better alignment
        # self.results_text = Label(
        #     text="", markup=True, size_hint_y=None, color=default_text_color
        # )
        # self.results_text.bind(texture_size=self.results_text.setter("size"))
        # self.scroll_view.add_widget(self.results_text)
        self.results_grid = GridLayout(cols=6, size_hint_y=None, spacing=2)
        self.results_grid.bind(minimum_height=self.results_grid.setter('height'))
        self.scroll_view.add_widget(self.results_grid)
        self.add_widget(self.scroll_view)


        # --- Exit Button ---
        exit_button_layout = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=40, spacing=10
        )

        # Spacer to push the button to the right
        spacer = Widget(size_hint_x=1)
        exit_button_layout.add_widget(spacer)

        self.exit_button = Button(text="Exit", size_hint_x=None, width=100)
        self.exit_button.bind(on_press=self.exit_app)
        exit_button_layout.add_widget(self.exit_button)

        self.add_widget(exit_button_layout)

    def _display_dataframe(self, df):
        """Formats and displays the DataFrame in the results_text area."""
        if df is None or df.empty:
            # self.results_text.text = "No data to display."
            self.results_grid.clear_widgets() # Clear previous grid content
            no_data_label = Label(text="No data to display.", size_hint_y=None, height=30)
            self.results_grid.add_widget(no_data_label) # Add a single label
            # Make the label span all columns if possible, or adjust grid cols
            # For simplicity, we'll just add it. It might look a bit off if grid has many cols.
            # A better way for "no data" might be to hide the grid and show a separate label.
            return

        self.results_grid.clear_widgets() # Clear previous results
        self.results_grid.cols = 6 # Ensure 6 columns for data + header

        # Define column properties for better control if needed later
        # For now, we'll use default Label behavior within GridLayout cells
        headers = ['Date', 'Account', 'Payee', 'Category', 'Notes', 'Amount']
        for header_text in headers:
            header_label = Label(
                text=f"[b]{header_text}[/b]",
                markup=True,
                size_hint_y=None,
                height=40, # Adjust height as needed
                color=(0,0,0,1), # Explicitly set text color to black
                halign='left',
                valign='middle'
            )
            header_label.bind(size=header_label.setter('text_size')) # For text wrapping
            self.results_grid.add_widget(header_label)

        for index, row in df.iterrows():
            # Ensure string and format date to YYYY-MM-DD
            trans_date_full = str(row["TRANSDATE"])
            trans_date = trans_date_full.split("T")[0] if "T" in trans_date_full else trans_date_full
            
            account_name = (
                str(row["ACCOUNTNAME"]) if pd.notna(row["ACCOUNTNAME"]) else ""
            )
            payee_name = str(row["PAYEENAME"]) if pd.notna(row["PAYEENAME"]) else ""
            categ_name = (
                str(row["CATEGNAME"]) if pd.notna(row["CATEGNAME"]) else ""
            )
            notes = str(row["NOTES"]) if pd.notna(row["NOTES"]) else ""
            trans_amount = row["TRANSAMOUNT"]

            row_data = [trans_date, account_name, payee_name, categ_name, notes, str(trans_amount)]
            for item in row_data:
                cell_label = Label(
                    text=item,
                    size_hint_y=None,
                    height=30, # Adjust height as needed
                    color=(0,0,0,1), # Explicitly set text color to black
                    halign='left',
                    valign='middle'
                )
                cell_label.bind(size=cell_label.setter('text_size')) # For text wrapping
                self.results_grid.add_widget(cell_label)

    def run_query(self, instance):
        """Handles the query button press, fetches and displays transactions."""
        db_file = load_db_path()
        start_date = self.start_date_input.text
        end_date = self.end_date_input.text
        if not db_file:
            self.show_popup("Error", "Database path not configured in .env file.")
            return

        # self.results_text.text = "Querying..." # results_text is removed
        # Update results_label to show querying status
        self.results_label.text = "Status: Processing query..."
        self.last_df_data = None  # Clear previous DataFrame
        self.results_grid.clear_widgets() # Clear grid before new query

        error_message, df = get_transactions(db_file, start_date, end_date)

        if error_message:
            # self.results_text.text = "" # No longer using self.results_text directly for data
            # Distinguish "no data" message from actual errors
            if "No income/expense records found" in error_message:
                self.results_label.text = "No records found for the selected period."
                # self.results_text.text was here, message is now part of results_label
                # or handled by _display_dataframe(None)
                # Optionally, display this message in the grid area too
                self._display_dataframe(None) # Will show "No data to display"
            else:  # Actual database or pandas error
                self.show_popup("Query Error", error_message)
                self.results_label.text = "Query failed. See popup for details."
            return

        # If we are here, error_message is None.
        # df could be None or an empty DataFrame if get_transactions changes behavior.
        # Currently, get_transactions returns error_message for "no data".
        if df is not None and not df.empty:
            self.last_df_data = df
            self.results_label.text = f"Found {len(df)} records:"
            self._display_dataframe(df)
        else:
            # This case handles if get_transactions might return (None, empty_df)
            # or (None, None) in the future
            self.results_label.text = "No records found for the selected period."
            # self.results_text.text = "The query returned no data."
            self._display_dataframe(None) # Will show "No data to display"

    def show_popup(self, title, message):
        """Displays a popup message to the user."""
        popup_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Widgets in the popup will use the globally set default font
        popup_label = Label(text=message, color=(0, 0, 0, 1))
        close_button = Button(text="Close", size_hint_y=None, height=40)
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)

        # The Popup's title and content will use the globally set default font
        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def exit_app(self, instance):
        """Closes the application."""
        App.get_running_app().stop()


class MMEXKivyApp(App):
    """The main Kivy application class."""

    def build(self):
        Window.clearcolor = (0.9, 0.9, 0.9, 1)

        # Resolve font path: user can specify relative (to script) or absolute path
        actual_font_path = UNICODE_FONT_PATH
        if not os.path.isabs(actual_font_path):
            actual_font_path = os.path.join(SCRIPT_DIR, actual_font_path)

        # Set the global default font to support non-English characters
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
                # The app will still try to run, but Kivy's original default
                # font might not display all characters correctly.
            else:
                # Escape backslashes in the path for the Kv string, as Kivy's
                # Kv parser needs them escaped.
                kv_font_path = actual_font_path.replace("\\", "\\\\")
                # It's good practice to ensure the path in kv_string is
                # enclosed in single quotes, especially if it might contain
                # spaces or special characters, though less critical here.
                kv_string = f"""
<Label>:
    font_name: '{kv_font_path}'
<TextInput>:
    font_name: '{kv_font_path}'
<Button>:
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
    # SCRIPT_DIR is defined globally
    os.chdir(SCRIPT_DIR)  # Change CWD to script's directory for Kivy and other relative
    # paths that Kivy or other libraries might use.
    MMEXKivyApp().run()
