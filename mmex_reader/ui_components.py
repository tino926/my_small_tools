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
    from error_handling import handle_database_operation
except ImportError:
    # Fallback if error_handling module is not available
    def handle_database_operation(func, *args, **kwargs):
        return None, func(*args, **kwargs)

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
        
        # Update responsive config when window size changes
        Window.bind(on_resize=self._on_window_resize)
    
    def _on_window_resize(self, instance, width, height):
        """Update responsive configuration when window is resized."""
        self.responsive = ResponsiveConfig.get_config(width)
        logger.debug(f"Window resized to {width}x{height}, updated to {self.responsive.screen_size.value}")
    
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
        show_popup(title, message, popup_type='error')
    
    def show_success(self, message: str, title: str = "Success"):
        """Show a success popup with consistent styling.
        
        Args:
            message: Success message to display
            title: Popup title
        """
        show_popup(title, message, popup_type='success')

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
    # Set default properties
    default_props = {
        'title': title,
        'size_hint': (0.8, 0.6),
        'auto_dismiss': True
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
    
    # Set color based on popup type
    color_map = {
        'error': ui_config.colors.error,
        'warning': ui_config.colors.warning,
        'success': ui_config.colors.success,
        'info': ui_config.colors.button
    }
    
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

# =============================================================================
# UI COMPONENTS
# =============================================================================


class DatePickerWidget(BaseUIComponent):
    """A custom date picker widget with calendar interface."""
    
    def __init__(self, initial_date=None, callback=None, **kwargs):
        super(DatePickerWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (300, 350)
        self.callback = callback
        
        # Set initial date
        if initial_date:
            if isinstance(initial_date, str):
                try:
                    self.current_date = datetime.strptime(initial_date, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid date format: {initial_date}, using current date")
                    self.current_date = datetime.now()
            else:
                self.current_date = initial_date
        else:
            self.current_date = datetime.now()
            
        self.selected_date = self.current_date
        
        # Create the date picker interface
        self._create_header()
        self._create_calendar()
        self._create_footer()
        
    def _create_header(self):
        """Create the header with month/year navigation."""
        header_layout = BoxLayout(
            orientation='horizontal', 
            size_hint=(1, None), 
            height=self.ui_config.responsive.button_height
        )
        
        # Previous month button
        prev_btn = self.create_button(
            '<', 
            callback=self._prev_month,
            size_hint=(None, 1), 
            width=40
        )
        header_layout.add_widget(prev_btn)
        
        # Month/Year label
        self.month_year_label = self.create_label(
            self.current_date.strftime("%B %Y"),
            size_hint=(1, 1),
            halign='center'
        )
        header_layout.add_widget(self.month_year_label)
        
        # Next month button
        next_btn = self.create_button(
            '>', 
            callback=self._next_month,
            size_hint=(None, 1), 
            width=40
        )
        header_layout.add_widget(next_btn)
        
        self.add_widget(header_layout)
        
    def _create_calendar(self):
        """Create the calendar grid."""
        # Day headers
        day_headers = BoxLayout(
            orientation='horizontal', 
            size_hint=(1, None), 
            height=30
        )
        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            label = self.create_label(day, size_hint=(1, 1), bold=True)
            day_headers.add_widget(label)
        self.add_widget(day_headers)
        
        # Calendar grid
        self.calendar_grid = GridLayout(
            cols=7, 
            size_hint=(1, 1), 
            spacing=2
        )
        self._populate_calendar()
        self.add_widget(self.calendar_grid)
        
    def _create_footer(self):
        """Create the footer with action buttons."""
        footer_layout = BoxLayout(
            orientation='horizontal', 
            size_hint=(1, None), 
            height=self.ui_config.responsive.button_height, 
            spacing=self.ui_config.responsive.spacing
        )
        
        # Today button
        today_btn = self.create_button(
            'Today', 
            callback=self._select_today,
            size_hint=(0.5, 1), 
            background_color=self.ui_config.colors.highlight
        )
        footer_layout.add_widget(today_btn)
        
        # Cancel button
        cancel_btn = self.create_button(
            'Cancel', 
            callback=self._cancel,
            size_hint=(0.5, 1), 
            background_color=self.ui_config.colors.error
        )
        footer_layout.add_widget(cancel_btn)
        
        self.add_widget(footer_layout)
        
    def _populate_calendar(self):
        """Populate the calendar grid with day buttons."""
        self.calendar_grid.clear_widgets()
        
        try:
            # Get calendar data
            cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
            
            for week in cal:
                for day in week:
                    if day == 0:
                        # Empty cell for days from other months
                        self.calendar_grid.add_widget(Label(text=''))
                    else:
                        # Day button
                        day_btn = Button(
                            text=str(day),
                            size_hint=(1, 1),
                            background_color=self.ui_config.colors.background
                        )
                        
                        # Highlight selected date
                        if (day == self.selected_date.day and 
                            self.current_date.month == self.selected_date.month and
                            self.current_date.year == self.selected_date.year):
                            day_btn.background_color = self.ui_config.colors.highlight
                        
                        # Highlight today
                        today = datetime.now()
                        if (day == today.day and 
                            self.current_date.month == today.month and
                            self.current_date.year == today.year):
                            day_btn.background_color = self.ui_config.colors.header
                        
                        day_btn.bind(on_release=lambda btn, d=day: self._select_date(d))
                        self.calendar_grid.add_widget(day_btn)
        except Exception as e:
            logger.error(f"Error populating calendar: {e}")
            self.show_error(f"Error creating calendar: {e}")
                    
    def _prev_month(self, instance):
        """Navigate to previous month."""
        try:
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month - 1)
            self._update_display()
        except Exception as e:
            logger.error(f"Error navigating to previous month: {e}")
            self.show_error("Error navigating calendar")
        
    def _next_month(self, instance):
        """Navigate to next month."""
        try:
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1)
            self._update_display()
        except Exception as e:
            logger.error(f"Error navigating to next month: {e}")
            self.show_error("Error navigating calendar")
        
    def _update_display(self):
        """Update the calendar display."""
        try:
            self.month_year_label.text = self.current_date.strftime("%B %Y")
            self._populate_calendar()
        except Exception as e:
            logger.error(f"Error updating calendar display: {e}")
            self.show_error("Error updating calendar")
        
    def _select_date(self, day):
        """Select a specific date."""
        try:
            self.selected_date = self.current_date.replace(day=day)
            self._populate_calendar()
            if self.callback:
                self.callback(self.selected_date.strftime("%Y-%m-%d"))
        except Exception as e:
            logger.error(f"Error selecting date: {e}")
            self.show_error("Error selecting date")
            
    def _select_today(self, instance):
        """Select today's date."""
        try:
            today = datetime.now()
            self.current_date = today
            self.selected_date = today
            self._update_display()
            if self.callback:
                self.callback(self.selected_date.strftime("%Y-%m-%d"))
        except Exception as e:
            logger.error(f"Error selecting today: {e}")
            self.show_error("Error selecting today's date")
            
    def _cancel(self, instance):
        """Cancel date selection."""
        if self.callback:
            self.callback(None)
            
    def get_selected_date(self):
        """Get the currently selected date as a string."""
        return self.selected_date.strftime("%Y-%m-%d")


class DatePickerButton(BaseUIComponent):
    """A button that opens a date picker when clicked."""
    
    def __init__(self, initial_date=None, date_change_callback=None, **kwargs):
        """
        Initialize DatePickerButton.
        
        Args:
            initial_date: Initial date to display (YYYY-MM-DD format)
            date_change_callback: Function to call when date changes
            **kwargs: Additional keyword arguments
        """
        super().__init__(**kwargs)
        self.date_change_callback = date_change_callback
        
        # Set initial date with validation
        try:
            if initial_date:
                # Validate date format
                datetime.strptime(initial_date, "%Y-%m-%d")
                self.current_date = initial_date
            else:
                self.current_date = datetime.now().strftime("%Y-%m-%d")
        except ValueError as e:
            logger.warning(f"Invalid initial date format: {initial_date}, using today's date")
            self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create button with responsive styling
        self.button = self.create_button(
            text=self.current_date,
            on_release=self._open_date_picker
        )
        self.add_widget(self.button)
        
    def _open_date_picker(self, instance):
        """Open the date picker popup."""
        try:
            # Create date picker widget
            date_picker = DatePickerWidget(
                initial_date=self.current_date,
                callback=self._on_date_selected
            )
            
            # Create and show popup
            self.popup = create_popup(
                title='Select Date',
                content=date_picker,
                size_hint=(0.8, 0.8)
            )
            show_popup(self.popup)
            
        except Exception as e:
            logger.error(f"Error opening date picker: {e}")
            self.show_error("Error opening date picker")
        
    def _on_date_selected(self, selected_date):
        """Handle date selection from picker."""
        try:
            if selected_date:
                self.current_date = selected_date
                self.button.text = selected_date
                if self.date_change_callback:
                    self.date_change_callback(self, selected_date)
            if hasattr(self, 'popup'):
                self.popup.dismiss()
        except Exception as e:
            logger.error(f"Error handling date selection: {e}")
            self.show_error("Error selecting date")
        
    def get_date(self):
        """Get the current date value."""
        return self.current_date
        
    def set_date(self, date_str):
        """Set the date value with validation."""
        try:
            if date_str:
                # Validate date format
                datetime.strptime(date_str, "%Y-%m-%d")
                self.current_date = date_str
                self.button.text = date_str
        except ValueError as e:
            logger.error(f"Invalid date format: {date_str}")
            self.show_error("Invalid date format")
        except Exception as e:
            logger.error(f"Error setting date: {e}")
            self.show_error("Error setting date")

class AccountTabContent(BaseUIComponent):
    """Content for an account-specific tab with responsive design."""
    
    def __init__(self, account_id, account_name, **kwargs):
        """
        Initialize AccountTabContent.
        
        Args:
            account_id: ID of the account
            account_name: Name of the account
            **kwargs: Additional keyword arguments
        """
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
                text="Balance: Loading...",
                size_hint=(0.3, 1),
                halign='right',
                valign='middle',
                text_size=(None, None)
            )
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

