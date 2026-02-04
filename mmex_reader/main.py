"""MMEX Kivy Application - Main Entry Point

This module contains the main application class that extends Kivy's App class.
It initializes the MMEXAppLayout and handles application-level configuration.
"""

import kivy
kivy.require("2.1.0")

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder

import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Font Configuration
UNICODE_FONT_PATH = "fonts/NotoSansCJKtc-Regular.otf"


class MMEXKivyApp(App):
    """The main Kivy application class."""

    def build(self):
        """Build the application UI."""
        # Configure window
        self._configure_window()
        
        # Configure fonts
        self._configure_fonts()
        
        # Create and return the main layout
        from app_layout import MMEXAppLayout
        return MMEXAppLayout()

    def _configure_window(self):
        """Configure window properties."""
        Window.clearcolor = (0.99, 0.99, 0.99, 1)
        Window.minimum_width = 800
        Window.minimum_height = 600

    def _configure_fonts(self):
        """Configure application fonts."""
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


# This allows the file to be run directly
if __name__ == "__main__":
    print("--- MMEX Database Schema Configuration ---")
    # We'll print the schema constants from db_utils if available
    try:
        from db_utils import (
            DB_TABLE_TRANSACTIONS, DB_TABLE_ACCOUNTS, DB_TABLE_PAYEES, 
            DB_TABLE_CATEGORIES, DB_TABLE_TAGS, DB_TABLE_TRANSACTION_TAGS,
            DB_FIELD_TRANS_ID, DB_FIELD_TRANS_DATE, DB_FIELD_TRANS_NOTES,
            DB_FIELD_TRANS_AMOUNT, DB_FIELD_TRANS_ACCOUNTID_FK, DB_FIELD_TRANS_PAYEEID_FK,
            DB_FIELD_TRANS_CATEGID_FK, DB_FIELD_ACCOUNT_ID_PK, DB_FIELD_ACCOUNT_NAME,
            DB_FIELD_ACCOUNT_INITIAL_BALANCE, DB_FIELD_PAYEE_ID_PK, DB_FIELD_PAYEE_NAME,
            DB_FIELD_CATEGORY_ID_PK, DB_FIELD_CATEGORY_NAME, DB_FIELD_TAG_ID_PK,
            DB_FIELD_TAG_NAME, DB_FIELD_TRANSTAG_TRANSID_FK, DB_FIELD_TRANSTAG_TAGID_FK
        )
        
        print(f"DB_TABLE_TRANSACTIONS: {DB_TABLE_TRANSACTIONS}")
        print(f"DB_TABLE_ACCOUNTS: {DB_TABLE_ACCOUNTS}")
        print(f"DB_TABLE_PAYEES: {DB_TABLE_PAYEES}")
        print(f"DB_TABLE_CATEGORIES: {DB_TABLE_CATEGORIES}")
        print(f"DB_TABLE_TAGS: {DB_TABLE_TAGS}")
        print(f"DB_TABLE_TRANSACTION_TAGS: {DB_TABLE_TRANSACTION_TAGS}")
    except ImportError as e:
        print(f"Could not import database schema constants: {e}")
        print("Database schema constants will be loaded when needed.")
    
    print("--- Starting MMEX Kivy Application ---")
    MMEXKivyApp().run()