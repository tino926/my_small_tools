"""UI utility functions for the MMEX application.

This module provides common UI utility functions that were originally in ui_components.py.
"""

import logging
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from datetime import datetime, timedelta

from .base_components import UIConfig, ui_config, create_popup as base_create_popup, show_popup as base_show_popup

logger = logging.getLogger(__name__)


def create_styled_label(text: str, label_type: str = 'data', num_columns: int = 1, **kwargs) -> Label:
    """Create a styled label with flexible configuration.

    Args:
        text: The label text
        label_type: 'header' or 'data' to determine styling
        num_columns: Number of columns for width calculation (data labels only)
        **kwargs: Additional Label properties to override defaults

    Returns:
        A styled Label widget
    """
    if label_type == 'header':
        defaults = {
            'text': text,
            'size_hint_y': None,
            'height': 40,
            'bold': True,
            'color': (1, 1, 1, 1)  # White text
        }
        defaults.update(kwargs)
        label = Label(**defaults)

        # Add background color
        with label.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*ui_config.colors.header)
            label.rect = Rectangle(pos=label.pos, size=label.size)

        # Update rectangle position and size when the label changes
        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        label.bind(pos=update_rect, size=update_rect)

    else:  # data label
        defaults = {
            'text': text,
            'size_hint_y': None,
            'height': 30,
            'size_hint_x': 1/num_columns,
            'text_size': (None, 30),
            'halign': 'left',
            'valign': 'middle',
            'shorten': True,
            'shorten_from': 'right'
        }
        defaults.update(kwargs)
        label = Label(**defaults)

        # Bind size to update text_size
        def update_text_size(instance, value):
            instance.text_size = (value, 30)

        label.bind(width=update_text_size)

    return label


def create_header_label(text: str):
    """Create a styled header label (deprecated - use create_styled_label)."""
    return create_styled_label(text, 'header')


def _create_data_label(text: str, num_columns: int):
    """Create a data label (deprecated - use create_styled_label)."""
    return create_styled_label(text, 'data', num_columns)


def _add_grid_headers(grid, display_headers, sort_callback, ui_config):
    """Add headers to the grid."""
    try:
        # Map headers to actual column names
        column_mapping = {
            "Date": "TRANSDATE",
            "Account": "ACCOUNTNAME", 
            "Payee": "PAYEENAME",
            "Category": "CATEGNAME",
            "Tags": "TAGNAMES",
            "Notes": "NOTES",
            "Amount": "TRANSAMOUNT"
        }

        for header in display_headers:
            if sort_callback and header in column_mapping:
                # Create sortable header button
                header_btn = SortableHeaderButton(
                    text=header,
                    column_name=column_mapping[header],
                    sort_callback=sort_callback,
                    size_hint_x=1/len(display_headers)
                )
                grid.add_widget(header_btn)
            else:
                # Create regular header label
                header_label = create_header_label(header)
                header_label.size_hint_x = 1/len(display_headers)
                grid.add_widget(header_label)

    except Exception as e:
        logger.error(f"Error adding grid headers: {e}")


def _format_cell_value(column_name: str, value) -> str:
    """Format cell value based on column type."""
    try:
        if column_name in ('TRANSAMOUNT', 'TOTRANSAMOUNT'):
            return f"${value:.2f}" if pd.notna(value) else ""
        elif column_name == 'TRANSDATE':
            return str(value).split()[0] if pd.notna(value) else ""
        else:
            return str(value) if pd.notna(value) else ""
    except Exception as e:
        logger.error(f"Error formatting cell value: {e}")
        return str(value) if value is not None else ""


