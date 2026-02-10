"""UI configuration and constants for the MMEX Kivy application."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List, Optional, Callable
from kivy.core.window import Window

logger = logging.getLogger(__name__)

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
    
    # Header heights
    header_height: int = 50
    header_height_mobile: int = 80
    
    # Specific padding/spacing for different sizes
    padding_mobile: int = 5
    spacing_mobile: int = 3
    padding_tablet: int = 8
    spacing_tablet: int = 5
    padding_desktop: int = 10
    spacing_desktop: int = 10
    
    @classmethod
    def get_config(cls, screen_width: float) -> 'ResponsiveConfig':
        """Get responsive configuration based on screen width."""
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
            
    def get_screen_size(self) -> ScreenSize:
        return self.screen_size

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
        """Register a callback to be notified when responsive config changes."""
        if callback not in self._resize_callbacks:
            self._resize_callbacks.append(callback)
    
    def unregister_resize_callback(self, callback):
        """Unregister a previously registered callback."""
        if callback in self._resize_callbacks:
            self._resize_callbacks.remove(callback)
    
    @property
    def is_mobile(self) -> bool:
        return self.responsive.screen_size == ScreenSize.MOBILE
    
    @property
    def is_tablet(self) -> bool:
        return self.responsive.screen_size == ScreenSize.TABLET
    
    @property
    def is_desktop(self) -> bool:
        return self.responsive.screen_size == ScreenSize.DESKTOP

# Global UI configuration instance
ui_config = UIConfig()

# Legacy constants
BG_COLOR = ui_config.colors.background
HEADER_COLOR = ui_config.colors.header
BUTTON_COLOR = ui_config.colors.button
HIGHLIGHT_COLOR = ui_config.colors.highlight
