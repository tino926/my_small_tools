"""Transaction Components for the MMEX Kivy application.

This module provides UI components for transaction-related functionality.
"""

# Standard library imports
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
import pandas as pd

# Third-party imports
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

# Local imports
try:
    from error_handling import handle_database_operation, is_valid_date_format
except ImportError:
    # Fallback if error_handling module is not available
    def handle_database_operation(func, *args, **kwargs):
        return None, func(*args, **kwargs)

from ui.base import BaseUIComponent
from ui.config import ui_config, create_popup, show_popup

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# TRANSACTION COMPONENTS
# =============================================================================


class SortableHeaderButton(Button):
    """A button for table headers that supports sorting functionality."""

    def __init__(self, header_text: str, column_index: int, sort_callback: Optional[Callable] = None, **kwargs):
        """
        Initialize SortableHeaderButton.

        Args:
            header_text: Text to display on the button
            column_index: Index of the column this header represents
            sort_callback: Function to call when the header is clicked
            **kwargs: Additional keyword arguments
        """
        super(SortableHeaderButton, self).__init__(**kwargs)
        self.header_text = header_text
        self.column_index = column_index
        self.sort_callback = sort_callback
        self.is_sorted_ascending = None  # None = not sorted, True = asc, False = desc

        # Set button text
        self.text = self._get_button_text()

        # Bind click event
        self.bind(on_release=self._on_click)

    def _get_button_text(self) -> str:
        """Get the text to display on the button, including sort indicator."""
        if self.is_sorted_ascending is None:
            return self.header_text
        elif self.is_sorted_ascending:
            return f"{self.header_text} ↑"
        else:
            return f"{self.header_text} ↓"

    def _on_click(self, instance):
        """Handle button click event."""
        if self.sort_callback:
            self.sort_callback(self.header_text)

    def set_sorted_state(self, is_ascending: Optional[bool]):
        """Update the sorted state of this header.

        Args:
            is_ascending: True for ascending, False for descending, None for not sorted
        """
        self.is_sorted_ascending = is_ascending
        self.text = self._get_button_text()


def populate_grid_with_dataframe(
    grid: GridLayout,
    df: pd.DataFrame,
    headers: List[str],
    sort_callback: Optional[Callable] = None,
    row_click_callback: Optional[Callable] = None
):
    """Populate a GridLayout with data from a pandas DataFrame.

    Args:
        grid: GridLayout to populate
        df: DataFrame containing the data
        headers: List of column headers
        sort_callback: Callback function for header clicks
        row_click_callback: Callback function for row clicks
    """
    try:
        # Clear existing widgets
        grid.clear_widgets()

        # Set number of columns
        grid.cols = len(headers)

        # Create header row with sortable buttons
        for i, header in enumerate(headers):
            header_btn = SortableHeaderButton(
                header_text=header,
                column_index=i,
                sort_callback=sort_callback
            )
            grid.add_widget(header_btn)

        # Add data rows
        for idx, row in df.iterrows():
            for col_idx, header in enumerate(headers):
                # Get cell value
                if header in row:
                    cell_value = str(row[header]) if pd.notna(row[header]) else ""
                else:
                    cell_value = ""

                # Create cell widget
                cell_label = Label(
                    text=cell_value,
                    size_hint_y=None,
                    height=ui_config.responsive.button_height,
                    halign='left',
                    valign='middle',
                    text_size=(None, ui_config.responsive.button_height)
                )
                
                # Bind click event to the entire row
                if row_click_callback:
                    # Store row data in the label for access in callback
                    cell_label.row_data = row.to_dict()
                    cell_label.bind(on_touch_down=lambda instance, touch: 
                                   _on_row_touch(instance, touch, row_click_callback) 
                                   if instance.collide_point(touch.x, touch.y) else False)
                
                grid.add_widget(cell_label)

        # Update grid height to accommodate all rows
        grid.height = ui_config.responsive.button_height * (len(df) + 1)  # +1 for header
        
    except Exception as e:
        logger.error(f"Error populating grid with DataFrame: {e}")
        show_popup("Error", f"Failed to populate grid: {e}")


def _on_row_touch(instance, touch, callback):
    """Handle touch events on row cells."""
    if instance.collide_point(touch.x, touch.y) and touch.is_double_tap:
        if hasattr(instance, 'row_data'):
            callback(instance.row_data)