def _add_grid_data_rows(grid, df, display_headers, row_click_callback, ui_config):
    """Add data rows to the grid."""
    try:
        # Map display headers to DataFrame columns
        header_to_column = {
            "Date": "TRANSDATE",
            "Account": "ACCOUNTNAME",
            "Payee": "PAYEENAME",
            "Category": "CATEGNAME",
            "Tags": "TAGNAMES",
            "Notes": "NOTES",
            "Amount": "TRANSAMOUNT"
        }

        if display_headers:
            display_columns = [
                header_to_column.get(h, h)
                for h in display_headers
                if header_to_column.get(h, h) in df.columns
            ]
        else:
            display_columns = df.columns

        # PERFORMANCE OPTIMIZATION: Prepare all widgets in memory first, then add to grid in bulk
        # This avoids triggering expensive UI layout calculations for each widget individually
        all_widgets = []

        for row_index, row in df.iterrows():
            for col in display_columns:
                value = row[col]
                # Format value based on column type
                text = _format_cell_value(col, value)

                if row_click_callback:
                    # Create clickable button for better touch handling
                    cell_widget = Button(
                        text=text,
                        size_hint_y=None,
                        height=ui_config.responsive.row_height,
                        size_hint_x=1/len(display_columns),
                        halign='left',
                        valign='middle',
                        background_color=ui_config.colors.background,
                        color=ui_config.colors.text
                    )
                    cell_widget.text_size = (None, None)
                    cell_widget.bind(size=cell_widget.setter('text_size'))

                    # Bind click event with row data using a factory function to avoid closure issues
                    def make_on_row_click(row_data):
                        def on_row_click(instance):
                            row_click_callback(row_data)
                        return on_row_click

                    cell_widget.bind(on_press=make_on_row_click(row.to_dict()))
                else:
                    # Create regular label
                    cell_widget = _create_data_label(text, len(display_columns))

                all_widgets.append(cell_widget)

        # Add all widgets to the grid in a single bulk operation
        # This is dramatically more efficient than adding them one-by-one
        for widget in all_widgets:
            grid.add_widget(widget)

    except Exception as e:
        logger.error(f"Error adding grid data rows: {e}")


def populate_grid_with_dataframe(grid, df, headers=None, sort_callback=None, row_click_callback=None):
    """Populate a grid layout with data from a DataFrame with responsive design.

    Args:
        grid: The GridLayout to populate
        df: The DataFrame containing the data
        headers: Optional list of column headers
        sort_callback: Optional callback function for sorting
        row_click_callback: Optional callback function for row clicks
    """
    try:
        # Early return for empty data
        if df is None or df.empty:
            grid.clear_widgets()
            no_data_label = Label(
                text="No data available",
                size_hint_y=None,
                height=ui_config.responsive.row_height,
                color=ui_config.colors.text
            )
            grid.add_widget(no_data_label)
            return

        # Get UI configuration
        ui_config = UIConfig()

        # Determine if we're on mobile based on screen width
        screen_width = Window.width
        is_mobile = screen_width < ui_config.responsive.mobile_breakpoint

        # Define mobile-friendly column subsets
        if is_mobile and headers:
            # Show only essential columns on mobile
            mobile_headers = ["Date", "Payee", "Amount", "Category"]
            display_headers = [h for h in mobile_headers if h in headers]
            grid.cols = len(display_headers) if display_headers else 4
        else:
            display_headers = headers if headers else list(df.columns)
            if headers:
                grid.cols = len(headers)
            else:
                grid.cols = len(df.columns) if not df.empty else 1

        # Clear existing widgets only once
        grid.clear_widgets()

        # Add headers if provided
        if display_headers:
            _add_grid_headers(grid, display_headers, sort_callback, ui_config)

        # Add data rows with responsive column filtering
        _add_grid_data_rows(grid, df, display_headers, row_click_callback, ui_config)

    except Exception as e:
        logger.error(f"Error populating grid with dataframe: {e}")
        # Add error message to grid
        error_label = Label(
            text="Error loading data",
            size_hint_y=None,
            height=40,
            color=(1, 0, 0, 1)  # Red color for error
        )
        grid.clear_widgets()
        grid.add_widget(error_label)


# Re-export functions to maintain backward compatibility with old module structure
create_popup = base_create_popup
show_popup = base_show_popup


# Import SortableHeaderButton since it's referenced in _add_grid_headers
try:
    from .transaction_components import SortableHeaderButton
except ImportError:
    # If import fails, define a minimal version for backward compatibility
    class SortableHeaderButton(Button):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Minimal implementation for backward compatibility
            pass