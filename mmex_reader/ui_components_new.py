"""UI components for the MMEX Kivy application.

This module provides reusable UI component classes for the MMEX Kivy application,
including date pickers, account tabs, transaction forms, and other interactive elements.

Classes:
    UIConfig: Configuration class for UI constants and responsive design
    BaseUIComponent: Base class for all UI components with common functionality
    DatePickerWidget: Custom date picker with calendar interface
    DatePickerButton: Button that opens a date picker popup
    AccountTabContent: Content for account-specific tabs with responsive design
    TransactionListWidget: Widget for displaying transaction lists
    TransactionEditDialog: Dialog for editing transaction details

Constants:
    UI_COLORS: Color scheme constants
    UI_SIZES: Size and spacing constants
    RESPONSIVE_BREAKPOINTS: Screen size breakpoints for responsive design

Functions:
    create_popup: Utility function for creating standardized popups
    show_popup: Utility function for showing simple message popups
    get_responsive_config: Get responsive configuration based on screen size
"""

# Standard library imports
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

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
from datetime import datetime, timedelta
import calendar

# Local imports
try:
    from error_handling import handle_database_operation, is_valid_date_format
except ImportError:
    # Fallback if error_handling module is not available
    def handle_database_operation(func, *args, **kwargs):
        return None, func(*args, **kwargs)

# Import from new modules to maintain backward compatibility
from ui_config_new import *
from base_ui_component_new import *
from date_components_new import *
from account_components_new import *
from transaction_components_new import *

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# UTILITY FUNCTIONS (Preserved in this module)
# =============================================================================

def create_popup(title: str, content_widget: Any, buttons: Optional[List[Dict]] = None,
                popup_type: str = 'info', **kwargs) -> Popup:
    """Create a standardized popup with consistent styling.

    Args:
        title: Popup title
        content_widget: Widget to display in popup content
        buttons: List of button configurations
        popup_type: Type of popup ('info', 'error', 'warning', 'success')
        **kwargs: Additional popup properties

    Returns:
        Popup: Configured popup widget
    """
    # Set default properties
    # Map popup type to color style (used for header separator and accents)
    type_color_map = {
        'error': ui_config.colors.error,
        'warning': ui_config.colors.warning,
        'success': ui_config.colors.success,
        'info': ui_config.colors.button
    }
    header_color = type_color_map.get(popup_type, ui_config.colors.button)

    default_props = {
        'title': title,
        'size_hint': (0.8, 0.6),
        'auto_dismiss': True,
        # Style Popup header separator to reflect popup type
        'separator_color': header_color
    }
    default_props.update(kwargs)

    # Create main layout
    main_layout = BoxLayout(orientation='vertical', spacing=ui_config.responsive.spacing)

    # Add content widget
    if content_widget:
        main_layout.add_widget(content_widget)

    # Add buttons if provided
    if buttons:
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=ui_config.responsive.button_height + 10,
            spacing=ui_config.responsive.spacing
        )

        for button_config in buttons:
            btn = Button(
                text=button_config.get('text', 'OK'),
                size_hint_x=button_config.get('size_hint_x', 1.0),
                background_color=ui_config.colors.button
            )

            if 'callback' in button_config:
                btn.bind(on_release=button_config['callback'])

            button_layout.add_widget(btn)

        main_layout.add_widget(button_layout)

    # Create popup
    popup = Popup(content=main_layout, **default_props)
    return popup

def show_popup(title: str, message: str, popup_type: str = 'info'):
    """Show a simple message popup.

    Args:
        title: Popup title
        message: Message to display
        popup_type: Type of popup ('info', 'error', 'warning', 'success')
    """
    # Create message label
    content = Label(
        text=message,
        text_size=(None, None),
        halign='center',
        valign='middle'
    )
    # Ensure center alignment by coupling text_size to widget size
    content.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))

    # Set color based on popup type
    color_map = {
        'error': ui_config.colors.error,
        'warning': ui_config.colors.warning,
        'success': ui_config.colors.success,
        'info': ui_config.colors.button
    }
    # Apply message color based on type for quick visual cue
    content.color = (0, 0, 0, 1)  # default text color
    try:
        # Use a subtle tint via canvas background when possible
        tint = color_map.get(popup_type, ui_config.colors.button)
        with content.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*tint)
            rect = Rectangle(pos=content.pos, size=content.size)
            content.bind(pos=lambda inst, val: setattr(rect, 'pos', inst.pos))
            content.bind(size=lambda inst, val: setattr(rect, 'size', inst.size))
    except Exception:
        # Non-critical styling failure; keep functional popup
        pass

    # Create and show popup
    popup = create_popup(
        title=title,
        content_widget=content,
        buttons=[{
            'text': 'OK',
            'callback': lambda instance: popup.dismiss()
        }],
        popup_type=popup_type
    )
    popup.open()

# Preserve legacy imports for backward compatibility
BG_COLOR = ui_config.colors.background
HEADER_COLOR = ui_config.colors.header
BUTTON_COLOR = ui_config.colors.button
HIGHLIGHT_COLOR = ui_config.colors.highlight