def create_popup(title, content_widget=None, buttons=None, size_hint=(0.8, 0.4), auto_dismiss=True):
    """Create a popup with customizable content and buttons.
    
    Args:
        title: The popup title
        content_widget: Widget to display in the popup (if None, an empty BoxLayout is used)
        buttons: List of dictionaries with button configurations, each containing:
                - text: Button text
                - callback: Function to call when button is pressed
                - size_hint_x: Horizontal size hint (default: 1)
        size_hint: Size hint for the popup (default: (0.8, 0.4))
        auto_dismiss: Whether the popup can be dismissed by clicking outside (default: True)
        
    Returns:
        The created Popup instance
    """
    # Create main content layout
    main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    
    # Add content widget if provided
    if content_widget:
        main_layout.add_widget(content_widget)
    
    # Add buttons if provided
    if buttons:
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        for btn_config in buttons:
            btn = Button(
                text=btn_config['text'],
                size_hint_x=btn_config.get('size_hint_x', 1)
            )
            if 'callback' in btn_config:
                btn.bind(on_press=btn_config['callback'])
            button_layout.add_widget(btn)
            
        main_layout.add_widget(button_layout)
    
    # Create and return popup
    popup = Popup(
        title=title,
        content=main_layout,
        size_hint=size_hint,
        auto_dismiss=auto_dismiss
    )
    
    return popup

