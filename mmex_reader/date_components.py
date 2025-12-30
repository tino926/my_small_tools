"""Date picker UI components for the MMEX Kivy application.

This module provides date picker widgets and interfaces.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import calendar

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

# Local imports
from .base_components import BaseUIComponent, ui_config

logger = logging.getLogger(__name__)


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
            height=ui_config.responsive.button_height
        )

        # Previous month button
        prev_btn = self.create_button(
            '<',
            callback=self._prev_month,
            size_hint=(None, 1),
            width=40,
            background_color=ui_config.colors.button
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
            width=40,
            background_color=ui_config.colors.button
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
            height=ui_config.responsive.button_height,
            spacing=ui_config.responsive.spacing
        )

        # Today button
        today_btn = self.create_button(
            'Today',
            callback=self._select_today,
            size_hint=(0.5, 1),
            background_color=ui_config.colors.highlight
        )
        footer_layout.add_widget(today_btn)

        # Cancel button
        cancel_btn = self.create_button(
            'Cancel',
            callback=self._cancel,
            size_hint=(0.5, 1),
            background_color=ui_config.colors.error
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
                            background_color=ui_config.colors.background
                        )

                        # Highlight selected date
                        if (day == self.selected_date.day and
                            self.current_date.month == self.selected_date.month and
                            self.current_date.year == self.selected_date.year):
                            day_btn.background_color = ui_config.colors.highlight

                        # Highlight today
                        today = datetime.now()
                        if (day == today.day and
                            self.current_date.month == today.month and
                            self.current_date.year == today.year):
                            day_btn.background_color = ui_config.colors.header

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

    def __init__(self, initial_date: Optional[str] = None, date_change_callback: Optional[Callable] = None, **kwargs):
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
            callback=self._open_date_picker
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
            self.popup = Popup(
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