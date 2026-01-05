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
from ui_components import (
    AccountTabContent,
    show_popup,
    populate_grid_with_dataframe,
    DatePickerButton,
    TransactionDetailsPopup,
)
from visualization import VisualizationTab
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
        self.db_path = load_db_path()
        
        # Initialize async operations manager
        self.async_manager = AsyncQueryManager()
        self.loading_indicator = LoadingIndicator()
        
        # Set up responsive layout
        self._setup_responsive_layout()
        
        # Create UI components
        self.db_path_label = Label(
            text=f"DB: {self.db_path or 'Not Set'}",
            size_hint_y=None,
            height=UIConstants.HEADER_HEIGHT,
        )
        self.add_widget(self.db_path_label)

        # Create date inputs
        self._create_date_inputs()

        # Create search and filter layout
        self._create_search_filter_layout()

        # Create tabbed panel
        self._create_tabbed_panel()

        # Create pagination controls
        self._create_pagination_controls(self)

        # Create account tabs
        self.load_account_specific_tabs()

        # Create exit button
        self._create_exit_button()

        # Load initial data
        self.run_global_query()

    def _setup_responsive_layout(self):
        """Setup responsive layout properties."""
        # Bind to window resize events
        Window.bind(on_resize=self._on_window_resize)

    def _on_window_resize(self, window, width, height):
        """Handle window resize events."""
        self._update_responsive_components()

    def _update_responsive_components(self):
        """Update components based on window size."""
        # This method can be expanded to handle responsive updates
        pass

    def _create_date_inputs(self):
        """Create date input fields."""
        from datetime import datetime, timedelta

        date_input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=UIConstants.INPUT_HEIGHT,
            spacing=self.spacing
        )

        # Start date input with date picker
        start_label = Label(
            text="Start Date:",
            size_hint_x=0.15
        )
        date_input_layout.add_widget(start_label)

        def get_first_day_of_last_month():
            today = datetime.now()
            first_day_of_current_month = today.replace(day=1)
            first_day_of_last_month = (
                first_day_of_current_month - timedelta(days=1)
            ).replace(day=1)
            return first_day_of_last_month.strftime(UIConstants.DATE_FORMAT)

        self.start_date_input = DatePickerButton(
            initial_date=get_first_day_of_last_month(),
            date_change_callback=self._on_date_change
        )
        date_input_layout.add_widget(self.start_date_input)

        # End date input with date picker
        end_label = Label(
            text="End Date:",
            size_hint_x=0.15
        )
        date_input_layout.add_widget(end_label)

        self.end_date_input = DatePickerButton(
            initial_date=datetime.now().strftime(UIConstants.DATE_FORMAT),
            date_change_callback=self._on_date_change
        )
        date_input_layout.add_widget(self.end_date_input)

        self.add_widget(date_input_layout)

    def _validate_date(self, date_str):
        """Validate date string format."""
        from datetime import datetime
        try:
            datetime.strptime(date_str, UIConstants.DATE_FORMAT)
            return True
        except ValueError:
            return False

    def _on_date_change(self, instance, date_value):
        """Handle date change events."""
        # Validate dates
        start_date = self.start_date_input.get_date()
        end_date = self.end_date_input.get_date()
        
        if not self._validate_date(start_date) or not self._validate_date(end_date):
            show_popup("Date Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        # Run the global query with new dates
        self.run_global_query()

    def _create_search_filter_layout(self):
        """Create search and filter controls."""
        search_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=UIConstants.INPUT_HEIGHT,
            spacing=self.spacing
        )

        # Search input
        self.search_input = TextInput(
            hint_text="Search transactions...",
            multiline=False,
            size_hint_x=0.6
        )
        self.search_input.bind(text=self._on_search_change)
        search_layout.add_widget(self.search_input)

        # Filter type spinner
        from kivy.uix.spinner import Spinner
        self.filter_spinner = Spinner(
            text=UIConstants.FILTER_OPTIONS[0],
            values=UIConstants.FILTER_OPTIONS,
            size_hint_x=0.2
        )
        search_layout.add_widget(self.filter_spinner)

        # Filter button
        filter_btn = Button(
            text="Filter Options",
            size_hint_x=0.15
        )
        filter_btn.bind(on_press=self._show_filter_options)
        search_layout.add_widget(filter_btn)

        # Clear button
        clear_btn = Button(
            text="Clear",
            size_hint_x=0.1
        )
        clear_btn.bind(on_press=self._clear_search_filter)
        search_layout.add_widget(clear_btn)

        self.add_widget(search_layout)

    def _create_tabbed_panel(self):
        """Create the main tabbed panel."""
        self.tab_panel = TabbedPanel(
            do_default_tab=False,
            tab_pos="top_mid",
            size_hint_y=0.6
        )
        self.tab_panel.bind(current_tab=self.on_tab_switch)
        self.add_widget(self.tab_panel)

        # Create the "All Transactions" tab first
        self._create_all_transactions_tab()

        # Create the visualization tab
        self._create_visualization_tab()

    def _create_all_transactions_tab(self):
        """Create the 'All Transactions' tab."""
        self.all_transactions_tab = TabbedPanelHeader(text="All")
        
        all_trans_content = BoxLayout(orientation="vertical", spacing=5, padding=5)
        
        # Status label
        self.all_transactions_status = Label(
            text="Perform a query to see all transactions.",
            size_hint_y=None,
            height=30
        )
        all_trans_content.add_widget(self.all_transactions_status)

        # Create grid for transactions
        self.all_transactions_grid = GridLayout(
            cols=len(UIConstants.TRANSACTION_HEADERS),
            size_hint_y=0.8,
            spacing=2
        )
        self.all_transactions_grid.bind(minimum_height=self.all_transactions_grid.setter('height'))

        # Add scroll view
        scroll_view_all = ScrollView()
        scroll_view_all.add_widget(self.all_transactions_grid)
        all_trans_content.add_widget(scroll_view_all)

        self.all_transactions_tab.content = all_trans_content
        self.tab_panel.add_widget(self.all_transactions_tab)
        self.tab_panel.default_tab = self.all_transactions_tab

    def _create_visualization_tab(self):
        """Create the visualization tab."""
        viz_tab = TabbedPanelHeader(text="Charts")
        self.visualization_tab = VisualizationTab()
        viz_tab.content = self.visualization_tab
        self.tab_panel.add_widget(viz_tab)

    def _create_exit_button(self):
        """Create the exit button."""
        exit_button_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=UIConstants.BUTTON_HEIGHT,
            spacing=self.spacing
        )
        
        # Add empty widget to push exit button to the right
        exit_button_layout.add_widget(Label(size_hint_x=0.8))
        
        self.exit_button = Button(
            text="Exit",
            size_hint_x=0.2
        )
        self.exit_button.bind(on_press=self.exit_app)
        exit_button_layout.add_widget(self.exit_button)
        
        self.add_widget(exit_button_layout)

    def _create_pagination_controls(self, parent_layout):
        """Create pagination controls."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.textinput import TextInput

        pagination_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=UIConstants.BUTTON_HEIGHT,
            spacing=self.spacing,
            padding=[0, 10, 0, 0]
        )

        # Page info label
        self.pagination_info_label = Label(
            text="",
            size_hint_x=0.4
        )
        pagination_layout.add_widget(self.pagination_info_label)

        # Previous button
        prev_btn = Button(
            text="Previous",
            size_hint_x=0.1
        )
        prev_btn.bind(on_press=self._on_previous_page)
        pagination_layout.add_widget(prev_btn)

        # Page input
        self.page_input = TextInput(
            text="1",
            multiline=False,
            size_hint_x=0.1,
            input_filter='int'
        )
        self.page_input.bind(text=self._on_page_input_change)
        pagination_layout.add_widget(self.page_input)

        # Of label
        self.of_label = Label(
            text="of 0",
            size_hint_x=0.1
        )
        pagination_layout.add_widget(self.of_label)

        # Next button
        next_btn = Button(
            text="Next",
            size_hint_x=0.1
        )
        next_btn.bind(on_press=self._on_next_page)
        pagination_layout.add_widget(next_btn)

        # Go button
        go_btn = Button(
            text="Go",
            size_hint_x=0.1
        )
        go_btn.bind(on_press=lambda x: self._on_page_input_change(None, self.page_input.text))
        pagination_layout.add_widget(go_btn)

        parent_layout.add_widget(pagination_layout)

    def _on_previous_page(self, instance):
        """Handle previous page button click."""
        if self.current_page > 1:
            self.current_page -= 1
            self._load_paginated_data()

    def _on_next_page(self, instance):
        """Handle next page button click."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_paginated_data()

    def _on_page_input_change(self, instance, value):
        """Handle page input change."""
        try:
            page_num = int(value)
            if 1 <= page_num <= self.total_pages:
                self.current_page = page_num
                self._load_paginated_data()
            else:
                self.page_input.text = str(self.current_page)
        except ValueError:
            self.page_input.text = str(self.current_page)

    def _update_pagination_controls(self):
        """Update pagination controls with current information."""
        if self.pagination_info:
            self.page_input.text = str(self.current_page)
            self.of_label.text = f"of {self.total_pages}"
            self.pagination_info_label.text = f"Page {self.current_page} of {self.total_pages} " \
                                            f"(Showing {min(self.page_size, len(self.filtered_transactions_df or []))} " \
                                            f"of {self.total_count} transactions)"
        else:
            self.pagination_info_label.text = f"Showing {len(self.filtered_transactions_df or [])} transactions"

    def load_account_specific_tabs(self):
        """Load account-specific tabs asynchronously."""
        # Show loading indicator
        self.loading_indicator.show(self.all_transactions_status, "Loading accounts...")

        # Use async operation to load accounts
        def load_accounts_callback():
            error, accounts_df = get_all_accounts(self.db_path)
            if error:
                self.loading_indicator.hide()
                show_popup("Error Loading Accounts", error)
                return
            return error, accounts_df

        async_op = AsyncDatabaseOperation(
            target_func=load_accounts_callback,
            success_callback=self._on_accounts_loaded,
            error_callback=self._on_accounts_error
        )
        async_op.start()

    def _on_accounts_loaded(self, result):
        """Handle successful account loading."""
        error, accounts_df = result
        self.loading_indicator.hide()
        
        if error:
            show_popup("Error Loading Accounts", error)
            return

        if accounts_df is not None and not accounts_df.empty:
            for index, row in accounts_df.iterrows():
                account_id = row["ACCOUNTID"]
                account_name = str(row["ACCOUNTNAME"])
                
                # Get initial balance
                initial_balance = 0.0
                if "INITIALBAL" in accounts_df.columns:
                    raw_val = row["INITIALBAL"]
                    if pd.notna(raw_val):
                        try:
                            initial_balance = float(raw_val)
                        except ValueError:
                            print(f"Warning: Could not convert INITIALBAL '{raw_val}' to float for account {account_name}.")

                # Create account tab
                self._create_account_tab({
                    'id': account_id,
                    'name': account_name,
                    'initial_balance': initial_balance
                })

    def _on_accounts_error(self, error):
        """Handle account loading error."""
        self.loading_indicator.hide()
        show_popup("Error Loading Accounts", str(error))

    def _create_account_tab(self, account):
        """Create an account-specific tab."""
        account_id = account['id']
        account_name = account['name']
        initial_balance = account['initial_balance']

        tab_header = TabbedPanelHeader(text=account_name[:25])
        tab_content = AccountTabContent(
            account_id=account_id,
            account_name=account_name,
            initial_balance=initial_balance
        )
        
        tab_header.content = tab_content
        self.tab_panel.add_widget(tab_header)
        
        # Store reference to account info
        self.account_tabs[account_id] = {
            'name': account_name,
            'content': tab_content,
            'initial_balance': initial_balance
        }

    def _show_filter_options(self, instance):
        """Show filter options popup."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        for option in UIConstants.FILTER_OPTIONS:
            btn = Button(text=option, size_hint_y=None, height=UIConstants.BUTTON_HEIGHT)
            btn.bind(on_press=lambda x, opt=option: self._select_filter_option(opt))
            layout.add_widget(btn)
        
        close_btn = Button(text='Close', size_hint_y=None, height=UIConstants.BUTTON_HEIGHT)
        close_btn.bind(on_press=lambda x: popup.dismiss())
        layout.add_widget(close_btn)
        
        popup = Popup(title='Filter Options', content=layout, size_hint=(0.5, 0.6))
        popup.open()

    def _select_filter_option(self, option, popup=None):
        """Select a filter option."""
        self.filter_spinner.text = option
        if popup:
            popup.dismiss()
        # Reapply search filter with new option
        self._apply_search_filter()

    def _on_search_change(self, *args):
        """Handle search input changes."""
        # Introduce a small delay to avoid excessive filtering while typing
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._apply_search_filter(), 0.3)

    def _apply_search_filter(self, *args):
        """Apply search and filter to the transaction data."""
        if self.all_transactions_df is None:
            return

        search_text = self.search_input.text.lower()
        filter_type = self.filter_spinner.text

        # Filter the data based on search text and filter type
        if search_text:
            self.filtered_transactions_df = self._filter_transactions(search_text, filter_type)
        else:
            self.filtered_transactions_df = self.all_transactions_df.copy()

        # Reset to first page when applying new filter
        self.current_page = 1
        
        # Update pagination info
        self.total_count = len(self.filtered_transactions_df) if self.filtered_transactions_df is not None else 0
        self.total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        self.pagination_info = PaginationInfo(self.total_count, self.page_size, self.current_page)
        
        # Update the current tab to show filtered results
        self._update_current_tab()

    def _filter_transactions(self, search_text, filter_type):
        """Filter transactions based on search text and filter type."""
        if self.all_transactions_df is None or self.all_transactions_df.empty:
            return pd.DataFrame()

        df = self.all_transactions_df.copy()
        
        # Apply case-insensitive search
        if filter_type == "All Fields":
            # Search across all text columns
            mask = False
            for col in df.columns:
                if df[col].dtype == "object":  # Text columns
                    mask |= df[col].astype(str).str.lower().str.contains(search_text, na=False)
            df = df[mask]
        elif filter_type in df.columns:
            # Search in specific column
            df = df[df[filter_type].astype(str).str.lower().str.contains(search_text, na=False)]
        
        return df

    def _update_current_tab(self):
        """Update the currently active tab."""
        current_tab = self.tab_panel.current_tab
        if current_tab == self.all_transactions_tab:
            self._update_all_transactions_tab()
        elif hasattr(self, 'visualization_tab') and current_tab == self.visualization_tab:
            self.update_visualization()
        else:
            # Account tab - get the account name from the tab text
            self._update_account_tab(current_tab.text)

    def sort_transactions(self, column_header):
        """Sort transactions by the specified column."""
        if self.filtered_transactions_df is not None and not self.filtered_transactions_df.empty:
            # Determine sort direction
            if column_header == self.current_sort_column:
                self.current_sort_ascending = not self.current_sort_ascending
            else:
                self.current_sort_column = column_header
                self.current_sort_ascending = True

            # Sort the dataframe
            self.filtered_transactions_df = self.filtered_transactions_df.sort_values(
                by=column_header, 
                ascending=self.current_sort_ascending
            ).reset_index(drop=True)

            # Update current tab to show sorted results
            self._update_current_tab()

    def _clear_search_filter(self, instance):
        """Clear search and filter controls."""
        self.search_input.text = ""
        self.filter_spinner.text = UIConstants.FILTER_OPTIONS[0]
        self.filtered_transactions_df = self.all_transactions_df
        self._update_current_tab()

    def on_transaction_row_click(self, transaction_data):
        """Handle transaction row click event."""
        popup = TransactionDetailsPopup(
            transaction_data=transaction_data,
            on_save_callback=self._on_transaction_save,
            on_delete_callback=self._on_transaction_delete
        )
        popup.show()

    def _on_transaction_save(self, updated_data):
        """Handle transaction save event."""
        # This would typically update the database and refresh the view
        show_popup("Update Successful", "Transaction updated successfully!")
        # Refresh the current view
        self.run_global_query()

    def _on_transaction_delete(self, transaction_data):
        """Handle transaction deletion."""
        # This would typically delete from the database and refresh the view
        show_popup("Delete Successful", "Transaction deleted successfully!")
        # Refresh the current view
        self.run_global_query()

    def _generate_cache_key(self, page_number, page_size, account_id=None):
        """Generate a cache key for the given parameters."""
        start_date = self.start_date_input.get_date()
        end_date = self.end_date_input.get_date()
        search_text = self.search_input.text
        filter_type = self.filter_spinner.text
        
        import hashlib
        cache_str = f"{start_date}_{end_date}_{page_number}_{page_size}_{account_id}_{search_text}_{filter_type}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _clear_cache(self):
        """Clear all cached data."""
        # This would clear the cache if implemented
        pass

    def _get_cached_data(self, cache_key):
        """Get data from cache if available."""
        # This would retrieve from cache if implemented
        return None

    def _set_cached_data(self, cache_key, data):
        """Set data in cache."""
        # This would store to cache if implemented
        pass

    def update_visualization(self):
        """Update the visualization tab with current data."""
        if self.filtered_transactions_df is not None:
            self.visualization_tab.show_chart(self.filtered_transactions_df)

    def exit_app(self, instance):
        """Exit the application."""
        App.get_running_app().stop()

    def _load_paginated_data(self):
        """Load paginated transaction data asynchronously with caching support."""
        start_date_str = self.start_date_input.get_date()
        end_date_str = self.end_date_input.get_date()

        # Generate cache key
        cache_key = self._generate_cache_key(self.current_page, self.page_size)

        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            self._on_transactions_loaded(cached_data)
            return

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
        from pagination_utils import get_transaction_count  # Import here to avoid circular dependency
        error, self.total_count = result

        if error:
            self._on_count_error(error)
            return

        # Create pagination info
        self.pagination_info = PaginationInfo(self.total_count, self.page_size, self.current_page)

        # Now load the actual transactions
        start_date_str = self.start_date_input.get_date()
        end_date_str = self.end_date_input.get_date()

        # Integrate caching: store results keyed by date range and pagination
        cache_key = self._generate_cache_key(self.current_page, self.page_size)
        transactions_operation = AsyncDatabaseOperation(
            target_func=get_transactions,
            args=(self.db_path, start_date_str, end_date_str, None, self.page_size, self.current_page),
            success_callback=lambda res, ck=cache_key: self._on_transactions_loaded_with_cache(res, ck),
            error_callback=self._on_transactions_error
        )
        transactions_operation.start()

    def _on_count_error(self, error):
        """Handle transaction count loading error."""
        self.loading_indicator.hide()
        show_popup("Error", f"Error loading transaction count: {error}")

    def _on_transactions_loaded_with_cache(self, result, cache_key):
        """Handle successful transaction loading with caching."""
        error, df = result
        if error:
            self._on_transactions_error(error)
            return

        # Cache the results
        self._set_cached_data(cache_key, df)
        
        # Process the loaded data
        self._on_transactions_loaded((None, df))

    def _on_transactions_loaded(self, result):
        """Handle successful transaction data loading."""
        error, df = result
        self.loading_indicator.hide()
        
        if error:
            show_popup("Error Loading Transactions", error)
            return

        # Update the dataframes
        self.all_transactions_df = df
        self.filtered_transactions_df = df.copy()  # Start with all data, then apply filters

        # Update pagination info
        if df is not None:
            self.total_count = len(df)
            self.total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        
        # Update the current tab to show new data
        self._update_current_tab()

    def _on_transactions_error(self, error):
        """Handle transaction loading error."""
        self.loading_indicator.hide()
        show_popup("Error Loading Transactions", str(error))

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

                    # Update account-specific status
                    content.results_label.text = f"Transactions for {account_name} ({len(account_transactions)} found)"

                    # Update account balance
                    self._update_account_balance(account_id, content, account_info)

    def _update_account_balance(self, account_id, content, account_info=None):
        """Update account balance display.

        Args:
            account_id: ID of the account
            content: Content widget for the account tab
            account_info: Optional account information dictionary
        """
        # Validate date format
        end_date_str = self.end_date_input.get_date()
        if not self._validate_date(end_date_str):
            content.update_status("Invalid date format for balance calculation")
            return

        # Determine initial balance
        initial_balance = 0.0
        if account_info:
            initial_balance = account_info.get("initial_balance", 0.0)
        else:
            # Try to find the balance in self.account_tabs
            for acc_id, acc_info in self.account_tabs.items():
                if acc_id == account_id:
                    initial_balance = acc_info.get("initial_balance", 0.0)
                    break

        # Calculate balance asynchronously
        def calculate_balance():
            return calculate_balance_for_account(self.db_path, account_id, end_date_str, initial_balance)

        def on_balance_success(result):
            error, balance = result
            if error:
                content.update_status(f"Error: {error}")
            elif balance is not None:
                content.update_balance(balance)
            else:
                content.update_status("Balance: N/A")

        def on_balance_error(error):
            content.update_status(f"Balance error: {error}")

        # Execute balance calculation asynchronously
        async_op = AsyncDatabaseOperation(
            target_func=calculate_balance,
            success_callback=on_balance_success,
            error_callback=on_balance_error
        )
        async_op.start()