def show_popup(title, message):
    """Show a simple popup with the given title and message.
    
    Args:
        title: The popup title
        message: The message to display
    """
    # Use the more flexible create_popup function
    popup = create_popup(
        title=title,
        content_widget=Label(text=message),
        buttons=[{'text': 'OK', 'callback': lambda instance: popup.dismiss()}]
    )
    popup.open()

class SortableHeaderButton(Button):
    """A button that can be used as a sortable column header."""
    
    def __init__(self, text, column_name, sort_callback, **kwargs):
        super(SortableHeaderButton, self).__init__(**kwargs)
        self.text = text
        self.column_name = column_name
        self.sort_callback = sort_callback
        self.sort_ascending = True  # Track sort direction
        self.size_hint_y = None
        self.height = 40
        self.bold = True
        self.background_color = HEADER_COLOR
        self.color = (1, 1, 1, 1)  # White text
        
        # Bind click event
        self.bind(on_release=self.on_header_click)
    
    def on_header_click(self, instance):
        """Handle header click for sorting."""
        # Toggle sort direction
        self.sort_ascending = not self.sort_ascending
        
        # Update button text to show sort direction
        direction_symbol = " ↑" if self.sort_ascending else " ↓"
        base_text = self.text.replace(" ↑", "").replace(" ↓", "")
        self.text = base_text + direction_symbol
        
        # Call the sort callback
        self.sort_callback(self.column_name, self.sort_ascending)

