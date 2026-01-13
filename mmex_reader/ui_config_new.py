"""UI Configuration components for the MMEX Kivy application.

This module provides configuration classes for UI components,
including colors, responsive design settings, and UI constants.
"""

# Standard library imports
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

# Third-party imports
from kivy.core.window import Window

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