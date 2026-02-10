from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from typing import Optional, Callable, Any, List, Dict
import datetime
from datetime import datetime
import calendar
import logging

from .config import ui_config, HEADER_COLOR
from .base import BaseUIComponent

logger = logging.getLogger(__name__)

# =============================================================================
# POPUP UTILITIES
# =============================================================================

def create_popup(title: str, content_widget: Any = None, buttons: Optional[List[Dict]] = None, 
                size_hint=(0.8, 0.4), auto_dismiss=True, popup_type: str = 'info', **kwargs) -> Popup:
    """Create a standardized popup with consistent styling."""
    
    # Map popup type to color style
    type_color_map = {
        'error': ui_config.colors.error,
        'warning': ui_config.colors.warning,
        'success': ui_config.colors.success,
        'info': ui_config.colors.button
    }
    header_color = type_color_map.get(popup_type, ui_config.colors.button)
    
    # Handle kwargs overlap with explicit args
    default_props = {
        'title': title,
        'size_hint': size_hint,
        'auto_dismiss': auto_dismiss,
        'separator_color': header_color
    }
    default_props.update(kwargs)
    
    # Create main layout
    main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    
    # Add content widget
    if content_widget:
        main_layout.add_widget(content_widget)
    
    # Add buttons if provided
    if buttons:
        button_layout = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=50,
            spacing=10
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
    
    # Add key binding for ESC to dismiss
    def _on_key_down(window, key, scancode, codepoint, modifiers):
        if key == 27:  # ESC
            try:
                popup.dismiss()
            except Exception:
                pass
            return True
        return False
    
    try:
        Window.bind(on_key_down=_on_key_down)
        def _cleanup(instance):
            try:
                Window.unbind(on_key_down=_on_key_down)
            except Exception:
                pass
        popup.bind(on_dismiss=_cleanup)
    except Exception:
        pass

    return popup

def show_popup(title: str, message: str, popup_type: str = 'info') -> None:
    """Show a simple message popup."""
    # Create message label
    content = Label(
        text=message,
        text_size=(None, None),
        halign='center',
        valign='middle'
    )
    # Ensure center alignment
    content.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
    
    # Set color based on popup type
    color_map = {
        'error': ui_config.colors.error,
        'warning': ui_config.colors.warning,
        'success': ui_config.colors.success,
        'info': ui_config.colors.button
    }
    
    # Apply subtle tint via canvas
    tint = color_map.get(popup_type, ui_config.colors.button)
    with content.canvas.before:
        Color(*tint)
        rect = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda inst, val: setattr(rect, 'pos', inst.pos))
        content.bind(size=lambda inst, val: setattr(rect, 'size', inst.size))
    
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
# WIDGETS
# =============================================================================

class DatePickerWidget(BaseUIComponent):
    """A calendar widget for date selection."""
    
    def __init__(self, initial_date=None, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.callback = callback
        
        # Parse initial date
        try:
            if initial_date:
                if isinstance(initial_date, str):
                    self.current_date = datetime.strptime(initial_date, "%Y-%m-%d")
                else:
                    self.current_date = initial_date
            else:
                self.current_date = datetime.now()
        except Exception:
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
            show_popup("Error", f"Error creating calendar: {e}", "error")
                    
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
            show_popup("Error", "Error navigating calendar", "error")
        
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
            show_popup("Error", "Error navigating calendar", "error")
        
    def _update_display(self):
        """Update the calendar display."""
        try:
            self.month_year_label.text = self.current_date.strftime("%B %Y")
            self._populate_calendar()
        except Exception as e:
            logger.error(f"Error updating calendar display: {e}")
            show_popup("Error", "Error updating calendar", "error")
        
    def _select_date(self, day):
        """Select a specific date."""
        try:
            self.selected_date = self.current_date.replace(day=day)
            self._populate_calendar()
            if self.callback:
                self.callback(self.selected_date.strftime("%Y-%m-%d"))
        except Exception as e:
            logger.error(f"Error selecting date: {e}")
            show_popup("Error", "Error selecting date", "error")
            
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
            show_popup("Error", "Error selecting today's date", "error")
            
    def _cancel(self, instance):
        """Cancel date selection."""
        if self.callback:
            self.callback(None)
            
    def get_selected_date(self):
        """Get the currently selected date as a string."""
        return self.selected_date.strftime("%Y-%m-%d")


class DatePickerButton(BaseUIComponent):
    """A button that opens a date picker when clicked."""
    
    def __init__(self, initial_date: Optional[str] = None, date_change_callback: Optional[Callable] = None, **kwargs):
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
        
    def _open_date_picker(self, instance: Any) -> None:
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
            self.popup.open()
            
        except Exception as e:
            logger.error(f"Error opening date picker: {e}")
            self.show_error("Error opening date picker")
        
    def _on_date_selected(self, selected_date: Optional[str]) -> None:
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
        
    def get_date(self) -> str:
        """Get the current date value."""
        return self.current_date
        
    def set_date(self, date_str: str) -> None:
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
    """Create a styled label with flexible configuration."""
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
            'size_hint_x': 1/num_columns if num_columns > 0 else 1,
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