def create_styled_label(text, label_type='data', num_columns=1, **kwargs):
    """Create a styled label with flexible configuration.
    
    Args:
        text: The label text
        label_type: 'header' or 'data' to determine styling
        num_columns: Number of columns for width calculation (data labels only)
        **kwargs: Additional Label properties to override defaults
        
    Returns:
        A styled Label widget
    """
    if label_type == 'header':
        defaults = {
            'text': text,
            'size_hint_y': None,
            'height': 40,
            'bold': True,
            'color': (1, 1, 1, 1)  # White text
        }
        defaults.update(kwargs)
        label = Label(**defaults)
        
        # Add background color
        with label.canvas.before:
            Color(*HEADER_COLOR)
            label.rect = Rectangle(pos=label.pos, size=label.size)
        
        # Update rectangle position and size when the label changes
        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size
        
        label.bind(pos=update_rect, size=update_rect)
        
    else:  # data label
        defaults = {
            'text': text,
            'size_hint_y': None,
            'height': 30,
            'size_hint_x': 1/num_columns,
            'text_size': (None, 30),
            'halign': 'left',
            'valign': 'middle',
            'shorten': True,
            'shorten_from': 'right'
        }
        defaults.update(kwargs)
        label = Label(**defaults)
        
        # Bind size to update text_size
        def update_text_size(instance, value):
            instance.text_size = (value, 30)
        
        label.bind(width=update_text_size)
    
    return label

# Backward compatibility functions
def create_header_label(text):
    """Create a styled header label (deprecated - use create_styled_label)."""
    return create_styled_label(text, 'header')

def _create_data_label(text, num_columns):
    """Create a data label (deprecated - use create_styled_label)."""
    return create_styled_label(text, 'data', num_columns)
    return label

def populate_grid_with_dataframe(grid, df, headers=None, sort_callback=None, row_click_callback=None):
    """Populate a grid layout with data from a DataFrame with responsive design.
    
    Args:
        grid: The GridLayout to populate
        df: The DataFrame containing the data
        headers: Optional list of column headers
        sort_callback: Optional callback function for sorting
        row_click_callback: Optional callback function for row clicks
    """
    try:
        # Clear existing widgets
        grid.clear_widgets()
        
        # Get UI configuration
        ui_config = UIConfig()
        
        # Determine if we're on mobile based on screen width
        screen_width = Window.width
        is_mobile = screen_width < ui_config.responsive.mobile_breakpoint
        
        # Define mobile-friendly column subsets
        if is_mobile and headers:
            # Show only essential columns on mobile
            mobile_headers = ["Date", "Payee", "Amount", "Category"]
            display_headers = [h for h in mobile_headers if h in headers]
            grid.cols = len(display_headers) if display_headers else 4
        else:
            display_headers = headers if headers else list(df.columns) if not df.empty else []
            if headers:
                grid.cols = len(headers)
            else:
                grid.cols = len(df.columns) if not df.empty else 1
        
        # Handle empty DataFrame
        if df is None or df.empty:
            no_data_label = Label(
                text="No data available",
                size_hint_y=None,
                height=ui_config.responsive.row_height,
                color=ui_config.colors.text
            )
            grid.add_widget(no_data_label)
            return
        
        # Add headers if provided
        if display_headers:
            _add_grid_headers(grid, display_headers, sort_callback, ui_config)
        
        # Add data rows with responsive column filtering
        _add_grid_data_rows(grid, df, display_headers, row_click_callback, ui_config)
        
    except Exception as e:
        logger.error(f"Error populating grid with dataframe: {e}")
        # Add error message to grid
        error_label = Label(
            text="Error loading data",
            size_hint_y=None,
            height=40,
            color=(1, 0, 0, 1)  # Red color for error
        )
        grid.clear_widgets()
        grid.add_widget(error_label)


