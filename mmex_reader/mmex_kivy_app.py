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
                ACCOUNTLIST_V1.ACCOUNTNAME, 
                CHECKINGACCOUNT_V1.TRANSDATE, 
                CHECKINGACCOUNT_V1.NOTES, 
                CHECKINGACCOUNT_V1.TRANSAMOUNT, 
                PAYEE_V1.PAYEENAME,
                CATEGORY_V1.CATEGNAME
            FROM CHECKINGACCOUNT_V1
            LEFT JOIN ACCOUNTLIST_V1 ON CHECKINGACCOUNT_V1.ACCOUNTID = ACCOUNTLIST_V1.ACCOUNTID
            LEFT JOIN PAYEE_V1 ON CHECKINGACCOUNT_V1.PAYEEID = PAYEE_V1.PAYEEID
            LEFT JOIN CATEGORY_V1 ON CHECKINGACCOUNT_V1.CATEGID = CATEGORY_V1.CATEGID
            WHERE CHECKINGACCOUNT_V1.TRANSDATE BETWEEN ? AND ?
            ORDER BY CHECKINGACCOUNT_V1.TRANSDATE ASC, CHECKINGACCOUNT_V1.TRANSID ASC;
        """
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
        self.results_text = Label(
            text="", markup=True, size_hint_y=None, color=default_text_color
        )
        self.results_text.bind(texture_size=self.results_text.setter("size"))
        self.scroll_view.add_widget(self.results_text)
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
            self.results_text.text = "No data to display."
            return

        # The results_text Label will use the globally set default font.
        # Markup [b] for bold is used.

        header = f"[b]{'Date':<12} | {'Account':<15} | {'Payee':<20} | {'Category':<25} | {'Notes':<30} | {'Amount'}[/b]\n"
        header += "-" * 120 + "\n"
        formatted_results = header
        for index, row in df.iterrows():
            trans_date = str(row["TRANSDATE"])  # Ensure string
            account_name = (
                str(row["ACCOUNTNAME"]) if pd.notna(row["ACCOUNTNAME"]) else ""
            )
            payee_name = str(row["PAYEENAME"]) if pd.notna(row["PAYEENAME"]) else ""
            categ_name = str(row["CATEGNAME"]) if pd.notna(row["CATEGNAME"]) else ""
            notes = str(row["NOTES"]) if pd.notna(row["NOTES"]) else ""
            trans_amount = row["TRANSAMOUNT"]

            # Format each data line
            formatted_results += (
                f"{trans_date} | {account_name:<15} | {payee_name:<20} | "
                f"{categ_name:<25} | {notes:<30} | {trans_amount}\n"
            )
        self.results_text.text = formatted_results

    def run_query(self, instance):
        """Handles the query button press, fetches and displays transactions."""
        db_file = load_db_path()
        start_date = self.start_date_input.text
        end_date = self.end_date_input.text

        if not db_file:
            self.show_popup("Error", "Database path not configured in .env file.")
            return

        self.results_text.text = "Querying..."
        self.results_label.text = "Status: Processing query..."
        self.last_df_data = None  # Clear previous DataFrame

        error_message, df = get_transactions(db_file, start_date, end_date)

        if error_message:
            self.results_text.text = ""  # Clear previous results before showing error
            # Distinguish "no data" message from actual errors
            if "No income/expense records found" in error_message:
                self.results_label.text = "No records found for the selected period."
                self.results_text.text = (
                    "Please try different dates or check your database."
                )
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
            self.results_text.text = "The query returned no data."

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
