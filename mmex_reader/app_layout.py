"""MMEX Application Layout - Refactored module

This module contains the MMEXAppLayout class with its core functionality.
The original monolithic file has been split to improve maintainability.
"""

# Standard library imports
import os
from datetime import datetime, timedelta

# Third-party imports
import kivy
import pandas as pd

# Kivy imports
kivy.require("2.1.0")
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
# Removed unused imports: ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.textinput import TextInput
# Removed unused import: Widget

# Local module imports
from db_utils import (
    load_db_path,
    get_all_accounts,
    get_transactions,
    calculate_balance_for_account,
)
from ui import AccountTabContent, DatePickerButton, show_popup
from ui import populate_grid_with_dataframe, TransactionDetailsPopup
from visualization_refactored import VisualizationTab
from config_manager import config_manager
from async_utils import AsyncDatabaseOperation, LoadingIndicator, AsyncQueryManager
from pagination_utils import PaginationInfo, get_offset_limit, get_transaction_count


class UIConstants:
    """Centralized constants for UI configuration."""
    
    # Window settings
    WINDOW_MIN_WIDTH = 800
    WINDOW_MIN_HEIGHT = 600
    
    # Component dimensions
    BUTTON_HEIGHT = 40
    INPUT_HEIGHT = 35
    HEADER_HEIGHT = 45
    
    # Spacing and padding
    COMPONENT_SPACING = 5
    LAYOUT_PADDING = 10
    
    # Default values
    DEFAULT_PAGE_SIZE = 50
    MAX_SAMPLE_ROWS = 100
    
    # Date format
    DATE_FORMAT = "%Y-%m-%d"
    
    # Transaction headers
    TRANSACTION_HEADERS = [
        "Date", "Account", "Payee", "Category", "Tags", "Notes", "Amount"
    ]
    
    # Filter options
    FILTER_OPTIONS = [
        "All Fields", "Account", "Payee", "Category", "Notes", "Tags"
    ]


class MMEXAppLayout(BoxLayout):
    """Main application layout for the MMEX Kivy application."""

    def __init__(self, **kwargs):
        """Initialize the MMEX application layout."""
        super(MMEXAppLayout, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = UIConstants.LAYOUT_PADDING
        self.spacing = UIConstants.COMPONENT_SPACING
        self.all_transactions_df = None
        self.filtered_transactions_df = None
        self.current_sort_column = None
        self.current_sort_ascending = True
        self.account_tabs = {}
        self.current_page = 1
        self.page_size = getattr(config_manager.get_config(), 'page_size', UIConstants.DEFAULT_PAGE_SIZE)
        self.total_count = 0
        self.total_pages = 0
        self.pagination_info = None