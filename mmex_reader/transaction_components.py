"""Transaction-specific UI components for the MMEX Kivy application.

This module provides UI components specifically for transaction management.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

# Third-party imports
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
import pandas as pd

# Local imports
from .base_components import BaseUIComponent, ui_config
from .date_components import DatePickerButton


class SortableHeaderButton(Button):
    """A button for table headers that supports sorting functionality."""

    def __init__(self, text='', column_name='', sort_callback=None, **kwargs):
        """
        Initialize SortableHeaderButton.

        Args:
            text: Header text to display
            column_name: Internal name of the column to sort
            sort_callback: Function to call when header is clicked for sorting
            **kwargs: Additional keyword arguments
        """
        super().__init__(**kwargs)
        self.text = text
        self.column_name = column_name
        self.sort_callback = sort_callback
        self.sort_ascending = True  # Track sort direction
        self.size_hint_y = None
        self.height = 40
        self.bold = True
        self.background_color = ui_config.colors.header
        self.color = (1, 1, 1, 1)  # White text

        # Bind click event
        self.bind(on_release=self.on_header_click)

    def on_header_click(self, instance):
        """Handle header click for sorting."""
        # Toggle sort direction
        self.sort_ascending = not self.sort_ascending

        # Update button text to show sort direction
        direction_symbol = " ↑" if self.sort_ascending else " ↓"
        base_text = self.text.replace(" ↑", "").replace(" ↓", "")
        self.text = base_text + direction_symbol

        # Call the sort callback
        if self.sort_callback:
            self.sort_callback(self.column_name, self.sort_ascending)


class AccountTabContent(BaseUIComponent):
    """Content for an account-specific tab with responsive design."""

    def __init__(self, account_id, account_name, initial_balance=0, **kwargs):
        """
        Initialize AccountTabContent.

        Args:
            account_id: ID of the account
            account_name: Name of the account
            initial_balance: Initial balance for the account
            **kwargs: Additional keyword arguments
        """
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.account_id = account_id
        self.account_name = account_name
        self.initial_balance = initial_balance

        # Set responsive properties based on screen size
        if ui_config.is_mobile:
            self.padding = 5
            self.spacing = 3
            self.is_mobile = True
        elif ui_config.is_mobile:  # tablet
            self.padding = 8
            self.spacing = 5
            self.is_mobile = False
        else:  # desktop
            self.padding = 10
            self.spacing = 10
            self.is_mobile = False

        self._create_header()
        self._setup_transaction_list()
        self._update_balance(initial_balance)

    def _create_header(self):
        """Create the account header with responsive layout."""
        try:
            # Account info header with responsive layout
            if self.is_mobile:
                # Stack account info vertically on mobile
                self.header = BoxLayout(
                    orientation='vertical',
                    size_hint=(1, None),
                    height=80 if ui_config.is_mobile else 90,
                    spacing=self.spacing
                )

                # Account name label
                self.account_label = self.create_label(
                    text=f"Account: {self.account_name}",
                    size_hint=(1, 0.5),
                    halign='center'
                )
                self.header.add_widget(self.account_label)

                # Balance label
                self.balance_label = self.create_label(
                    text="Balance: Calculating...",
                    size_hint=(1, 0.5),
                    halign='center'
                )
                self.header.add_widget(self.balance_label)
            else:
                # Horizontal layout for larger screens
                self.header = BoxLayout(
                    orientation='horizontal',
                    size_hint=(1, None),
                    height=40,
                    spacing=self.spacing
                )

                # Account name label
                self.account_label = self.create_label(
                    text=f"Account: {self.account_name}",
                    size_hint=(0.7, 1),
                    halign='left'
                )
                self.header.add_widget(self.account_label)

                # Balance label
                self.balance_label = self.create_label(
                    text="Balance: Calculating...",
                    size_hint=(0.3, 1),
                    halign='right'
                )
                self.header.add_widget(self.balance_label)

            self.add_widget(self.header)

        except Exception as e:
            logger.error(f"Error creating account header: {e}")
            # Fallback to simple header
            self.balance_label = self.create_label(
                text="Balance: Calculating...",
                size_hint=(0.3, 1),
                halign='right',
                valign='middle',
                text_size=(None, None)
            )
            self.header = BoxLayout(
                orientation='horizontal',
                size_hint=(1, None),
                height=40,
                spacing=self.spacing
            )
            self.account_label = self.create_label(
                text=f"Account: {self.account_name}",
                size_hint=(0.7, 1),
                halign='left'
            )
            self.header.add_widget(self.account_label)
            self.header.add_widget(self.balance_label)
            self.add_widget(self.header)

        # Results label
        self.results_label = self.create_label(
            text=f"Transactions for {self.account_name}",
            size_hint=(1, None),
            height=30,
            halign='left' if not self.is_mobile else 'center'
        )
        self.add_widget(self.results_label)

    def _setup_transaction_list(self):
        """Setup the transaction list with responsive layout."""
        # Transactions grid in a scroll view
        self.scroll_view = ScrollView(size_hint=(1, 1))  # Take all remaining space

        # Grid for transactions with responsive columns
        if self.is_mobile:
            # Fewer columns on mobile for better readability
            self.results_grid = GridLayout(cols=4, spacing=2, size_hint_y=None)
        else:
            # Full columns on larger screens
            self.results_grid = GridLayout(cols=7, spacing=2, size_hint_y=None)

        # The height will be set based on the children
        self.results_grid.bind(minimum_height=self.results_grid.setter('height'))

        # Add grid to scroll view
        self.scroll_view.add_widget(self.results_grid)

        # Add scroll view to main layout
        self.add_widget(self.scroll_view)

    def update_balance(self, balance):
        """Update the displayed balance."""
        self.balance_label.text = f"Balance: ${balance:.2f}"


class TransactionDetailsPopup(BaseUIComponent):
    """A popup component for displaying and editing transaction details."""

    def __init__(self, transaction_data, on_save_callback=None, on_delete_callback=None, **kwargs):
        """
        Initialize the transaction details popup.

        Args:
            transaction_data: Dictionary containing transaction information
            on_save_callback: Callback function when transaction is saved
            on_delete_callback: Callback function when transaction is deleted
            **kwargs: Additional keyword arguments
        """
        super().__init__(**kwargs)
        self.transaction_data = transaction_data.copy() if transaction_data else {}
        self.on_save_callback = on_save_callback
        self.on_delete_callback = on_delete_callback
        self.popup = None
        self.input_fields = {}

        # Field configurations with validation rules
        self.field_configs = [
            ('Transaction ID', 'TRANSID', False, 'text', self._validate_readonly, None, None),
            ('Date', 'TRANSDATE', True, 'text', self._validate_date, True, None),
            ('Account', 'ACCOUNTNAME', False, 'text', self._validate_readonly, None, None),
            ('Payee', 'PAYEENAME', True, 'text', self._validate_required, False, None),
            ('Category', 'CATEGNAME', True, 'text', self._validate_required, False, None),
            ('Amount', 'TRANSAMOUNT', True, 'text', self._validate_amount, True, None),
            ('Transaction Code', 'TRANSCODE', True, 'dropdown', None, False, ['Withdrawal', 'Deposit', 'Transfer']),
            ('Notes', 'NOTES', False, 'multiline', None, False, None),
            ('Tags', 'TAGNAMES', False, 'text', None, False, None),
            ('Status', 'STATUS', True, 'dropdown', None, False, ['None', 'Reconciled', 'Void', 'Follow up', 'Duplicate']),
            ('Follow Up', 'FOLLOWUPID', False, 'text', None, False, None)
        ]

    def show(self):
        """Display the transaction details popup."""
        try:
            content = self._create_content()

            # Create and show popup
            self.popup = Popup(
                title=f"Transaction Details - {self.transaction_data.get('TRANSDATE', 'Unknown Date')}",
                content=content,
                size_hint=(0.9, 0.9),
                auto_dismiss=False
            )
            self.popup.open()

        except Exception as e:
            logger.error(f"Error showing transaction details popup: {e}")
            self.show_error("Error displaying transaction details")

    def _create_content(self):
        """Create the main content layout for the popup."""
        try:
            main_layout = BoxLayout(
                orientation='vertical',
                padding=ui_config.responsive.padding,
                spacing=ui_config.responsive.spacing
            )

            # Create scroll view for form fields
            scroll = ScrollView()
            form_layout = GridLayout(
                cols=2,
                spacing=ui_config.responsive.spacing,
                size_hint_y=None,
                padding=ui_config.responsive.padding
            )
            form_layout.bind(minimum_height=form_layout.setter('height'))

            # Create form fields
            self._create_form_fields(form_layout)

            scroll.add_widget(form_layout)
            main_layout.add_widget(scroll)

            # Add button layout
            button_layout = self._create_button_layout()
            main_layout.add_widget(button_layout)

            return main_layout

        except Exception as e:
            logger.error(f"Error creating popup content: {e}")
            return self.create_label("Error creating content")

    def _create_form_fields(self, form_layout):
        """Create form fields based on configuration."""
        try:
            for field_config in self.field_configs:
                label_text, field_key, editable, field_type, validator, required = field_config[0:6]
                
                # Handle optional values for dropdowns
                allowed_values = field_config[6] if len(field_config) > 6 else None

                # Add label with required indicator
                label_text_display = f"{label_text}{'*' if required else ''}:"
                label = self.create_label(
                    text=label_text_display,
                    size_hint_y=None,
                    height=ui_config.responsive.input_height,
                    halign='right'
                )
                form_layout.add_widget(label)

                # Get field value
                value = str(self.transaction_data.get(field_key, '')) if self.transaction_data.get(field_key) is not None else ''

                # Create appropriate input widget
                widget = self._create_input_widget(field_config, value, editable)
                self.input_fields[field_key] = widget
                form_layout.add_widget(widget)

        except Exception as e:
            logger.error(f"Error creating form fields: {e}")
            form_layout.add_widget(self.create_label("Error creating form fields"))

    def _create_input_widget(self, field_config, value, editable):
        """Create appropriate input widget based on field type."""
        try:
            field_type = field_config[3]

            if field_type == 'multiline':
                return TextInput(
                    text=value,
                    multiline=True,
                    size_hint_y=None,
                    height=ui_config.responsive.input_height * 2,
                    readonly=not editable,
                    background_color=ui_config.colors.background
                )
            elif field_type == 'dropdown':
                allowed_values = field_config[6] if len(field_config) > 6 else []
                return Spinner(
                    text=value if value else (allowed_values[0] if allowed_values else ''),
                    values=allowed_values,
                    size_hint_y=None,
                    height=ui_config.responsive.input_height,
                    disabled=not editable,
                    background_color=ui_config.colors.background
                )
            else:  # Default to text input
                return TextInput(
                    text=value,
                    multiline=False,
                    size_hint_y=None,
                    height=ui_config.responsive.input_height,
                    readonly=not editable,
                    background_color=ui_config.colors.background
                )

        except Exception as e:
            logger.error(f"Error creating input widget: {e}")
            return self.create_label("Error creating input")

    def _create_button_layout(self):
        """Create the button layout."""
        try:
            button_layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=ui_config.responsive.button_height,
                spacing=ui_config.responsive.spacing
            )

            # Save button
            save_btn = self.create_button(
                text='Save Changes',
                size_hint_x=0.3,
                callback=self._on_save
            )
            button_layout.add_widget(save_btn)

            # Delete button
            delete_btn = self.create_button(
                text='Delete',
                callback=self._on_delete,
                size_hint_x=0.3
            )
            delete_btn.background_color = ui_config.colors.error
            button_layout.add_widget(delete_btn)

            # Cancel button
            cancel_btn = self.create_button(
                text='Cancel',
                callback=self._on_cancel,
                size_hint_x=0.3
            )
            button_layout.add_widget(cancel_btn)

            return button_layout

        except Exception as e:
            logger.error(f"Error creating button layout: {e}")
            return BoxLayout()

    def _validate_date(self, date_str):
        """Validate date format."""
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, ""
        except ValueError:
            return False, "Invalid date format (YYYY-MM-DD required)"

    def _validate_amount(self, amount_str):
        """Validate amount format."""
        try:
            if isinstance(amount_str, str):
                amount_str = amount_str.replace('$', '').replace(',', '')
            float(amount_str)
            return True, ""
        except ValueError:
            return False, "Invalid amount format"

    def _validate_required(self, value_str):
        """Validate that a required field is not empty."""
        if not value_str.strip():
            return False, "This field is required"
        return True, ""

    def _validate_readonly(self, value_str):
        """Validator for readonly fields (always passes)."""
        return True, ""

    def _validate_form(self):
        """Validate all form fields."""
        errors = []

        try:
            for field_config in self.field_configs:
                field_key = field_config[1]
                validator = field_config[4] if len(field_config) > 4 else None
                required = field_config[5] if len(field_config) > 5 else False

                widget = self.input_fields.get(field_key)
                if not widget:
                    continue

                value = getattr(widget, 'text', '')

                # Check required fields
                if required and not value.strip():
                    errors.append(f"{field_config[0]} is required")
                    continue

                # Run validator if provided
                if validator and value.strip():
                    is_valid, error_msg = validator(value)
                    if not is_valid:
                        errors.append(f"{field_config[0]}: {error_msg}")

            return len(errors) == 0, errors

        except Exception as e:
            logger.error(f"Error validating form: {e}")
            return False, ["Validation error occurred"]

    def _on_save(self, instance):
        """Handle save button press with improved validation."""
        try:
            # Validate form
            is_valid, errors = self._validate_form()
            if not is_valid:
                error_message = "\n".join(errors)
                self.show_error(error_message, title='Validation Error')
                return

            # Collect updated data from input fields
            updated_data = self.transaction_data.copy()

            for field_key, widget in self.input_fields.items():
                if hasattr(widget, 'text'):
                    updated_data[field_key] = widget.text

            # Call save callback if provided
            if self.on_save_callback:
                self.on_save_callback(updated_data)

            self.popup.dismiss()

        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            self.show_error("Error saving transaction")

    def _on_delete(self, instance):
        """Handle delete button press with confirmation."""
        try:
            # Create confirmation content
            content_layout = BoxLayout(orientation='vertical', spacing=10)
            content_layout.add_widget(
                self.create_label('Are you sure you want to delete this transaction?')
            )

            # Create button layout for confirmation
            button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)

            # Confirm delete button
            confirm_btn = self.create_button(
                text='Yes, Delete',
                callback=self._confirm_delete
            )
            confirm_btn.background_color = ui_config.colors.error
            button_layout.add_widget(confirm_btn)

            # Cancel button
            cancel_btn = self.create_button(
                text='Cancel',
                callback=self.dismiss_confirm_popup
            )
            button_layout.add_widget(cancel_btn)

            content_layout.add_widget(button_layout)

            # Create and show confirmation popup
            self.confirm_popup = Popup(
                title='Confirm Delete',
                content=content_layout,
                size_hint=(0.6, 0.4),
                auto_dismiss=False
            )
            self.confirm_popup.open()

        except Exception as e:
            logger.error(f"Error showing delete confirmation: {e}")
            self.show_error("Error showing delete confirmation")

    def _confirm_delete(self, instance):
        """Confirm and execute delete operation."""
        try:
            if self.on_delete_callback:
                self.on_delete_callback(self.transaction_data)
            self.confirm_popup.dismiss()
            self.popup.dismiss()
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            self.show_error("Error deleting transaction")

    def dismiss_confirm_popup(self, instance):
        """Dismiss the confirmation popup."""
        if hasattr(self, 'confirm_popup'):
            self.confirm_popup.dismiss()

    def _on_cancel(self, instance):
        """Handle cancel button press."""
        try:
            self.popup.dismiss()
        except Exception as e:
            logger.error(f"Error canceling popup: {e}")