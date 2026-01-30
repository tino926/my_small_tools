"""Account Components for the MMEX Kivy application.

This module provides UI components for account-related functionality.
"""

# Standard library imports
import logging
from typing import Any, Callable, Dict, Optional

# Third-party imports
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

# Local imports
try:
    from error_handling import handle_database_operation, is_valid_date_format
except ImportError:
    # Fallback if error_handling module is not available
    def handle_database_operation(func, *args, **kwargs):
        return None, func(*args, **kwargs)

from ui.base import BaseUIComponent
from ui.config import ui_config, show_popup
from ui.transaction import populate_grid_with_dataframe, SortableHeaderButton

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# ACCOUNT COMPONENTS
# =============================================================================


class AccountTabContent(BaseUIComponent):
    """Content for account-specific tabs with responsive design."""

    def __init__(self, account_id: int, account_name: str, initial_balance: float = 0.0, **kwargs):
        """
        Initialize AccountTabContent.

        Args:
            account_id: Unique identifier for the account
            account_name: Display name for the account
            initial_balance: Starting balance for the account
            **kwargs: Additional keyword arguments
        """
        super(AccountTabContent, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.account_id = account_id
        self.account_name = account_name
        self.initial_balance = initial_balance

        # Create account-specific UI components
        self._create_account_header()
        self._create_results_area()
        self._create_balance_display()

    def _create_account_header(self):
        """Create the account header with account information."""
        header_layout = self._create_responsive_layout(
            orientation='horizontal',
            size_hint_y=None,
            height=self.ui_config.responsive.button_height * 2
        )

        # Account name label
        account_label = self.create_label(
            f"Account: {self.account_name}",
            size_hint_x=0.7,
            bold=True
        )
        header_layout.add_widget(account_label)

        # Account ID label
        id_label = self.create_label(
            f"ID: {self.account_id}",
            size_hint_x=0.3,
            halign='right'
        )
        header_layout.add_widget(id_label)

        self.add_widget(header_layout)

    def _create_results_area(self):
        """Create the area for displaying account transaction results."""
        # Results label
        self.results_label = self.create_label(
            "Loading transactions...",
            size_hint_y=None,
            height=self.ui_config.responsive.button_height
        )
        self.add_widget(self.results_label)

        # Create grid for results
        self.results_grid = GridLayout(
            cols=7,  # Same as main transaction grid
            size_hint_y=None,
            spacing=2
        )
        self.results_grid.bind(minimum_height=self.results_grid.setter('height'))

        # Add scroll view
        scroll_view = ScrollView(size_hint=(1, 0.7))
        scroll_view.add_widget(self.results_grid)
        self.add_widget(scroll_view)

    def _create_balance_display(self):
        """Create the balance display area."""
        balance_layout = self._create_responsive_layout(
            orientation='horizontal',
            size_hint_y=None,
            height=self.ui_config.responsive.button_height
        )

        # Balance label
        self.balance_label = self.create_label(
            "Balance: Calculating...",
            size_hint_x=0.7
        )
        balance_layout.add_widget(self.balance_label)

        # Spacer
        balance_layout.add_widget(self.create_label("", size_hint_x=0.3))

        self.add_widget(balance_layout)

    def _create_responsive_layout(self, **kwargs):
        """Create a layout with responsive properties."""
        layout = BoxLayout(**kwargs)
        layout.padding = self.ui_config.responsive.padding
        layout.spacing = self.ui_config.responsive.spacing
        return layout

    def update_results(self, transactions_df):
        """Update the transaction results display.

        Args:
            transactions_df: DataFrame containing account transactions
        """
        try:
            # Update results label
            count = len(transactions_df) if transactions_df is not None else 0
            self.results_label.text = f"{count} transactions for {self.account_name}"

            # Populate grid with transaction data
            if transactions_df is not None and not transactions_df.empty:
                populate_grid_with_dataframe(
                    self.results_grid,
                    transactions_df,
                    ["Date", "Account", "Payee", "Category", "Tags", "Notes", "Amount"],
                    sort_callback=self._handle_sort,
                    row_click_callback=self._handle_row_click
                )
            else:
                # Clear grid if no transactions
                self.results_grid.clear_widgets()
                self.results_grid.cols = 7
                # Add a single label indicating no transactions
                no_data_label = self.create_label("No transactions found for this account.")
                no_data_label.height = self.ui_config.responsive.button_height * 2
                self.results_grid.add_widget(no_data_label)
                self.results_grid.height = no_data_label.height

        except Exception as e:
            logger.error(f"Error updating account results: {e}")
            self.show_error(f"Error updating account results: {e}")

    def _handle_sort(self, column_header):
        """Handle sorting of transactions by column."""
        logger.info(f"Sorting by column: {column_header}")
        # This would typically trigger a resort of the data
        # For now, just log the event

    def _handle_row_click(self, transaction_data):
        """Handle clicking on a transaction row."""
        logger.info(f"Transaction row clicked: {transaction_data}")
        # This would typically open a detail view
        # For now, just log the event

    def update_balance(self, balance: float):
        """Update the displayed account balance.

        Args:
            balance: New balance amount to display
        """
        try:
            self.balance_label.text = f"Balance: ${balance:.2f}"
        except Exception as e:
            logger.error(f"Error updating balance display: {e}")
            self.balance_label.text = f"Balance: Error - {e}"

    def update_status(self, status_message: str):
        """Update the status display.

        Args:
            status_message: Status message to display
        """
        try:
            self.results_label.text = status_message
        except Exception as e:
            logger.error(f"Error updating status: {e}")