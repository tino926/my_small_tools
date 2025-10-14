"""A Kivy application for reading and displaying financial transactions
from an MMEX (MoneyManagerEx) database file.

This application provides a GUI for viewing and filtering transactions,
viewing account balances, and visualizing financial data with charts.

The application is organized into several modules:
- db_utils.py: Database utility functions
- ui_components.py: UI component classes
- visualization.py: Data visualization functions
- mmex_kivy_app.py: Main application code
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
from ui_components import (
    AccountTabContent,
    show_popup,
    populate_grid_with_dataframe,
    DatePickerButton,
    TransactionDetailsPopup,
    BG_COLOR,
    BUTTON_COLOR,
)
from visualization import VisualizationTab
from pagination_utils import get_transaction_count, PaginationInfo
from async_utils import AsyncDatabaseOperation, LoadingIndicator
from kv_components import (
    DateInputLayout,
    SearchFilterLayout,
    TransactionGrid,
    PaginationControls,
    VisualizationContent as KvVisualizationContent
)
from config_manager import config_manager, SettingsPopup

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UNICODE_FONT_PATH = os.path.join(SCRIPT_DIR, "fonts", "NotoSansCJKtc-Regular.otf")

# Load Kivy Language file
KV_FILE = os.path.join(SCRIPT_DIR, "mmex_app.kv")
if os.path.exists(KV_FILE):
    Builder.load_file(KV_FILE)

class UIConstants:
    """UI constants for consistent styling and behavior."""
    WINDOW_MIN_WIDTH = 1200
    WINDOW_MIN_HEIGHT = 800
    DEFAULT_FONT_SIZE = 14
    HEADER_HEIGHT = 40
    ROW_HEIGHT = 30
    BUTTON_HEIGHT = 40
    INPUT_HEIGHT = 35
    TAB_HEIGHT = 50
    SCROLL_DISTANCE = 20
    
    # Responsive breakpoints
    MOBILE_BREAKPOINT = 600
    TABLET_BREAKPOINT = 1024
    DESKTOP_BREAKPOINT = 1200
    
    # Responsive sizing
    MOBILE_PADDING = 5
    TABLET_PADDING = 8
    DESKTOP_PADDING = 10
    
    MOBILE_SPACING = 3
    TABLET_SPACING = 5
    DESKTOP_SPACING = 10
    
    # Transaction headers
    TRANSACTION_HEADERS = ["Date", "Account", "Payee", "Category", "Tags", "Notes", "Amount"]
    
    # Filter options
    FILTER_OPTIONS = ["All", "Income", "Expense", "Transfer"]
    
    # Date format
    DATE_FORMAT = "%Y-%m-%d"


class MMEXAppLayout(BoxLayout):
    """Main layout for the MMEX Kivy application."""

    def __init__(self, **kwargs):
        super(MMEXAppLayout, self).__init__(**kwargs)
        self.orientation = "vertical"
        
        # Initialize responsive properties
        self._setup_responsive_layout()
        
        # Initialize state variables
        self.db_path = load_db_path()
        self.current_sort_column = None
        self.current_sort_ascending = True
        self.all_transactions_df = pd.DataFrame()
        self.filtered_transactions_df = pd.DataFrame()
        self.account_tabs = {}
        
        # Initialize pagination state
        self.current_page = 1
        self.page_size = config_manager.get_config().page_size  # Use config value
        self.total_count = 0
        self.pagination_info = None
        
        # Initialize async loading
        self.loading_indicator = LoadingIndicator()

        # Create UI components
        self._create_date_inputs()
        self._create_search_filter_layout()
        self._create_tabbed_panel()
        self._create_exit_button()

        # Initialize data
        self.load_account_specific_tabs()
        self.run_global_query()
        
        # Bind to window resize events for responsive updates
        from kivy.core.window import Window
        Window.bind(on_resize=self._on_window_resize)
    
    def _setup_responsive_layout(self):
        """Setup responsive layout properties based on screen size."""
        from kivy.core.window import Window
        screen_width = Window.width
        
        if screen_width <= UIConstants.MOBILE_BREAKPOINT:
            self.padding = UIConstants.MOBILE_PADDING
            self.spacing = UIConstants.MOBILE_SPACING
            self.is_mobile = True
            self.is_tablet = False
            self.is_desktop = False
        elif screen_width <= UIConstants.TABLET_BREAKPOINT:
            self.padding = UIConstants.TABLET_PADDING
            self.spacing = UIConstants.TABLET_SPACING
            self.is_mobile = False
            self.is_tablet = True
            self.is_desktop = False
        else:
            self.padding = UIConstants.DESKTOP_PADDING
            self.spacing = UIConstants.DESKTOP_SPACING
            self.is_mobile = False
            self.is_tablet = False
            self.is_desktop = True
    
    def _on_window_resize(self, window, width, height):
        """Handle window resize events to update responsive layout."""
        old_is_mobile = getattr(self, 'is_mobile', False)
        old_is_tablet = getattr(self, 'is_tablet', False)
        old_is_desktop = getattr(self, 'is_desktop', True)
        
        self._setup_responsive_layout()
        
        # Only update layout if screen category changed
        if (old_is_mobile != self.is_mobile or 
            old_is_tablet != self.is_tablet or 
            old_is_desktop != self.is_desktop):
            self._update_responsive_components()
    
    def _update_responsive_components(self):
        """Update component sizing based on current screen size."""
        # Update date inputs layout
        if hasattr(self, 'date_layout'):
            if self.is_mobile:
                self.date_layout.orientation = 'vertical'
                if hasattr(self, 'start_date_input'):
                    self.start_date_input.size_hint = (1, None)
                if hasattr(self, 'end_date_input'):
                    self.end_date_input.size_hint = (1, None)
            else:
                self.date_layout.orientation = 'horizontal'
                if hasattr(self, 'start_date_input'):
                    self.start_date_input.size_hint = (0.5, None)
                if hasattr(self, 'end_date_input'):
                    self.end_date_input.size_hint = (0.5, None)
        
        # Update search filter layout
        if hasattr(self, 'search_filter_layout'):
            if self.is_mobile:
                self.search_filter_layout.orientation = 'vertical'
                self.search_input.size_hint = (1, None)
                self.filter_button.size_hint = (1, None)
                self.clear_filter_button.size_hint = (1, None)
            else:
                self.search_filter_layout.orientation = 'horizontal'
                self.search_input.size_hint = (0.6, None)
                self.filter_button.size_hint = (0.2, None)
                self.clear_filter_button.size_hint = (0.2, None)

    def run_global_query(self):
        """Execute the global transaction query and update the UI."""
        # Reset pagination to first page when running new query
        self.current_page = 1
        self._load_paginated_data()

    def on_tab_switch(self, instance, tab):
        """Handle tab switching to update content."""
        if tab.text == "All Transactions":
            self._update_all_transactions_tab()
        elif tab.text == "Charts":
            self.update_visualization()
        else:
            self._update_account_tab(tab.text)
    
    def _update_all_transactions_tab(self):
        """Update the All Transactions tab content."""
        populate_grid_with_dataframe(
            self.all_transactions_grid,
            self.filtered_transactions_df,
            UIConstants.TRANSACTION_HEADERS,
            sort_callback=self.sort_transactions,
            row_click_callback=self.on_transaction_row_click,
        )
        
        # Update status with pagination info
        if self.pagination_info:
            self.all_transactions_status.text = f"{len(self.filtered_transactions_df)} transactions on current page"
        else:
            self.all_transactions_status.text = f"{len(self.filtered_transactions_df)} transactions found"
    
    def _update_account_tab(self, account_name):
        """Update account-specific tab content.
        
        Args:
            account_name: Name of the account to update
        """
        for account_id, account_info in self.account_tabs.items():
            if account_info["name"] == account_name:
                content = account_info["content"]

                if hasattr(self, 'filtered_transactions_df'):
                    account_transactions = self.filtered_transactions_df[
                        self.filtered_transactions_df["ACCOUNTNAME"] == account_name
                    ]

                    populate_grid_with_dataframe(
                        content.results_grid,
                        account_transactions,
                        UIConstants.TRANSACTION_HEADERS,
                        sort_callback=self.sort_transactions,
                        row_click_callback=self.on_transaction_row_click,
                    )
                    content.results_label.text = f"{len(account_transactions)} transactions found"

                    # Update balance
                    self._update_account_balance(account_id, content, account_info)
                break
    
    def _update_account_balance(self, account_id, content, account_info=None):
        """Update account balance display.
        
        Args:
            account_id: Account ID
            content: Account tab content widget
            account_info: Account information dictionary (optional, for backward compatibility)
        """
        try:
            if not self._validate_date(self.end_date_input.text):
                content.balance_label.text = "Balance: Invalid date"
                return
                
            end_date = datetime.strptime(self.end_date_input.text, UIConstants.DATE_FORMAT)
            error, balance = calculate_balance_for_account(
                self.db_path,
                account_id,
                end_date,
            )
            if error:
                content.balance_label.text = f"Balance: {error}"
            else:
                content.balance_label.text = f"Balance: ${balance:.2f}"
        except Exception as e:
            content.balance_label.text = "Balance: Error"

    def _create_date_inputs(self):
        """Create date input fields with responsive validation using date picker widgets."""
        # Create responsive date layout
        if self.is_mobile:
            self.date_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=80, spacing=self.spacing)
        else:
            self.date_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=self.spacing)

        # Start date section
        if self.is_mobile:
            start_section = BoxLayout(orientation='horizontal', size_hint=(1, 0.5), spacing=5)
            start_section.add_widget(Label(text="Start Date:", size_hint=(0.3, 1)))
            self.start_date_input = DatePickerButton(
                initial_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                date_change_callback=self._on_date_change,
                size_hint=(0.7, 1),
            )
            start_section.add_widget(self.start_date_input)
            self.date_layout.add_widget(start_section)
        else:
            self.date_layout.add_widget(Label(text="Start Date:", size_hint=(None, 1), width=80))
            self.start_date_input = DatePickerButton(
                initial_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                date_change_callback=self._on_date_change,
                size_hint=(0.5, 1),
            )
            self.date_layout.add_widget(self.start_date_input)

        # End date section
        if self.is_mobile:
            end_section = BoxLayout(orientation='horizontal', size_hint=(1, 0.5), spacing=5)
            end_section.add_widget(Label(text="End Date:", size_hint=(0.3, 1)))
            self.end_date_input = DatePickerButton(
                initial_date=datetime.now().strftime("%Y-%m-%d"),
                date_change_callback=self._on_date_change,
                size_hint=(0.7, 1),
            )
            end_section.add_widget(self.end_date_input)
            self.date_layout.add_widget(end_section)
        else:
            self.date_layout.add_widget(Label(text="End Date:", size_hint=(None, 1), width=70))
            self.end_date_input = DatePickerButton(
                initial_date=datetime.now().strftime("%Y-%m-%d"),
                date_change_callback=self._on_date_change,
                size_hint=(0.5, 1),
            )
            self.date_layout.add_widget(self.end_date_input)

        self.add_widget(self.date_layout)

    def _validate_date(self, date_str):
        """Validate date string format.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            datetime.strptime(date_str, UIConstants.DATE_FORMAT)
            return True
        except ValueError:
            return False
    
    def _on_date_change(self, instance, value):
        """Trigger the global query when the date changes, with validation."""
        start_date = self.start_date_input.get_date() if hasattr(self.start_date_input, 'get_date') else self.start_date_input.text
        end_date = self.end_date_input.get_date() if hasattr(self.end_date_input, 'get_date') else self.end_date_input.text
        
        if self._validate_date(start_date) and self._validate_date(end_date):
            self.run_global_query()

    def _create_search_filter_layout(self):
        """Create responsive search and filter layout."""
        # Create responsive search layout
        if self.is_mobile:
            self.search_filter_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=120, spacing=self.spacing)
            
            # Search section
            search_section = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=5)
            search_section.add_widget(Label(text="Search:", size_hint=(0.25, 1)))
            self.search_input = TextInput(multiline=False, size_hint=(0.75, 1))
            search_section.add_widget(self.search_input)
            self.search_filter_layout.add_widget(search_section)
            
            # Filter section
            filter_section = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=5)
            filter_section.add_widget(Label(text="Filter By:", size_hint=(0.25, 1)))
            self.filter_button = Button(
                text="All Fields", size_hint=(0.75, 1), background_color=BUTTON_COLOR
            )
            filter_section.add_widget(self.filter_button)
            self.search_filter_layout.add_widget(filter_section)
            
            # Clear button section
            clear_section = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=5)
            clear_section.add_widget(Label(text="", size_hint=(0.25, 1)))  # Spacer
            self.clear_filter_button = Button(
                text="Clear Filter", size_hint=(0.75, 1), background_color=BUTTON_COLOR
            )
            clear_section.add_widget(self.clear_filter_button)
            self.search_filter_layout.add_widget(clear_section)
        else:
            self.search_filter_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=self.spacing)
            
            # Search input
            self.search_filter_layout.add_widget(Label(text="Search:", size_hint=(None, 1), width=70))
            self.search_input = TextInput(multiline=False, size_hint=(0.5, 1))
            self.search_filter_layout.add_widget(self.search_input)

            # Filter type dropdown
            self.search_filter_layout.add_widget(Label(text="Filter By:", size_hint=(None, 1), width=70))
            self.filter_button = Button(
                text="All Fields", size_hint=(0.3, 1), background_color=BUTTON_COLOR
            )
            self.search_filter_layout.add_widget(self.filter_button)

            # Clear filter button
            self.clear_filter_button = Button(
                text="Clear", size_hint=(0.2, 1), background_color=BUTTON_COLOR
            )
            self.search_filter_layout.add_widget(self.clear_filter_button)
        
        # Bind events
        self.search_input.bind(text=self._on_search_change)
        self.filter_button.bind(on_release=self._show_filter_options)
        self.clear_filter_button.bind(on_release=self._clear_search_filter)

        self.add_widget(self.search_filter_layout)

    def _create_tabbed_panel(self):
        """Create the tabbed panel for accounts."""
        self.tab_panel = TabbedPanel(
            do_default_tab=False,
            tab_width=150,
            tab_height=40,
            background_color=BG_COLOR,
            size_hint=(1, 1),
        )
        self.tab_panel.bind(on_tab_switch=self.on_tab_switch)

        # Create main tabs
        self._create_all_transactions_tab()
        self._create_visualization_tab()

        self.add_widget(self.tab_panel)

    def _create_all_transactions_tab(self):
        """Create the 'All Transactions' tab."""
        self.all_transactions_tab = TabbedPanelHeader(text="All Transactions")

        # Content for "All Transactions" tab
        all_content = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Status label
        self.all_transactions_status = Label(
            text="All Transactions", 
            size_hint=(1, None), 
            height=UIConstants.ROW_HEIGHT
        )
        all_content.add_widget(self.all_transactions_status)

        # Pagination controls
        self._create_pagination_controls(all_content)

        # Scroll view for transactions
        scroll_view = ScrollView(size_hint=(1, 1))

        # Grid for transactions
        self.all_transactions_grid = GridLayout(
            cols=len(UIConstants.TRANSACTION_HEADERS), 
            spacing=2, 
            size_hint_y=None
        )
        self.all_transactions_grid.bind(
            minimum_height=self.all_transactions_grid.setter("height")
        )

        # Add grid to scroll view
        scroll_view.add_widget(self.all_transactions_grid)

        # Add scroll view to content
        all_content.add_widget(scroll_view)

        # Set content for tab
        self.all_transactions_tab.content = all_content

        # Add tab to panel
        self.tab_panel.add_widget(self.all_transactions_tab)
        self.tab_panel.default_tab = self.all_transactions_tab

    def _create_visualization_tab(self):
        """Create the 'Charts' tab."""
        self.visualization_tab = TabbedPanelHeader(text="Charts")

        # Create visualization content
        self.visualization_content = VisualizationTab()
        self.visualization_content.set_parent_app(self)

        # Set content for tab
        self.visualization_tab.content = self.visualization_content

        # Add tab to panel
        self.tab_panel.add_widget(self.visualization_tab)

    def _create_exit_button(self):
        """Create responsive exit and settings buttons."""
        self.exit_layout = BoxLayout(size_hint=(1, None), height=40, spacing=self.spacing)

        if self.is_mobile:
            # On mobile, create two buttons side by side
            settings_button = Button(
                text="Settings", size_hint=(0.5, 1), background_color=(0.2, 0.6, 1, 1)
            )
            exit_button = Button(
                text="Exit", size_hint=(0.5, 1), background_color=BUTTON_COLOR
            )
            settings_button.bind(on_release=self.open_settings)
            exit_button.bind(on_release=self.exit_app)
            self.exit_layout.add_widget(settings_button)
            self.exit_layout.add_widget(exit_button)
        else:
            # Add spacer on larger screens
            self.exit_layout.add_widget(Widget(size_hint=(0.6, 1)))
            
            # Settings button
            settings_button = Button(
                text="Settings", size_hint=(0.2, 1), background_color=(0.2, 0.6, 1, 1)
            )
            settings_button.bind(on_release=self.open_settings)
            self.exit_layout.add_widget(settings_button)
            
            # Exit button
            exit_button = Button(
                text="Exit", size_hint=(0.2, 1), background_color=BUTTON_COLOR
            )
            exit_button.bind(on_release=self.exit_app)
            self.exit_layout.add_widget(exit_button)

        self.add_widget(self.exit_layout)

    def load_account_specific_tabs(self):
        """Load account-specific tabs asynchronously."""
        # Show loading indicator on the main status
        if hasattr(self, 'all_transactions_status'):
            self.loading_indicator.show(self.all_transactions_status, "Loading accounts...")
        
        # Create async operation for getting accounts
        accounts_operation = AsyncDatabaseOperation(
            target_func=get_all_accounts,
            args=(self.db_path,),
            success_callback=self._on_accounts_loaded,
            error_callback=self._on_accounts_error
        )
        accounts_operation.start()
        
    def _on_accounts_loaded(self, result):
        """Handle successful accounts loading."""
        error, accounts_df = result
        
        if error:
            self._on_accounts_error(error)
            return
            
        if accounts_df is None or accounts_df.empty:
            self.loading_indicator.hide()
            show_popup("No Accounts", "No accounts found in the database.")
            return

        # Create a tab for each account
        for _, account in accounts_df.iterrows():
            self._create_account_tab(account)
            
        # Hide loading indicator
        self.loading_indicator.hide()
        
    def _on_accounts_error(self, error):
        """Handle accounts loading error."""
        self.loading_indicator.hide()
        show_popup("Error", error)

    def _create_account_tab(self, account):
        """Create a tab for a specific account."""
        account_id = account["ACCOUNTID"]
        account_name = account["ACCOUNTNAME"]
        initial_balance = account["INITIALBAL"]

        # Create tab header and content
        tab = TabbedPanelHeader(text=account_name)
        content = AccountTabContent(account_id, account_name, initial_balance)
        tab.content = content

        # Add tab to panel
        self.tab_panel.add_widget(tab)

        # Store tab for reference
        self.account_tabs[account_id] = {
            "tab": tab,
            "content": content,
            "name": account_name,
            "initial_balance": initial_balance,
        }

        # Calculate and display initial balance
        self._update_account_balance(account_id, content)



    def _show_filter_options(self, instance):
        """Show filter options popup."""
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Filter options
        options = ["All Fields", "Account", "Payee", "Category", "Notes", "Tags"]

        for option in options:
            btn = Button(text=option, size_hint_y=None, height=40)
            btn.bind(
                on_release=lambda btn, opt=option: self._select_filter_option(opt, popup)
            )
            content.add_widget(btn)

        # Cancel button
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40)
        cancel_btn.bind(on_release=lambda x: popup.dismiss())
        content.add_widget(cancel_btn)

        popup = Popup(
            title="Select Filter Type",
            content=content,
            size_hint=(None, None),
            size=(300, 300),
            auto_dismiss=True
        )
        popup.open()

    def _select_filter_option(self, option, popup):
        """Select a filter option."""
        self.filter_button.text = option
        popup.dismiss()
        self._apply_search_filter()

    def _on_search_change(self, *args):
        """Handle search input changes."""
        # Reset to first page when search changes
        self.current_page = 1
        self._load_paginated_data()

    def _apply_search_filter(self, *args):
        """Apply search filter to transactions."""
        if self.all_transactions_df.empty:
            return

        search_text = self.search_input.text.lower()
        filter_type = self.filter_button.text

        if not search_text:
            self.filtered_transactions_df = self.all_transactions_df
        else:
            self.filtered_transactions_df = self._filter_transactions(search_text, filter_type)

        # Update only the current active tab efficiently
        self._update_current_tab()

    def _filter_transactions(self, search_text, filter_type):
        """Filter transactions based on search text and filter type."""
        filter_columns = {
            "All Fields": ["ACCOUNTNAME", "PAYEENAME", "CATEGNAME", "NOTES", "TAGNAMES"],
            "Account": ["ACCOUNTNAME"],
            "Payee": ["PAYEENAME"],
            "Category": ["CATEGNAME"],
            "Notes": ["NOTES"],
            "Tags": ["TAGNAMES"]
        }

        columns = filter_columns.get(filter_type, ["ACCOUNTNAME"])
        mask = False
        
        for col in columns:
            mask = mask | self.all_transactions_df[col].astype(str).str.lower().str.contains(search_text, na=False)
        
        return self.all_transactions_df[mask]

    def _update_current_tab(self):
        """Efficiently update only the current active tab."""
        current_tab = self.tab_panel.current_tab
        if current_tab.text == "All Transactions":
            self._update_all_transactions_tab()
        elif current_tab.text == "Charts":
            self.update_visualization()
        else:
            self._update_account_tab(current_tab.text)

    def sort_transactions(self, column_header):
        """Sort transactions based on the selected column."""
        if self.current_sort_column == column_header:
            self.current_sort_ascending = not self.current_sort_ascending
        else:
            self.current_sort_column = column_header
            self.current_sort_ascending = True

        if not self.filtered_transactions_df.empty:
            self.filtered_transactions_df.sort_values(
                by=self.current_sort_column,
                ascending=self.current_sort_ascending,
                inplace=True
            )

        # Update only the current active tab efficiently
        self._update_current_tab()

    def _clear_search_filter(self, instance):
        """Clear search filter."""
        self.search_input.text = ""
        self.filter_button.text = "All Fields"
        # Reset to first page when clearing filter
        self.current_page = 1
        self._load_paginated_data()
        
    def on_transaction_row_click(self, transaction_data):
        """Handle click on a transaction row.
        
        Args:
            transaction_data: Dictionary containing transaction information
        """
        # Create and show transaction details popup
        details_popup = TransactionDetailsPopup(
            transaction_data,
            on_save_callback=self._on_transaction_save,
            on_delete_callback=self._on_transaction_delete
        )
        details_popup.show()
    
    def _on_transaction_save(self, updated_data):
        """Handle saving updated transaction data.
        
        Args:
            updated_data: Dictionary containing updated transaction information
        """
        # For now, just show a confirmation popup
        # In a future implementation, this would update the database
        show_popup("Transaction Updated", "Transaction details have been updated.")
        

    
    def _on_transaction_delete(self, transaction_data):
        """Handle deleting a transaction.
        
        Args:
            transaction_data: Dictionary containing transaction information to delete
        """
        # For now, just show a confirmation popup
        # In a future implementation, this would delete from the database
        show_popup("Transaction Deleted", "Transaction has been deleted.")

    def _create_pagination_controls(self, parent_layout):
        """Create pagination controls for the All Transactions tab.
        
        Args:
            parent_layout: Parent layout to add pagination controls to
        """
        # Pagination layout
        if self.is_mobile:
            self.pagination_layout = BoxLayout(
                orientation='vertical', 
                size_hint=(1, None), 
                height=80, 
                spacing=5
            )
            
            # Page info row
            page_info_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.5))
            self.pagination_info_label = Label(
                text="No data", 
                size_hint=(1, 1),
                text_size=(None, None),
                halign='center'
            )
            page_info_layout.add_widget(self.pagination_info_label)
            self.pagination_layout.add_widget(page_info_layout)
            
            # Navigation buttons row
            nav_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.5), spacing=10)
            self.prev_button = Button(
                text="Previous", 
                size_hint=(0.33, 1), 
                background_color=BUTTON_COLOR,
                disabled=True
            )
            self.page_input = TextInput(
                text="1", 
                size_hint=(0.34, 1), 
                multiline=False,
                input_filter='int',
                halign='center'
            )
            self.next_button = Button(
                text="Next", 
                size_hint=(0.33, 1), 
                background_color=BUTTON_COLOR,
                disabled=True
            )
            nav_layout.add_widget(self.prev_button)
            nav_layout.add_widget(self.page_input)
            nav_layout.add_widget(self.next_button)
            self.pagination_layout.add_widget(nav_layout)
        else:
            self.pagination_layout = BoxLayout(
                orientation='horizontal', 
                size_hint=(1, None), 
                height=40, 
                spacing=10
            )
            
            # Previous button
            self.prev_button = Button(
                text="Previous", 
                size_hint=(None, 1), 
                width=100, 
                background_color=BUTTON_COLOR,
                disabled=True
            )
            self.pagination_layout.add_widget(self.prev_button)
            
            # Page info and input
            self.pagination_info_label = Label(
                text="No data", 
                size_hint=(0.6, 1),
                text_size=(None, None),
                halign='center'
            )
            self.pagination_layout.add_widget(self.pagination_info_label)
            
            # Page input
            page_input_layout = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=120, spacing=5)
            page_input_layout.add_widget(Label(text="Page:", size_hint=(None, 1), width=40))
            self.page_input = TextInput(
                text="1", 
                size_hint=(None, 1), 
                width=60, 
                multiline=False,
                input_filter='int'
            )
            page_input_layout.add_widget(self.page_input)
            self.pagination_layout.add_widget(page_input_layout)
            
            # Next button
            self.next_button = Button(
                text="Next", 
                size_hint=(None, 1), 
                width=100, 
                background_color=BUTTON_COLOR,
                disabled=True
            )
            self.pagination_layout.add_widget(self.next_button)
        
        # Bind events
        self.prev_button.bind(on_release=self._on_previous_page)
        self.next_button.bind(on_release=self._on_next_page)
        self.page_input.bind(on_text_validate=self._on_page_input_change)
        
        parent_layout.add_widget(self.pagination_layout)

    def _on_previous_page(self, instance):
        """Handle previous page button click."""
        if self.current_page > 1:
            self.current_page -= 1
            self._load_paginated_data()

    def _on_next_page(self, instance):
        """Handle next page button click."""
        if self.pagination_info and self.pagination_info.has_next:
            self.current_page += 1
            self._load_paginated_data()

    def _on_page_input_change(self, instance):
        """Handle page input change."""
        try:
            page = int(instance.text)
            if self.pagination_info and 1 <= page <= self.pagination_info.total_pages:
                self.current_page = page
                self._load_paginated_data()
            else:
                # Reset to current page if invalid
                instance.text = str(self.current_page)
        except ValueError:
            # Reset to current page if not a number
            instance.text = str(self.current_page)

    def _update_pagination_controls(self):
        """Update pagination control states and labels."""
        if not self.pagination_info:
            self.pagination_info_label.text = "No data"
            self.prev_button.disabled = True
            self.next_button.disabled = True
            self.page_input.text = "1"
            return
        
        # Update info label
        self.pagination_info_label.text = self.pagination_info.get_page_info_text()
        
        # Update button states
        self.prev_button.disabled = not self.pagination_info.has_previous
        self.next_button.disabled = not self.pagination_info.has_next
        
        # Update page input
        self.page_input.text = str(self.current_page)

    def _load_paginated_data(self):
        """Load paginated transaction data asynchronously."""
        start_date_str = self.start_date_input.get_date() if hasattr(self.start_date_input, 'get_date') else self.start_date_input.text
        end_date_str = self.end_date_input.get_date() if hasattr(self.end_date_input, 'get_date') else self.end_date_input.text

        # Show loading indicator
        self.loading_indicator.show(self.all_transactions_status, "Loading transactions...")
        
        # Create async operation for getting transaction count
        count_operation = AsyncDatabaseOperation(
            target_func=get_transaction_count,
            args=(self.db_path, start_date_str, end_date_str),
            success_callback=self._on_count_loaded,
            error_callback=self._on_count_error
        )
        count_operation.start()

    def _on_count_loaded(self, result):
        """Handle successful transaction count loading."""
        error, self.total_count = result
        
        if error:
            self._on_count_error(error)
            return
            
        # Create pagination info
        self.pagination_info = PaginationInfo(self.total_count, self.page_size, self.current_page)
        
        # Now load the actual transactions
        start_date_str = self.start_date_input.get_date() if hasattr(self.start_date_input, 'get_date') else self.start_date_input.text
        end_date_str = self.end_date_input.get_date() if hasattr(self.end_date_input, 'get_date') else self.end_date_input.text
        
        transactions_operation = AsyncDatabaseOperation(
            target_func=get_transactions,
            args=(self.db_path, start_date_str, end_date_str, self.page_size, self.current_page),
            success_callback=self._on_transactions_loaded,
            error_callback=self._on_transactions_error
        )
        transactions_operation.start()
        
    def _on_count_error(self, error):
        """Handle transaction count loading error."""
        self.loading_indicator.hide()
        show_popup("Error", f"Error getting transaction count: {error}")
        
    def _on_transactions_loaded(self, result):
        """Handle successful transactions loading."""
        error, self.all_transactions_df = result
        
        if error:
            self._on_transactions_error(error)
            return
            
        # Apply search filter to paginated data
        self._apply_search_filter()
        
        # Update pagination controls
        self._update_pagination_controls()
        
        # Hide loading indicator
        self.loading_indicator.hide()
        
    def _on_transactions_error(self, error):
        """Handle transactions loading error."""
        self.loading_indicator.hide()
        show_popup("Error", error)
        self.all_transactions_df = pd.DataFrame()
        self._apply_search_filter()
        self._update_pagination_controls()
        


    def update_visualization(self):
        """Update the visualization based on the selected chart type."""
        self.visualization_content.chart_layout.clear_widgets()

        if self.filtered_transactions_df.empty:
            self.visualization_content.chart_layout.add_widget(
                Label(text="No transaction data available for visualization")
            )
            return

        self.visualization_content.update_chart(self.filtered_transactions_df)

    def exit_app(self, instance):
        """Exit the application."""
        App.get_running_app().stop()

    def open_settings(self, instance):
        """Open the settings configuration popup."""
        settings_popup = SettingsPopup(config_manager)
        settings_popup.open()


class MMEXKivyApp(App):
    """Main application class."""

    def build(self):
        """Build and configure the application."""
        self._configure_window()
        self._configure_fonts()
        return MMEXAppLayout()

    def _configure_window(self):
        """Configure window properties."""
        Window.size = (1200, 800)
        Window.minimum_width, Window.minimum_height = 800, 600
        Window.bind(on_resize=self._on_window_resize)

    def _configure_fonts(self):
        """Configure global font settings."""
        Builder.load_string(f"""
        #:kivy 2.1.0
        <Label>:
            font_name: '{UNICODE_FONT_PATH}'
            text_size: self.width, None
            halign: 'left'
            valign: 'middle'
        <Button>:
            font_name: '{UNICODE_FONT_PATH}'
        <TextInput>:
            font_name: '{UNICODE_FONT_PATH}'
        """)

    def _on_window_resize(self, instance, width, height):
        """Handle window resize events."""
        if hasattr(self.root, 'tab_panel'):
            new_tab_width = max(100, min(150, width / 8))
            self.root.tab_panel.tab_width = new_tab_width


if __name__ == "__main__":
    MMEXKivyApp().run()
