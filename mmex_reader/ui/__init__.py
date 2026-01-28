"""UI Package for MMEX Kivy Application.

This package provides UI components and utilities for the MMEX Kivy application.
"""

# Configuration classes
from ui.config import (
    ScreenSize,
    UIColors,
    ResponsiveConfig,
    UIConfig,
    ui_config
)

# Base component
from ui.base import BaseUIComponent

# Widgets
from ui.widgets import (
    DatePickerWidget,
    DatePickerButton
)

# Account components
from ui.account import AccountTabContent

# Transaction components
from ui.transaction import (
    SortableHeaderButton,
    populate_grid_with_dataframe,
    TransactionDetailsPopup
)

# Constants and utilities
from ui.config import (
    BG_COLOR,
    HEADER_COLOR,
    BUTTON_COLOR,
    HIGHLIGHT_COLOR,
    show_popup,
    create_popup
)

__all__ = [
    # Configuration
    'ScreenSize',
    'UIColors',
    'ResponsiveConfig',
    'UIConfig',
    'ui_config',
    
    # Base component
    'BaseUIComponent',
    
    # Widgets
    'DatePickerWidget',
    'DatePickerButton',
    
    # Account components
    'AccountTabContent',
    
    # Transaction components
    'SortableHeaderButton',
    'populate_grid_with_dataframe',
    'TransactionDetailsPopup',
    
    # Constants and utilities
    'BG_COLOR',
    'HEADER_COLOR',
    'BUTTON_COLOR',
    'HIGHLIGHT_COLOR',
    'show_popup',
    'create_popup'
]