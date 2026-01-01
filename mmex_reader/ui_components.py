"""UI components facade for the MMEX Kivy application.

This module provides backwards compatibility by importing all components from 
the new modular structure.
"""

# Import all components from the modular structure

# Base components
from base_components import (
    ScreenSize,
    UIColors,
    ResponsiveConfig,
    UIConfig,
    BaseUIComponent,
    create_popup,
    show_popup,
    ui_config,
    BG_COLOR,
    HEADER_COLOR,
    BUTTON_COLOR,
    HIGHLIGHT_COLOR
)

# Date components
from date_components import (
    DatePickerWidget,
    DatePickerButton
)

# Transaction components
from transaction_components import (
    SortableHeaderButton,
    AccountTabContent,
    TransactionDetailsPopup
)

# Utility functions
from ui_utils import (
    create_styled_label,
    create_header_label,
    _create_data_label,
    populate_grid_with_dataframe,
    _add_grid_headers,
    _add_grid_data_rows,
    _format_cell_value
)

# Re-export everything to maintain full backward compatibility
__all__ = [
    'ScreenSize',
    'UIColors', 
    'ResponsiveConfig',
    'UIConfig',
    'BaseUIComponent',
    'create_popup',
    'show_popup',
    'ui_config',
    'BG_COLOR',
    'HEADER_COLOR',
    'BUTTON_COLOR',
    'HIGHLIGHT_COLOR',
    'DatePickerWidget',
    'DatePickerButton',
    'SortableHeaderButton',
    'AccountTabContent',
    'TransactionDetailsPopup', 
    'create_styled_label',
    'create_header_label',
    '_create_data_label',
    'populate_grid_with_dataframe',
    '_add_grid_headers',
    '_add_grid_data_rows',
    '_format_cell_value',
]