def _add_grid_headers(grid, display_headers, sort_callback, ui_config):
    """Add headers to the grid."""
    try:
        # Map headers to actual column names
        column_mapping = {
            "Date": "TRANSDATE",
            "Account": "ACCOUNTNAME", 
            "Payee": "PAYEENAME",
            "Category": "CATEGNAME",
            "Tags": "TAGNAMES",
            "Notes": "NOTES",
            "Amount": "TRANSAMOUNT"
        }
        
        for header in display_headers:
            if sort_callback and header in column_mapping:
                # Create sortable header button
                header_btn = SortableHeaderButton(
                    text=header,
                    column_name=column_mapping[header],
                    sort_callback=sort_callback,
                    size_hint_x=1/len(display_headers)
                )
                grid.add_widget(header_btn)
            else:
                # Create regular header label
                header_label = create_header_label(header)
                header_label.size_hint_x = 1/len(display_headers)
                grid.add_widget(header_label)
                
    except Exception as e:
        logger.error(f"Error adding grid headers: {e}")


def _add_grid_data_rows(grid, df, display_headers, row_click_callback, ui_config):
    """Add data rows to the grid."""
    try:
        # Map display headers to DataFrame columns
        header_to_column = {
            "Date": "TRANSDATE",
            "Account": "ACCOUNTNAME", 
            "Payee": "PAYEENAME",
            "Category": "CATEGNAME",
            "Tags": "TAGNAMES",
            "Notes": "NOTES",
            "Amount": "TRANSAMOUNT"
        }
        
        if display_headers:
            display_columns = [
                header_to_column.get(h, h) 
                for h in display_headers 
                if header_to_column.get(h, h) in df.columns
            ]
        else:
            display_columns = df.columns
        
        for row_index, row in df.iterrows():
            for col in display_columns:
                value = row[col]
                # Format value based on column type
                text = _format_cell_value(col, value)
                
                if row_click_callback:
                    # Create clickable button for better touch handling
                    cell_widget = Button(
                        text=text,
                        size_hint_y=None,
                        height=ui_config.responsive.row_height,
                        size_hint_x=1/len(display_columns),
                        halign='left',
                        valign='middle',
                        background_color=ui_config.colors.background,
                        color=ui_config.colors.text
                    )
                    cell_widget.text_size = (None, None)
                    cell_widget.bind(size=cell_widget.setter('text_size'))
                    
                    # Bind click event with row data
                    def on_row_click(instance, row_data=row.to_dict()):
                        row_click_callback(row_data)
                    
                    cell_widget.bind(on_press=on_row_click)
                else:
                    # Create regular label
                    cell_widget = _create_data_label(text, len(display_columns))
                
                grid.add_widget(cell_widget)
                
    except Exception as e:
        logger.error(f"Error adding grid data rows: {e}")


