"""UI components for the MMEX Kivy application.

This module provides reusable UI component classes for the MMEX Kivy application.
(Step 2: Refactored to use ui.widgets and ui.transaction)
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# Refactor Step 1: Import Config and Base classes
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

# Refactor Step 2: Import Widgets and Transaction components
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

logger = logging.getLogger(__name__)

# =============================================================================
# UI COMPONENTS
# =============================================================================

class AccountTabContent(BaseUIComponent):
    """Content for an account-specific tab with responsive design."""
    
    def __init__(self, account_id, account_name, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.account_id = account_id
        self.account_name = account_name
        
        try:
            # Set responsive properties based on screen size
            screen_size = self.ui_config.responsive.get_screen_size()
            
            if screen_size == ScreenSize.MOBILE:
                self.padding = self.ui_config.responsive.padding_mobile
                self.spacing = self.ui_config.responsive.spacing_mobile
                self.is_mobile = True
            elif screen_size == ScreenSize.TABLET:
                self.padding = self.ui_config.responsive.padding_tablet
                self.spacing = self.ui_config.responsive.spacing_tablet
                self.is_mobile = False
            else:  # Desktop
                self.padding = self.ui_config.responsive.padding_desktop
                self.spacing = self.ui_config.responsive.spacing_desktop
                self.is_mobile = False
            
            self._create_header()
            
        except Exception as e:
            logger.error(f"Error initializing AccountTabContent: {e}")
            self.show_error("Error initializing account tab")
    
    def _create_header(self):
        """Create the account header with responsive layout."""
        try:
            # Account info header with responsive layout
            if self.is_mobile:
                # Stack account info vertically on mobile
                self.header = BoxLayout(
                    orientation='vertical', 
                    size_hint=(1, None), 
                    height=self.ui_config.responsive.header_height_mobile,
                    spacing=self.spacing
                )
                
                # Account name label
                self.account_label = self.create_label(
                    text=f"Account: {self.account_name}",
                    size_hint=(1, 0.5),
                    halign='center'
                )
                self.header.add_widget(self.account_label)
                
                # Balance label
                self.balance_label = self.create_label(
                    text="Balance: Loading...",
                    size_hint=(1, 0.5),
                    halign='center'
                )
                self.header.add_widget(self.balance_label)
            else:
                # Horizontal layout for larger screens
                self.header = BoxLayout(
                    orientation='horizontal', 
                    size_hint=(1, None), 
                    height=self.ui_config.responsive.header_height,
                    spacing=self.spacing
                )
                
                # Account name label
                self.account_label = self.create_label(
                    text=f"Account: {self.account_name}",
                    size_hint=(0.7, 1),
                    halign='left'
                )
                self.header.add_widget(self.account_label)
                
                # Balance label
                self.balance_label = self.create_label(
                    text="Balance: Loading...",
                    size_hint=(0.3, 1),
                    halign='right'
                )
                self.header.add_widget(self.balance_label)
            
            self.add_widget(self.header)
            
        except Exception as e:
            logger.error(f"Error creating account header: {e}")
            self.show_error("Error creating account header")
            # Recreate balance label with proper settings
            self.balance_label = self.create_label(
                text="Balance: Loading...",
                size_hint=(0.3, 1),
                halign='right',
                valign='middle',
                text_size=(None, None)
            )
            self.header.add_widget(self.account_label)
            self.header.add_widget(self.balance_label)
        
        self.add_widget(self.header)
        
        # Results label
        self.results_label = Label(
            text=f"Transactions for {account_name}",
            size_hint=(1, None),
            height=30,
            halign='left' if not self.is_mobile else 'center',
            valign='middle'
        )
        self.add_widget(self.results_label)
        
        # Transactions grid in a scroll view
        self.scroll_view = ScrollView(size_hint=(1, 1))  # Take all remaining space
        
        # Grid for transactions with responsive columns
        if self.is_mobile:
            # Fewer columns on mobile for better readability
            self.results_grid = GridLayout(cols=4, spacing=1, size_hint_y=None)
        else:
            # Full columns on larger screens
            self.results_grid = GridLayout(cols=6, spacing=2, size_hint_y=None)
        
        # The height will be set based on the children
        self.results_grid.bind(minimum_height=self.results_grid.setter('height'))
        
        # Add grid to scroll view
        self.scroll_view.add_widget(self.results_grid)
        
        # Add scroll view to main layout
        self.add_widget(self.scroll_view)
        
        # Bind size to update text_size
        self.bind(size=self.update_text_size)
    
    def update_text_size(self, instance, value):
        """Update text_size when the widget size changes."""
        self.account_label.text_size = (self.account_label.width, None)
        self.balance_label.text_size = (self.balance_label.width, None)
    
    def update_balance(self, balance):
        """Update the displayed balance."""
        self.balance_label.text = f"Balance: ${balance:.2f}"
