import kivy
kivy.require('2.1.0') # replace with your Kivy version if needed

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window

import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

# --- Database Functions (adapted from mmex_reader.py) ---
def load_db_path():
    load_dotenv()
    db_file = os.getenv("DB_FILE_PATH")
    if not db_file:
        return None
    return db_file

def get_transactions(db_file, start_date_str, end_date_str):
    if not db_file:
        return "Error: DB_FILE_PATH not found.", None

    try:
        datetime.strptime(start_date_str, "%Y-%m-%d")
        datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return f"Error: Incorrect date format. Please use YYYY-MM-DD. Start: {start_date_str}, End: {end_date_str}", None

    conn = None  # Initialize conn to None
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
            WHERE CHECKINGACCOUNT_V1.TRANSDATE BETWEEN '{start_date_str}' AND '{end_date_str}'
            ORDER BY CHECKINGACCOUNT_V1.TRANSDATE ASC, CHECKINGACCOUNT_V1.TRANSID ASC;
        """
        df = pd.read_sql_query(query, conn)
        if df.empty:
            return f"No income/expense records found between {start_date_str} and {end_date_str}.", None
        return None, df # Return None for error, and df for data

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [10, 10, 10, 10]
        self.spacing = 10

        # --- Database Path Display ---
        self.db_path_label = Label(text=f"DB: {load_db_path() or 'Not Set'}", size_hint_y=None, height=30)
        self.add_widget(self.db_path_label)

        # --- Date Inputs ---
        input_layout = GridLayout(cols=2, size_hint_y=None, height=70, spacing=10)
        input_layout.add_widget(Label(text='Start Date (YYYY-MM-DD):'))
        self.start_date_input = TextInput(text="2025-01-01", multiline=False)
        input_layout.add_widget(self.start_date_input)

        input_layout.add_widget(Label(text='End Date (YYYY-MM-DD):'))
        self.end_date_input = TextInput(text="2025-05-31", multiline=False)
        input_layout.add_widget(self.end_date_input)
        self.add_widget(input_layout)

        # --- Query Button ---
        self.query_button = Button(text='Query Transactions', size_hint_y=None, height=40)
        self.query_button.bind(on_press=self.run_query)
        self.add_widget(self.query_button)

        # --- Results Area ---
        self.results_label = Label(text='Results will appear here.', size_hint_y=None, height=30)
        self.add_widget(self.results_label)
        
        self.scroll_view = ScrollView()
        self.results_text = Label(text='', markup=True, size_hint_y=None)
        self.results_text.bind(texture_size=self.results_text.setter('size')) # For scrolling
        self.scroll_view.add_widget(self.results_text)
        self.add_widget(self.scroll_view)

    def run_query(self, instance):
        db_file = load_db_path()
        start_date = self.start_date_input.text
        end_date = self.end_date_input.text

        if not db_file:
            self.show_popup("Error", "Database path not configured in .env file.")
            return

        self.results_text.text = "Querying..."
        error_message, df = get_transactions(db_file, start_date, end_date)

        if error_message:
            self.results_text.text = '' # Clear previous results before showing error
            self.show_popup("Query Error", error_message)
            self.results_label.text = "Query failed. See popup for details."
            return

        if df is not None and not df.empty:
            self.results_label.text = f"Found {len(df)} records:"
            # Format DataFrame for display
            # Using a simple string format for now, can be improved with Kivy's RecycleView for better performance
            header = f"[b]{'Date':<12} | {'Account':<15} | {'Payee':<20} | {'Category':<25} | {'Notes':<30} | {'Amount'}[/b]\n"
            header += "-" * 120 + "\n"
            formatted_results = header
            for index, row in df.iterrows():
                formatted_results += f"{row['TRANSDATE']} | {row['ACCOUNTNAME']:<15} | {row['PAYEENAME'] if row['PAYEENAME'] else '':<20} | {row['CATEGNAME'] if row['CATEGNAME'] else '':<25} | {row['NOTES'] if row['NOTES'] else '':<30} | {row['TRANSAMOUNT']}\n"
            self.results_text.text = formatted_results
        else:
            self.results_label.text = "No records found or query returned empty."
            self.results_text.text = '' # Clear previous results

    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text=message)
        close_button = Button(text='Close', size_hint_y=None, height=40)
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

class MMEXKivyApp(App):
    def build(self):
        Window.clearcolor = (0.9, 0.9, 0.9, 1) # Light grey background
        return MMEXAppLayout()

if __name__ == '__main__':
    # Change working directory to the script's directory
    # This is important for Kivy to find .kv files if you use them later
    # and for relative paths in general.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    MMEXKivyApp().run()