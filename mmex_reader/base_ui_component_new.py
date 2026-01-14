"""Base UI Component for the MMEX Kivy application.

This module provides the base class for all UI components with common functionality.
"""

# Standard library imports
import logging
from typing import Any, Callable, Optional

# Third-party imports
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

# Local imports
try:
    from error_handling import handle_database_operation, is_valid_date_format
except ImportError:
    # Fallback if error_handling module is not available
    def handle_database_operation(func, *args, **kwargs):
        return None, func(*args, **kwargs)

from ui_config_new import ui_config, show_popup

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# BASE CLASSES
# =============================================================================

class BaseUIComponent(BoxLayout):
    """Base class for all UI components with common functionality."""

    def __init__(self, **kwargs):
        super(BaseUIComponent, self).__init__(**kwargs)
        self.ui_config = ui_config
        self._setup_base_properties()

    def _setup_base_properties(self):
        """Setup base properties for the component."""
        self.padding = self.ui_config.responsive.padding
        self.spacing = self.ui_config.responsive.spacing

    def create_label(self, text: str, **kwargs) -> Label:
        """Create a standardized label with consistent styling.

        Args:
            text: Label text
            **kwargs: Additional label properties

        Returns:
            Label: Configured label widget
        """
        default_props = {
            'text': text,
            'size_hint_y': None,
            'height': self.ui_config.responsive.button_height,
            'halign': 'left',
            'valign': 'middle'
        }
        default_props.update(kwargs)

        label = Label(**default_props)
        label.bind(size=label.setter('text_size'))
        return label

    def create_button(self, text: str, callback: Optional[Callable] = None, **kwargs) -> Button:
        """Create a standardized button with consistent styling.

        Args:
            text: Button text
            callback: Button click callback
            **kwargs: Additional button properties

        Returns:
            Button: Configured button widget
        """
        default_props = {
            'text': text,
            'size_hint_y': None,
            'height': self.ui_config.responsive.button_height,
            'background_color': self.ui_config.colors.button
        }
        default_props.update(kwargs)

        button = Button(**default_props)
        if callback:
            button.bind(on_release=callback)
        return button

    def create_text_input(self, text: str = '', **kwargs) -> TextInput:
        """Create a standardized text input with consistent styling.

        Args:
            text: Initial text value
            **kwargs: Additional text input properties

        Returns:
            TextInput: Configured text input widget
        """
        default_props = {
            'text': text,
            'size_hint_y': None,
            'height': self.ui_config.responsive.input_height,
            'multiline': False
        }
        default_props.update(kwargs)

        return TextInput(**default_props)

    def show_error(self, message: str, title: str = "Error"):
        """Show an error popup with consistent styling.

        Args:
            message: Error message to display
            title: Popup title
        """
        show_popup(title, message, popup_type='error')

    def show_success(self, message: str, title: str = "Success"):
        """Show a success popup with consistent styling.

        Args:
            message: Success message to display
            title: Popup title
        """
        show_popup(title, message, popup_type='success')