"""UI components for the MMEX Kivy application.

This module provides reusable UI component classes for the MMEX Kivy application.
(Step 3: Final refactoring step - all components imported from ui package)
"""

# Standard library imports
import logging

# Local imports - Re-export from ui package
from ui.config import (
    ScreenSize,
    UIColors,
    ResponsiveConfig,
    UIConfig,
    ui_config,
    BG_COLOR,
    HEADER_COLOR,
    BUTTON_COLOR,
    HIGHLIGHT_COLOR
)

from ui.base import BaseUIComponent

from ui.widgets import (
    create_popup,
    show_popup,
    DatePickerWidget,
    DatePickerButton,
    create_styled_label,
    # Backward compatibility
    create_header_label,
    _create_data_label
)

from ui.transaction import SortableHeaderButton

from ui.account import AccountTabContent

logger = logging.getLogger(__name__)

# Verify exports
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
    'create_popup',
    'show_popup',
    'DatePickerWidget',
    'DatePickerButton',
    'create_styled_label',
    'create_header_label',
    '_create_data_label',
    'SortableHeaderButton',
    'AccountTabContent'
]
