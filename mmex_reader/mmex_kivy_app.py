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

# Import custom modules
from db_utils import (
    load_db_path,
    get_all_accounts,
    get_transactions,
    calculate_balance_for_account,
    CATEGORY_TABLE,
    SUBCATEGORY_TABLE,
    ACCOUNT_TABLE,
    TRANSACTION_TABLE,
    PAYEE_TABLE,
    TAG_TABLE,
    TAGLINK_TABLE,
)
from ui_components import (
    AccountTabContent,
    show_popup,
    create_header_label,
    populate_grid_with_dataframe,
    BG_COLOR,
    HEADER_COLOR,
    BUTTON_COLOR,
    HIGHLIGHT_COLOR,
)
from visualization import (
    VisualizationTab,
    create_category_spending_chart,
    create_spending_over_time_chart,
    create_income_vs_expenses_chart,
    create_top_payees_chart,
)

import os
from datetime import datetime, timedelta

# Third-party imports
import kivy
import pandas as pd

# Kivy imports
kivy.require("2.1.0")  # replace with your Kivy version if needed
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget  # For spacer

# --- Script Directory ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Font Configuration ---
UNICODE_FONT_PATH = os.path.join(SCRIPT_DIR, "fonts", "NotoSansCJKtc-Regular.otf")


