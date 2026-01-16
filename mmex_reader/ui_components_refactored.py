"""UI components for the MMEX Kivy application.

This module provides reusable UI component classes for the MMEX Kivy application,
including date pickers, account tabs, transaction forms, and other interactive elements.

DEPRECATED: This module has been split into smaller, more focused modules:
- ui_config_new.py: Configuration classes and constants
- base_ui_component_new.py: Base UI component class
- date_components_new.py: Date-related components
- account_components_new.py: Account-related components
- transaction_components_new.py: Transaction-related components

For new code, import directly from the specific modules above.
This module is maintained for backward compatibility.
"""

# Import all components from new modules to maintain backward compatibility
from ui_config_new import (
    ScreenSize,
    UIColors,
    ResponsiveConfig,
    UIConfig,
    ui_config,
    BG_COLOR,
    HEADER_COLOR,
    BUTTON_COLOR,
    HIGHLIGHT_COLOR,
    show_popup,
    create_popup
)

from base_ui_component_new import BaseUIComponent

from date_components_new import (
    DatePickerWidget,
    DatePickerButton
)

from account_components_new import AccountTabContent

from transaction_components_new import (
    SortableHeaderButton,
    populate_grid_with_dataframe,
    TransactionDetailsPopup
)

# Define __all__ to specify what gets imported with "from ui_components import *"
__all__ = [
    'ScreenSize',
    'UIColors', 
    'ResponsiveConfig',
    'UIConfig',
    'ui_config',
    'BG_COLOR',
    'HEADER_COLOR', 
    'BUTTON_COLOR',
    'HIGHLIGHT_COLOR',
    'BaseUIComponent',
    'DatePickerWidget',
    'DatePickerButton',
    'AccountTabContent',
    'SortableHeaderButton',
    'populate_grid_with_dataframe',
    'TransactionDetailsPopup',
    'show_popup',
    'create_popup'
]