def _format_cell_value(column_name, value):
    """Format cell value based on column type."""
    try:
        if column_name in ('TRANSAMOUNT', 'TOTRANSAMOUNT'):
            return f"${value:.2f}" if pd.notna(value) else ""
        elif column_name == 'TRANSDATE':
            return str(value).split()[0] if pd.notna(value) else ""
        else:
            return str(value) if pd.notna(value) else ""
    except Exception as e:
        logger.error(f"Error formatting cell value: {e}")
        return str(value) if value is not None else ""


# =============================================================================
# TRANSACTION DETAILS POPUP
# =============================================================================


class TransactionDetailsPopup(BaseUIComponent):
    """A popup component for displaying and editing transaction details."""
    
    def __init__(self, transaction_data, on_save_callback=None, on_delete_callback=None, **kwargs):
        """
        Initialize the transaction details popup.
        
        Args:
            transaction_data: Dictionary containing transaction information
            on_save_callback: Callback function when transaction is saved
            on_delete_callback: Callback function when transaction is deleted
            **kwargs: Additional keyword arguments
        """
        super().__init__(**kwargs)
        self.transaction_data = transaction_data.copy() if transaction_data else {}
        self.on_save_callback = on_save_callback
        self.on_delete_callback = on_delete_callback
        self.popup = None
        self.input_fields = {}
        
        # Field configurations with validation rules
        self.field_configs = [
            ('Transaction ID', 'TRANSID', False, 'text', None, None),
            ('Date', 'TRANSDATE', True, 'text', self._validate_date, True),
            ('Account', 'ACCOUNTNAME', False, 'text', None, None),
            ('Payee', 'PAYEENAME', True, 'text', None, False),
            ('Category', 'CATEGNAME', True, 'text', None, False),
            ('Amount', 'TRANSAMOUNT', True, 'text', self._validate_amount, True),
            ('Transaction Code', 'TRANSCODE', True, 'dropdown', None, False, ['Withdrawal', 'Deposit', 'Transfer']),
            ('Notes', 'NOTES', True, 'multiline', None, False),
            ('Tags', 'TAGNAMES', True, 'text', None, False),
            ('Status', 'STATUS', True, 'dropdown', None, False, ['None', 'Reconciled', 'Void', 'Follow up', 'Duplicate']),
            ('Follow Up', 'FOLLOWUPID', True, 'text', None, False)
        ]
        
    def show(self):
        """Display the transaction details popup."""
        try:
            content = self._create_content()
            
            self.popup = create_popup(
                title=f"Transaction Details - {self.transaction_data.get('TRANSDATE', 'Unknown Date')}",
                content=content,
                size_hint=(0.9, 0.9),
                auto_dismiss=False
            )
            show_popup(self.popup)
            
        except Exception as e:
            logger.error(f"Error showing transaction details popup: {e}")
            self.show_error("Error displaying transaction details")
        
    def _create_content(self):
        """Create the main content layout for the popup."""
        try:
            main_layout = BoxLayout(
                orientation='vertical', 
                padding=self.ui_config.responsive.padding_desktop, 
                spacing=self.ui_config.responsive.spacing_desktop
            )
            
            # Create scroll view for form fields
            scroll = ScrollView()
            form_layout = GridLayout(
                cols=2, 
                spacing=self.ui_config.responsive.spacing_desktop, 
                size_hint_y=None, 
                padding=self.ui_config.responsive.padding_desktop
            )
            form_layout.bind(minimum_height=form_layout.setter('height'))
            
            # Create form fields
            self._create_form_fields(form_layout)
            
            scroll.add_widget(form_layout)
            main_layout.add_widget(scroll)
            
            # Add button layout
            button_layout = self._create_button_layout()
            main_layout.add_widget(button_layout)
            
            return main_layout
            
        except Exception as e:
            logger.error(f"Error creating popup content: {e}")
            return self.create_label("Error creating content")
    
    def _create_form_fields(self, form_layout):
        """Create form fields based on configuration."""
        try:
            for field_config in self.field_configs:
                label_text, field_key, editable = field_config[0:3]
                field_type = field_config[3]
                validator = field_config[4] if len(field_config) > 4 else None
                required = field_config[5] if len(field_config) > 5 else False
                
                # Add label with required indicator
                label_text_display = f"{label_text}{'*' if required else ''}:"
                label = self.create_label(
                    text=label_text_display,
                    size_hint_y=None,
                    height=self.ui_config.responsive.input_height,
                    halign='right'
                )
                form_layout.add_widget(label)
                
                # Get field value
                value = str(self.transaction_data.get(field_key, '')) if self.transaction_data.get(field_key) is not None else ''
                
                # Create appropriate input widget
                widget = self._create_input_widget(field_config, value, editable)
                self.input_fields[field_key] = widget
                form_layout.add_widget(widget)
                
        except Exception as e:
            logger.error(f"Error creating form fields: {e}")
            form_layout.add_widget(self.create_label("Error creating form fields"))
    
    def _create_input_widget(self, field_config, value, editable):
        """Create appropriate input widget based on field type."""
        try:
            field_type = field_config[3]
            
            if field_type == 'multiline':
                return TextInput(
                    text=value,
                    multiline=True,
                    size_hint_y=None,
                    height=self.ui_config.responsive.input_height * 2,
                    readonly=not editable,
                    background_color=self.ui_config.colors.background
                )
            elif field_type == 'dropdown':
                values = field_config[6] if len(field_config) > 6 else []
                return Spinner(
                    text=value if value else (values[0] if values else ''),
                    values=values,
                    size_hint_y=None,
                    height=self.ui_config.responsive.input_height,
                    disabled=not editable,
                    background_color=self.ui_config.colors.background
                )
            else:  # Default to text input
                return TextInput(
                    text=value,
                    multiline=False,
                    size_hint_y=None,
                    height=self.ui_config.responsive.input_height,
                    readonly=not editable,
                    background_color=self.ui_config.colors.background
                )
                
        except Exception as e:
            logger.error(f"Error creating input widget: {e}")
            return self.create_label("Error creating input")
    
    def _create_button_layout(self):
        """Create the button layout."""
        try:
            button_layout = BoxLayout(
                orientation='horizontal', 
                size_hint_y=None, 
                height=self.ui_config.responsive.button_height, 
                spacing=self.ui_config.responsive.spacing_desktop
            )
            
            # Save button
            save_btn = self.create_button(
                text='Save Changes',
                size_hint_x=0.3,
                on_release=self._on_save
            )
            button_layout.add_widget(save_btn)
            
            # Delete button
            delete_btn = self.create_button(
                text='Delete',
                size_hint_x=0.3,
                on_release=self._on_delete
            )
            delete_btn.background_color = self.ui_config.colors.error
            button_layout.add_widget(delete_btn)
            
            # Cancel button
            cancel_btn = self.create_button(
                text='Cancel',
                size_hint_x=0.3,
                on_release=self._on_cancel
            )
            button_layout.add_widget(cancel_btn)
            
            return button_layout
            
        except Exception as e:
            logger.error(f"Error creating button layout: {e}")
            return BoxLayout()
    
    def _validate_date(self, date_str):
        """Validate date format."""
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, ""
        except ValueError:
            return False, "Invalid date format (YYYY-MM-DD required)"
    
    def _validate_amount(self, amount_str):
        """Validate amount format."""
        try:
            if isinstance(amount_str, str):
                amount_str = amount_str.replace('$', '').replace(',', '')
            float(amount_str)
            return True, ""
        except ValueError:
            return False, "Invalid amount format"
    
    def _validate_form(self):
        """Validate all form fields."""
        errors = []
        
        try:
            for field_config in self.field_configs:
                field_key = field_config[1]
                validator = field_config[4] if len(field_config) > 4 else None
                required = field_config[5] if len(field_config) > 5 else False
                
                widget = self.input_fields.get(field_key)
                if not widget:
                    continue
                
                value = getattr(widget, 'text', '')
                
                # Check required fields
                if required and not value.strip():
                    errors.append(f"{field_config[0]} is required")
                    continue
                
                # Run validator if provided
                if validator and value.strip():
                    is_valid, error_msg = validator(value)
                    if not is_valid:
                        errors.append(f"{field_config[0]}: {error_msg}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating form: {e}")
            return False, ["Validation error occurred"]
    
    def _validate_form(self):
        """Validate form fields and return validation status and errors."""
        errors = []
        
        try:
            # Check required fields based on field_configs
            for field_config in self.field_configs:
                field_key = field_config['key']
                field_name = field_config['label']
                is_required = field_config.get('required', False)
                
                if is_required and field_key in self.input_fields:
                    widget = self.input_fields[field_key]
                    value = getattr(widget, 'text', '').strip()
                    
                    if not value:
                        errors.append(f"{field_name} is required")
                        continue
                    
                    # Validate amount field
                    if field_key == 'TRANSAMOUNT':
                        try:
                            # Remove currency symbols and convert
                            amount_str = value.replace('$', '').replace(',', '').strip()
                            if amount_str:
                                float(amount_str)
                        except ValueError:
                            errors.append(f"Invalid {field_name} format")
                    
                    # Validate date field
                    elif field_key == 'TRANSDATE':
                        if not self._validate_date_format(value):
                            errors.append(f"Invalid {field_name} format")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating form: {e}")
            return False, ["Validation error occurred"]
    
    def _validate_date_format(self, date_str):
        """Validate date format."""
        try:
            from datetime import datetime
            # Try common date formats
            date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
            
            for fmt in date_formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False
    
    def _on_save(self, instance):
        """Handle save button press with improved validation."""
        try:
            # Validate form
            is_valid, errors = self._validate_form()
            if not is_valid:
                error_message = "\n".join(errors)
                popup = create_popup(
                    title='Validation Error',
                    content=self.create_label(error_message),
                    size_hint=(0.6, 0.4)
                )
                show_popup(popup)
                return
            
            # Collect updated data from input fields
            updated_data = self.transaction_data.copy()
            
            for field_key, widget in self.input_fields.items():
                if hasattr(widget, 'text'):
                    updated_data[field_key] = widget.text
            
            # Call save callback if provided
            if self.on_save_callback:
                self.on_save_callback(updated_data)
            
            self.popup.dismiss()
            
        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            self.show_error("Error saving transaction")
    
    def _on_delete(self, instance):
        """Handle delete button press with confirmation."""
        try:
            # Create confirmation content
            content_layout = BoxLayout(orientation='vertical', spacing=10)
            content_layout.add_widget(
                self.create_label('Are you sure you want to delete this transaction?')
            )
            
            # Create button layout for confirmation
            button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
            
            # Confirm delete button
            confirm_btn = self.create_button(
                text='Yes, Delete',
                size_hint_x=0.5,
                on_release=lambda x: self._confirm_delete()
            )
            confirm_btn.background_color = self.ui_config.colors.error
            button_layout.add_widget(confirm_btn)
            
            # Cancel button
            cancel_btn = self.create_button(
                text='Cancel',
                size_hint_x=0.5,
                on_release=lambda x: self.confirm_popup.dismiss()
            )
            button_layout.add_widget(cancel_btn)
            
            content_layout.add_widget(button_layout)
            
            # Create and show confirmation popup
            self.confirm_popup = create_popup(
                title='Confirm Delete',
                content=content_layout,
                size_hint=(0.6, 0.4),
                auto_dismiss=False
            )
            show_popup(self.confirm_popup)
            
        except Exception as e:
            logger.error(f"Error showing delete confirmation: {e}")
            self.show_error("Error showing delete confirmation")
    
    def _confirm_delete(self):
        """Confirm and execute delete operation."""
        try:
            if self.on_delete_callback:
                self.on_delete_callback(self.transaction_data)
            self.confirm_popup.dismiss()
            self.popup.dismiss()
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            self.show_error("Error deleting transaction")
    
    def _on_cancel(self, instance):
        """Handle cancel button press."""
        try:
            self.popup.dismiss()
        except Exception as e:
            logger.error(f"Error canceling popup: {e}")
        