class MMEXAppLayout(BoxLayout):
    """Main layout for the MMEX Kivy application."""

    def __init__(self, **kwargs):
        super(MMEXAppLayout, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 10
        self.spacing = 10

        # Database path
        self.db_path = load_db_path()
        
        # Add sorting state variables
        self.current_sort_column = None
        self.current_sort_ascending = True

        # Date range inputs
        self._create_date_inputs()

        # Search and filter layout
        self._create_search_filter_layout()

        # Tabbed panel for accounts
        self._create_tabbed_panel()

        # Exit button
        self._create_exit_button()

        # Load account tabs
        self.load_account_specific_tabs()

        # Run initial query
        self.run_global_query()

    def run_global_query(self):
        """Execute the global transaction query and update the UI."""
        start_date_str = self.start_date_input.text
        end_date_str = self.end_date_input.text

        error, self.all_transactions_df = get_transactions(
            self.db_path, start_date_str, end_date_str
        )

        if error:
            show_popup("Error", error)
            self.all_transactions_df = pd.DataFrame()

        self.apply_search_filter()

    def on_tab_switch(self, instance, tab):
        """Handle tab switching to update content."""
        if tab.text == "All Transactions":
            populate_grid_with_dataframe(
                self.all_transactions_grid,
                self.filtered_transactions_df,
                self.filtered_transactions_df.columns.tolist(),
                sort_callback=self.sort_transactions,
            )
            self.all_transactions_status.text = f"{len(self.filtered_transactions_df)} transactions found"
        elif tab.text == "Charts":
            self.update_visualization()
        else:
            # Handle account-specific tabs
            account_name = tab.text
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
                            account_transactions.columns.tolist(),
                            sort_callback=self.sort_transactions,
                        )
                        content.results_label.text = f"{len(account_transactions)} transactions found"

                        # Update balance
                        try:
                            end_date = self.end_date_input.text
                            error, balance = calculate_balance_for_account(
                                self.db_path,
                                account_id,
                                account_info["initial_balance"],
                                datetime.strptime(end_date, "%Y-%m-%d"),
                            )
                            if error:
                                content.balance_label.text = f"Balance: Error"
                            else:
                                content.balance_label.text = f"Balance: ${balance:.2f}"
                        except Exception as e:
                            content.balance_label.text = f"Balance: Error"
                            print(f"Error calculating balance: {e}")
                    break

    def _create_date_inputs(self):
        """Create date input fields with validation."""
        date_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
    
        # Start date input - more responsive layout
        date_layout.add_widget(Label(text="Start Date:", size_hint=(None, 1), width=80))
    
        self.start_date_input = TextInput(
            text=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            multiline=False,
            size_hint=(0.5, 1),
        )
        self.start_date_input.bind(text=self.trigger_global_query_on_date_change)
        date_layout.add_widget(self.start_date_input)
    
        # End date input - more responsive layout
        date_layout.add_widget(Label(text="End Date:", size_hint=(None, 1), width=70))
    
        self.end_date_input = TextInput(
            text=datetime.now().strftime("%Y-%m-%d"),
            multiline=False,
            size_hint=(0.5, 1),
        )
        self.end_date_input.bind(text=self.trigger_global_query_on_date_change)
        date_layout.add_widget(self.end_date_input)
    
        self.add_widget(date_layout)

    def trigger_global_query_on_date_change(self, instance, value):
        """Trigger the global query when the date changes, with validation."""
        try:
            datetime.strptime(self.start_date_input.text, "%Y-%m-%d")
            datetime.strptime(self.end_date_input.text, "%Y-%m-%d")
            self.run_global_query()
        except ValueError:
            # Handle invalid date format
            pass

    def _create_search_filter_layout(self):
        """Create search and filter layout."""
        search_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
    
        # Search input - more responsive layout
        search_layout.add_widget(Label(text="Search:", size_hint=(None, 1), width=70))
    
        self.search_input = TextInput(multiline=False, size_hint=(0.5, 1))
        self.search_input.bind(text=self.apply_search_filter)
        search_layout.add_widget(self.search_input)
    
        # Filter type dropdown - more responsive layout
        search_layout.add_widget(Label(text="Filter By:", size_hint=(None, 1), width=70))
    
        self.filter_button = Button(
            text="All Fields", size_hint=(0.3, 1), background_color=BUTTON_COLOR
        )
        self.filter_button.bind(on_release=self.show_filter_options)
        search_layout.add_widget(self.filter_button)
    
        # Clear filter button - more responsive layout
        self.clear_filter_button = Button(
            text="Clear", size_hint=(0.2, 1), background_color=BUTTON_COLOR
        )
        self.clear_filter_button.bind(on_release=self.clear_search_filter)
        search_layout.add_widget(self.clear_filter_button)
    
        self.add_widget(search_layout)

    def _create_tabbed_panel(self):
        """Create the tabbed panel for accounts."""
        self.tab_panel = TabbedPanel(
            do_default_tab=False,
            tab_width=150,
            tab_height=40,
            background_color=BG_COLOR,
            size_hint=(1, 1),  # Take full available space
        )
    
        # Create "All Transactions" tab
        self._create_all_transactions_tab()
    
        # Create "Charts" tab
        self._create_visualization_tab()
    
        self.add_widget(self.tab_panel)

    def _create_all_transactions_tab(self):
        """Create the 'All Transactions' tab."""
        self.all_transactions_tab = TabbedPanelHeader(text="All Transactions")

        # Content for "All Transactions" tab
        all_content = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Status label
        self.all_transactions_status = Label(
            text="All Transactions", size_hint=(1, None), height=30
        )
        all_content.add_widget(self.all_transactions_status)

        # Scroll view for transactions
        scroll_view = ScrollView(size_hint=(1, 1))

        # Grid for transactions
        self.all_transactions_grid = GridLayout(cols=7, spacing=2, size_hint_y=None)
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
        """Create the exit button."""
        exit_layout = BoxLayout(size_hint=(1, None), height=40)

        # Add spacer
        exit_layout.add_widget(Widget(size_hint=(0.8, 1)))

        # Exit button
        exit_button = Button(
            text="Exit", size_hint=(0.2, 1), background_color=BUTTON_COLOR
        )
        exit_button.bind(on_release=self.exit_app)
        exit_layout.add_widget(exit_button)

        self.add_widget(exit_layout)

    def load_account_specific_tabs(self):
        """Load account-specific tabs."""
        error, accounts_df = get_all_accounts(self.db_path)

        if error:
            show_popup("Error", error)
            return

        if accounts_df is None or accounts_df.empty:
            show_popup("No Accounts", "No accounts found in the database.")
            return

        # Store account tabs for reference
        self.account_tabs = {}

        # Create a tab for each account
        for _, account in accounts_df.iterrows():
            account_id = account["ACCOUNTID"]
            account_name = account["ACCOUNTNAME"]
            initial_balance = account["INITIALBAL"]

            # Create tab header
            tab = TabbedPanelHeader(text=account_name)

            # Create tab content
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

            # Calculate initial balance
            try:
                end_date = self.end_date_input.text
                error, balance = calculate_balance_for_account(
                    self.db_path,
                    account_id,
                    initial_balance,
                    datetime.strptime(end_date, "%Y-%m-%d"),
                )

                if error:
                    content.balance_label.text = f"Balance: Error"
                else:
                    content.balance_label.text = f"Balance: ${balance:.2f}"
            except Exception as e:
                content.balance_label.text = f"Balance: Error"
                print(f"Error calculating balance: {e}")

                # Add headers and populate grid with sorting capability
                headers = ["Date", "Payee", "Category", "Tags", "Notes", "Amount"]
                populate_grid_with_dataframe(
                    content.results_grid, 
                    pd.DataFrame(),  # Empty DataFrame as placeholder since account_transactions is undefined
                    headers,
                    sort_callback=self.sort_transactions
                )
            else:
                content.results_label.text = (
                    f"No transactions found for {account_name}"
                )

                break

    def show_filter_options(self, instance):
        """Show filter options popup."""
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
    
        # Filter options
        options = ["All Fields", "Account", "Payee", "Category", "Notes", "Tags"]
    
        for option in options:
            btn = Button(text=option, size_hint_y=None, height=40)
            btn.bind(
                on_release=lambda btn, opt=option: self.select_filter_option(opt, popup)
            )
            content.add_widget(btn)
    
        # Cancel button
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40)
        cancel_btn.bind(on_release=lambda x: popup.dismiss())
        content.add_widget(cancel_btn)
    
        # More responsive popup size
        popup = Popup(
            title="Select Filter Type", 
            content=content, 
            size_hint=(None, None),
            size=(300, 300),  # Fixed size for small screens
            auto_dismiss=True
        )
        popup.open()

    def select_filter_option(self, option, popup):
        """Select a filter option."""
        self.filter_button.text = option
        popup.dismiss()
        self.apply_search_filter()

    def apply_search_filter(self, *args):
        """Apply search filter to transactions."""
        if not hasattr(self, "all_transactions_df") or self.all_transactions_df.empty:
            return

        search_text = self.search_input.text.lower()
        filter_type = self.filter_button.text

        if not search_text:
            # No filter, show all transactions
            self.filtered_transactions_df = self.all_transactions_df
        else:
            # Apply filter based on selected type
            if filter_type == "All Fields":
                # Search in all text columns
                mask = False
                for col in [
                    "ACCOUNTNAME",
                    "PAYEENAME",
                    "CATEGNAME",
                    "NOTES",
                    "TAGNAMES",
                ]:
                    mask = mask | self.all_transactions_df[col].astype(
                        str
                    ).str.lower().str.contains(search_text, na=False)
                self.filtered_transactions_df = self.all_transactions_df[mask]
            elif filter_type == "Account":
                mask = (
                    self.all_transactions_df["ACCOUNTNAME"]
                    .astype(str)
                    .str.lower()
                    .str.contains(search_text, na=False)
                )
                self.filtered_transactions_df = self.all_transactions_df[mask]
            elif filter_type == "Payee":
                mask = (
                    self.all_transactions_df["PAYEENAME"]
                    .astype(str)
                    .str.lower()
                    .str.contains(search_text, na=False)
                )
                self.filtered_transactions_df = self.all_transactions_df[mask]
            elif filter_type == "Category":
                mask = (
                    self.all_transactions_df["CATEGNAME"]
                    .astype(str)
                    .str.lower()
                    .str.contains(search_text, na=False)
                )
                self.filtered_transactions_df = self.all_transactions_df[mask]
            elif filter_type == "Notes":
                mask = (
                    self.all_transactions_df["NOTES"]
                    .astype(str)
                    .str.lower()
                    .str.contains(search_text, na=False)
                )
                self.filtered_transactions_df = self.all_transactions_df[mask]
            elif filter_type == "Tags":
                mask = (
                    self.all_transactions_df["TAGNAMES"]
                    .astype(str)
                    .str.lower()
                    .str.contains(search_text, na=False)
                )
                self.filtered_transactions_df = self.all_transactions_df[mask]

        # Update the active tab
        self.on_tab_switch(None, self.tab_panel.current_tab)

    def sort_transactions(self, column_header):
        """Sort transactions based on the selected column."""
        if self.current_sort_column == column_header:
            self.current_sort_ascending = not self.current_sort_ascending
        else:
            self.current_sort_column = column_header
            self.current_sort_ascending = True

        if hasattr(self, 'filtered_transactions_df') and not self.filtered_transactions_df.empty:
            self.filtered_transactions_df.sort_values(
                by=self.current_sort_column,
                ascending=self.current_sort_ascending,
                inplace=True
            )

        # Update the active tab to refresh the view
        self.on_tab_switch(None, self.tab_panel.current_tab)

    def clear_search_filter(self, instance):
        """Clear search filter."""
        self.search_input.text = ""
        self.filter_button.text = "All Fields"
        if hasattr(self, "all_transactions_df"):
            self.filtered_transactions_df = self.all_transactions_df
            self.on_tab_switch(None, self.tab_panel.current_tab)

    def update_visualization(self):
        """Update the visualization based on the selected chart type."""
        # Clear existing chart
        self.visualization_content.chart_layout.clear_widgets()

        # Check if we have transaction data
        if (
            not hasattr(self, "filtered_transactions_df")
            or self.filtered_transactions_df.empty
        ):
            self.visualization_content.chart_layout.add_widget(
                Label(text="No transaction data available for visualization")
            )
            return

        # Create chart based on selected type
        self.visualization_content.update_chart(self.filtered_transactions_df)

    def exit_app(self, instance):
        """Exit the application."""
        App.get_running_app().stop()


class MMEXKivyApp(App):
    """Main application class."""

    def build(self):
        # Set window size
        Window.size = (1200, 800)
        Window.minimum_width, Window.minimum_height = 800, 600
        
        # Enable window resizing events
        Window.bind(on_resize=self.on_window_resize)

        # Set global font
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

        return MMEXAppLayout()
        
    def on_window_resize(self, instance, width, height):
        """Handle window resize events."""
        # Update tab width based on window width
        app = App.get_running_app()
        if hasattr(app.root, 'tab_panel'):
            # Adjust tab width based on window width
            new_tab_width = max(100, min(150, width / 8))
            app.root.tab_panel.tab_width = new_tab_width


if __name__ == "__main__":
    MMEXKivyApp().run()