class TransactionDetailsPopup(BaseUIComponent):
    """Popup for viewing and editing transaction details."""

    def __init__(self, transaction_data: Dict[str, Any], on_save_callback: Optional[Callable] = None, 
                 on_delete_callback: Optional[Callable] = None, **kwargs):
        """
        Initialize TransactionDetailsPopup.

        Args:
            transaction_data: Dictionary containing transaction details
            on_save_callback: Function to call when saving changes
            on_delete_callback: Function to call when deleting transaction
            **kwargs: Additional keyword arguments
        """
        super(TransactionDetailsPopup, self).__init__(**kwargs)
        self.transaction_data = transaction_data.copy()  # Make a copy to avoid modifying original
        self.original_data = transaction_data.copy()
        self.on_save_callback = on_save_callback
        self.on_delete_callback = on_delete_callback

        # Create popup content
        self._create_content()

    def _create_content(self):
        """Create the popup content."""
        # Main layout
        main_layout = BoxLayout(orientation='vertical', spacing=self.ui_config.responsive.spacing, padding=10)

        # Title
        title_label = self.create_label("Transaction Details", bold=True, font_size=18)
        main_layout.add_widget(title_label)

        # Create form fields for transaction data
        form_layout = self._create_form_fields()
        main_layout.add_widget(form_layout)

        # Action buttons
        button_layout = self._create_action_buttons()
        main_layout.add_widget(button_layout)

        # Create popup
        self.popup = create_popup(
            title='Transaction Details',
            content_widget=main_layout,
            size_hint=(0.8, 0.8)
        )

    def _create_form_fields(self) -> BoxLayout:
        """Create form fields for transaction data."""
        form_layout = GridLayout(cols=2, spacing=self.ui_config.responsive.spacing, size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter('height'))

        # Define fields to show
        fields = [
            ('Date', 'DATE'),
            ('Account', 'ACCOUNTNAME'),
            ('Payee', 'PAYEENAME'),
            ('Category', 'CATEGNAME'),
            ('Amount', 'TRANSAMOUNT'),
            ('Notes', 'NOTES'),
            ('Status', 'STATUS')
        ]

        self.field_inputs = {}
        
        for label_text, data_key in fields:
            # Add label
            label = self.create_label(label_text)
            form_layout.add_widget(label)

            # Add input field
            if data_key in self.transaction_data:
                initial_value = str(self.transaction_data[data_key]) if self.transaction_data[data_key] is not None else ""
            else:
                initial_value = ""
            
            input_field = self.create_text_input(text=initial_value)
            self.field_inputs[data_key] = input_field
            form_layout.add_widget(input_field)

        return form_layout

    def _create_action_buttons(self) -> BoxLayout:
        """Create action buttons for the popup."""
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=self.ui_config.responsive.button_height + 10,
            spacing=self.ui_config.responsive.spacing
        )

        # Save button
        save_btn = self.create_button(
            'Save',
            callback=self._on_save,
            background_color=self.ui_config.colors.success
        )
        button_layout.add_widget(save_btn)

        # Delete button
        delete_btn = self.create_button(
            'Delete',
            callback=self._on_delete,
            background_color=self.ui_config.colors.error
        )
        button_layout.add_widget(delete_btn)

        # Cancel button
        cancel_btn = self.create_button(
            'Cancel',
            callback=self._on_cancel
        )
        button_layout.add_widget(cancel_btn)

        return button_layout

    def _on_save(self, instance):
        """Handle save button click."""
        try:
            # Update transaction data with values from inputs
            for data_key, input_field in self.field_inputs.items():
                self.transaction_data[data_key] = input_field.text

            # Call save callback if provided
            if self.on_save_callback:
                self.on_save_callback(self.transaction_data)

            # Close popup
            self.popup.dismiss()
        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            self.show_error(f"Error saving transaction: {e}")

    def _on_delete(self, instance):
        """Handle delete button click."""
        try:
            # Call delete callback if provided
            if self.on_delete_callback and self.original_data:
                self.on_delete_callback(self.original_data)

            # Close popup
            self.popup.dismiss()
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            self.show_error(f"Error deleting transaction: {e}")

    def _on_cancel(self, instance):
        """Handle cancel button click."""
        self.popup.dismiss()

    def show(self):
        """Display the popup."""
        self.popup.open()