"""Base UI Component classes for the MMEX Kivy application.

This module provides core configuration classes and the base UI component.
"""

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
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
import pandas as pd
from datetime import datetime, timedelta

# Local imports
try:
    from error_handling import handle_database_operation, is_valid_date_format
except ImportError:
    # Fallback if error_handling module is not available
    def handle_database_operation(func, *args, **kwargs):
        return None, func(*args, **kwargs)
    
    def is_valid_date_format(date_str, date_name="date"):
        return True  # Simplified validation for fallback

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION CLASSES
# =============================================================================

class ScreenSize(Enum):
    """Screen size categories for responsive design."""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"

@dataclass
class UIColors:
    """UI color scheme configuration."""
    background: Tuple[float, float, float, float] = (0.9, 0.9, 0.9, 1.0)
    header: Tuple[float, float, float, float] = (0.2, 0.6, 0.8, 1.0)
    button: Tuple[float, float, float, float] = (0.3, 0.5, 0.7, 1.0)
    highlight: Tuple[float, float, float, float] = (0.1, 0.7, 0.1, 1.0)
    error: Tuple[float, float, float, float] = (0.7, 0.3, 0.3, 1.0)
    warning: Tuple[float, float, float, float] = (0.8, 0.6, 0.2, 1.0)
    success: Tuple[float, float, float, float] = (0.2, 0.7, 0.2, 1.0)

@dataclass
class ResponsiveConfig:
    """Responsive design configuration for different screen sizes."""
    screen_size: ScreenSize
    padding: int
    spacing: int
    font_size: int
    button_height: int
    input_height: int

    @classmethod
    def get_config(cls, screen_width: float) -> 'ResponsiveConfig':
        """Get responsive configuration based on screen width.

        Args:
            screen_width: Current screen width in pixels

        Returns:
            ResponsiveConfig: Configuration for the current screen size
        """
        if screen_width <= 600:  # Mobile
            return cls(
                screen_size=ScreenSize.MOBILE,
                padding=5,
                spacing=3,
                font_size=14,
                button_height=35,
                input_height=35
            )
        elif screen_width <= 1024:  # Tablet
            return cls(
                screen_size=ScreenSize.TABLET,
                padding=8,
                spacing=5,
                font_size=16,
                button_height=40,
                input_height=40
            )
        else:  # Desktop
            return cls(
                screen_size=ScreenSize.DESKTOP,
                padding=10,
                spacing=10,
                font_size=18,
                button_height=45,
                input_height=45
            )

class UIConfig:
    """Central configuration class for UI components."""

    def __init__(self):
        self.colors = UIColors()
        self.responsive = ResponsiveConfig.get_config(Window.width)
        self._resize_callbacks = []

        # Update responsive config when window size changes
        Window.bind(on_resize=self._on_window_resize)

    def _on_window_resize(self, instance, width, height):
        """Update responsive configuration when window is resized."""
        old_size = self.responsive.screen_size
        self.responsive = ResponsiveConfig.get_config(width)
        new_size = self.responsive.screen_size
        logger.debug(f"Window resized to {width}x{height}, updated to {new_size.value}")

        # Notify registered callbacks if screen size category changed
        if old_size != new_size:
            for callback in self._resize_callbacks:
                callback(self.responsive)

    def register_resize_callback(self, callback):
        """Register a callback to be notified when responsive config changes.

        Args:
            callback: Function to call with the new responsive config
        """
        if callback not in self._resize_callbacks:
            self._resize_callbacks.append(callback)
            logger.debug(f"Registered resize callback: {callback.__qualname__ if hasattr(callback, '__qualname__') else callback}")

    def unregister_resize_callback(self, callback):
        """Unregister a previously registered callback.

        Args:
            callback: Previously registered callback function
        """
        if callback in self._resize_callbacks:
            self._resize_callbacks.remove(callback)
            logger.debug(f"Unregistered resize callback: {callback.__qualname__ if hasattr(callback, '__qualname__') else callback}")

    @property
    def is_mobile(self) -> bool:
        """Check if current screen size is mobile."""
        return self.responsive.screen_size == ScreenSize.MOBILE

    @property
    def is_tablet(self) -> bool:
        """Check if current screen size is tablet."""
        return self.responsive.screen_size == ScreenSize.TABLET

    @property
    def is_desktop(self) -> bool:
        """Check if current screen size is desktop."""
        return self.responsive.screen_size == ScreenSize.DESKTOP

# Global UI configuration instance
ui_config = UIConfig()

# Legacy color constants for backward compatibility
BG_COLOR = ui_config.colors.background
HEADER_COLOR = ui_config.colors.header
BUTTON_COLOR = ui_config.colors.button
HIGHLIGHT_COLOR = ui_config.colors.highlight


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
        try:
            from .ui_utils import show_popup
            show_popup(title, message, popup_type='error')
        except ImportError:
            print(f"Error: {message}")

    def show_success(self, message: str, title: str = "Success"):
        """Show a success popup with consistent styling.

        Args:
            message: Success message to display
            title: Popup title
        """
        try:
            from .ui_utils import show_popup
            show_popup(title, message, popup_type='success')
        except ImportError:
            print(f"Success: {message}")


# =============================================================================
# UTILITY FUNCTIONS
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
    from .ui_utils import ui_config  # Import here to avoid circular dependency

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
    from .ui_utils import create_popup  # Import here to avoid circular dependency
    
    # Create message label
    content = Label(
        text=message,
        text_size=(None, None),
        halign='center',
        valign='middle'
    )
    # Ensure center alignment by coupling text_size to widget size
    content.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))

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