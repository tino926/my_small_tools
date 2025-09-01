"""UI components for the MMEX Kivy application.

This module provides UI component classes for the MMEX Kivy application,
including account tab content and other reusable UI elements.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
import pandas as pd
from datetime import datetime, timedelta
import calendar

# UI color constants
BG_COLOR = (0.9, 0.9, 0.9, 1)  # Light gray background
HEADER_COLOR = (0.2, 0.6, 0.8, 1)  # Blue header
BUTTON_COLOR = (0.3, 0.5, 0.7, 1)  # Slightly darker blue for buttons
HIGHLIGHT_COLOR = (0.1, 0.7, 0.1, 1)  # Green for highlights


class DatePickerWidget(BoxLayout):
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
                self.current_date = datetime.strptime(initial_date, "%Y-%m-%d")
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
        header_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
        
        # Previous month button
        prev_btn = Button(text='<', size_hint=(None, 1), width=40, background_color=BUTTON_COLOR)
        prev_btn.bind(on_release=self._prev_month)
        header_layout.add_widget(prev_btn)
        
        # Month/Year label
        self.month_year_label = Label(
            text=self.current_date.strftime("%B %Y"),
            size_hint=(1, 1),
            halign='center',
            valign='middle'
        )
        self.month_year_label.bind(size=self.month_year_label.setter('text_size'))
        header_layout.add_widget(self.month_year_label)
        
        # Next month button
        next_btn = Button(text='>', size_hint=(None, 1), width=40, background_color=BUTTON_COLOR)
        next_btn.bind(on_release=self._next_month)
        header_layout.add_widget(next_btn)
        
        self.add_widget(header_layout)
        
    def _create_calendar(self):
        """Create the calendar grid."""
        # Day headers
        day_headers = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30)
        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            label = Label(text=day, size_hint=(1, 1), bold=True)
            day_headers.add_widget(label)
        self.add_widget(day_headers)
        
        # Calendar grid
        self.calendar_grid = GridLayout(cols=7, size_hint=(1, 1), spacing=2)
        self._populate_calendar()
        self.add_widget(self.calendar_grid)
        
    def _create_footer(self):
        """Create the footer with action buttons."""
        footer_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=10)
        
        # Today button
        today_btn = Button(text='Today', size_hint=(0.5, 1), background_color=HIGHLIGHT_COLOR)
        today_btn.bind(on_release=self._select_today)
        footer_layout.add_widget(today_btn)
        
        # Cancel button
        cancel_btn = Button(text='Cancel', size_hint=(0.5, 1), background_color=(0.7, 0.3, 0.3, 1))
        cancel_btn.bind(on_release=self._cancel)
        footer_layout.add_widget(cancel_btn)
        
        self.add_widget(footer_layout)
        
    def _populate_calendar(self):
        """Populate the calendar grid with day buttons."""
        self.calendar_grid.clear_widgets()
        
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
                        background_color=BG_COLOR
                    )
                    
                    # Highlight selected date
                    if (day == self.selected_date.day and 
                        self.current_date.month == self.selected_date.month and
                        self.current_date.year == self.selected_date.year):
                        day_btn.background_color = HIGHLIGHT_COLOR
                    
                    # Highlight today
                    today = datetime.now()
                    if (day == today.day and 
                        self.current_date.month == today.month and
                        self.current_date.year == today.year):
                        day_btn.background_color = HEADER_COLOR
                    
                    day_btn.bind(on_release=lambda btn, d=day: self._select_date(d))
                    self.calendar_grid.add_widget(day_btn)
                    
    def _prev_month(self, instance):
        """Navigate to previous month."""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self._update_display()
        
    def _next_month(self, instance):
        """Navigate to next month."""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self._update_display()
        
    def _update_display(self):
        """Update the calendar display."""
        self.month_year_label.text = self.current_date.strftime("%B %Y")
        self._populate_calendar()
        
    def _select_date(self, day):
        """Select a specific date."""
        self.selected_date = self.current_date.replace(day=day)
        self._populate_calendar()
        if self.callback:
            self.callback(self.selected_date.strftime("%Y-%m-%d"))
            
    def _select_today(self, instance):
        """Select today's date."""
        today = datetime.now()
        self.current_date = today
        self.selected_date = today
        self._update_display()
        if self.callback:
            self.callback(self.selected_date.strftime("%Y-%m-%d"))
            
    def _cancel(self, instance):
        """Cancel date selection."""
        if self.callback:
            self.callback(None)
            
    def get_selected_date(self):
        """Get the currently selected date as a string."""
        return self.selected_date.strftime("%Y-%m-%d")


class DatePickerButton(Button):
    """A button that opens a date picker when clicked."""
    
    def __init__(self, initial_date=None, date_change_callback=None, **kwargs):
        super(DatePickerButton, self).__init__(**kwargs)
        self.date_change_callback = date_change_callback
        self.background_color = BUTTON_COLOR
        
        # Set initial date
        if initial_date:
            self.current_date = initial_date
        else:
            self.current_date = datetime.now().strftime("%Y-%m-%d")
            
        self.text = self.current_date
        self.bind(on_release=self._open_date_picker)
        
    def _open_date_picker(self, instance):
        """Open the date picker popup."""
        date_picker = DatePickerWidget(
            initial_date=self.current_date,
            callback=self._on_date_selected
        )
        
        self.popup = Popup(
            title='Select Date',
            content=date_picker,
            size_hint=(None, None),
            size=(320, 400),
            auto_dismiss=True
        )
        self.popup.open()
        
    def _on_date_selected(self, selected_date):
        """Handle date selection from picker."""
        if selected_date:
            self.current_date = selected_date
            self.text = selected_date
            if self.date_change_callback:
                self.date_change_callback(self, selected_date)
        self.popup.dismiss()
        
    def get_date(self):
        """Get the current date value."""
        return self.current_date
        
    def set_date(self, date_str):
        """Set the date value."""
        self.current_date = date_str
        self.text = date_str

class AccountTabContent(BoxLayout):
    """Content for an account-specific tab with responsive design."""
    
    def __init__(self, account_id, account_name, **kwargs):
        super(AccountTabContent, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.account_id = account_id
        self.account_name = account_name
        
        # Determine responsive properties
        from kivy.core.window import Window
        screen_width = Window.width
        
        if screen_width <= 600:  # Mobile
            self.padding = 5
            self.spacing = 3
            self.is_mobile = True
        elif screen_width <= 1024:  # Tablet
            self.padding = 8
            self.spacing = 5
            self.is_mobile = False
        else:  # Desktop
            self.padding = 10
            self.spacing = 10
            self.is_mobile = False
        
        # Account info header with responsive layout
        if self.is_mobile:
            # Stack account info vertically on mobile
            self.header = BoxLayout(orientation='vertical', size_hint=(1, None), height=60, spacing=self.spacing)
            
            # Account name label
            self.account_label = Label(
                text=f"Account: {account_name}",
                size_hint=(1, 0.5),
                halign='center',
                valign='middle',
                text_size=(None, None)
            )
            self.header.add_widget(self.account_label)
            
            # Balance label
            self.balance_label = Label(
                text="Balance: Loading...",
                size_hint=(1, 0.5),
                halign='center',
                valign='middle',
                text_size=(None, None)
            )
            self.header.add_widget(self.balance_label)
        else:
            # Horizontal layout for larger screens
            self.header = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40, spacing=self.spacing)
            
            # Account name label
            self.account_label = Label(
                text=f"Account: {account_name}",
                size_hint=(0.7, 1),
                halign='left',
                valign='middle',
                text_size=(None, None)
            )
            self.header.add_widget(self.account_label)
            
            # Balance label
            self.balance_label = Label(
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

def show_popup(title, message):
    """Show a popup with the given title and message.
    
    Args:
        title: The popup title
        message: The message to display
    """
    content = BoxLayout(orientation='vertical', padding=10, spacing=10)
    content.add_widget(Label(text=message))
    
    # Add OK button
    btn = Button(text="OK", size_hint=(1, 0.2))
    content.add_widget(btn)
    
    # Create popup
    popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
    
    # Bind button to close popup
    btn.bind(on_release=popup.dismiss)
    
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

def create_header_label(text):
    """Create a styled header label.
    
    Args:
        text: The label text
        
    Returns:
        A styled Label widget
    """
    label = Label(
        text=text,
        size_hint_y=None,
        height=40,
        bold=True,
        color=(1, 1, 1, 1)  # White text
    )
    
    # Add background color
    with label.canvas.before:
        Color(*HEADER_COLOR)
        label.rect = Rectangle(pos=label.pos, size=label.size)
    
    # Update rectangle position and size when the label changes
    def update_rect(instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size
    
    label.bind(pos=update_rect, size=update_rect)
    
    return label

def _create_data_label(text, num_columns):
    """Create a data label with proper formatting and binding.
    
    Args:
        text: The text to display
        num_columns: Number of columns for width calculation
        
    Returns:
        Configured Label widget
    """
    label = Label(
        text=text,
        size_hint_y=None,
        height=30,
        size_hint_x=1/num_columns,
        text_size=(None, 30),
        halign='left',
        valign='middle',
        shorten=True,
        shorten_from='right'
    )
    
    # Bind size to update text_size
    def update_text_size(instance, value):
        instance.text_size = (value, 30)
    
    label.bind(width=update_text_size)
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
    # Clear existing widgets
    grid.clear_widgets()
    
    # Determine if we're on mobile based on grid column count
    is_mobile = grid.cols == 4
    
    # Define mobile-friendly column subsets
    if is_mobile and headers:
        # Show only essential columns on mobile
        mobile_headers = ["Date", "Payee", "Amount", "Category"]
        display_headers = [h for h in mobile_headers if h in headers]
        grid.cols = len(display_headers)
    else:
        display_headers = headers if headers else list(df.columns)
        if headers:
            grid.cols = len(headers)
        else:
            grid.cols = len(df.columns) if not df.empty else 1
    
    # Handle empty DataFrame
    if df.empty:
        grid.add_widget(Label(text="No data available", size_hint_y=None, height=40))
        return
    
    # Add headers if provided
    if display_headers:
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
    
    # Add data rows with responsive column filtering
    if display_headers:
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
        
        display_columns = [header_to_column.get(h, h) for h in display_headers if header_to_column.get(h, h) in df.columns]
    else:
        display_columns = df.columns
    
    for row_index, row in df.iterrows():
        # Create a list to store row widgets for click handling
        row_widgets = []
        
        for col in display_columns:
            value = row[col]
            # Format value based on column type
            if col in ('TRANSAMOUNT', 'TOTRANSAMOUNT'):
                text = f"${value:.2f}" if pd.notna(value) else ""
            elif col == 'TRANSDATE':
                text = str(value).split()[0] if pd.notna(value) else ""
            else:
                text = str(value) if pd.notna(value) else ""
            
            label = _create_data_label(text, len(display_columns))
            
            # Bind size to update text_size
            def update_text_size(label, *args):
                label.text_size = (label.width, None)
            
            label.bind(width=update_text_size)
            
            # Add click handling if callback is provided
            if row_click_callback:
                # Create a clickable button instead of label for better touch handling
                clickable_label = Button(
                    text=text,
                    size_hint_y=None,
                    height=UIConstants.ROW_HEIGHT,
                    size_hint_x=1/len(display_columns),
                    halign='left',
                    valign='middle',
                    background_color=(1, 1, 1, 0.1),  # Subtle background
                    color=(0, 0, 0, 1)  # Text color
                )
                clickable_label.text_size = (None, None)
                clickable_label.bind(size=clickable_label.setter('text_size'))
                
                # Bind click event with row data
                def on_row_click(instance, row_data=row.to_dict()):
                    row_click_callback(row_data)
                
                clickable_label.bind(on_press=on_row_click)
                grid.add_widget(clickable_label)
            else:
                grid.add_widget(label)


class TransactionDetailsPopup:
    """A popup component for displaying and editing transaction details."""
    
    def __init__(self, transaction_data, on_save_callback=None, on_delete_callback=None):
        """
        Initialize the transaction details popup.
        
        Args:
            transaction_data: Dictionary containing transaction information
            on_save_callback: Callback function when transaction is saved
            on_delete_callback: Callback function when transaction is deleted
        """
        self.transaction_data = transaction_data.copy() if transaction_data else {}
        self.on_save_callback = on_save_callback
        self.on_delete_callback = on_delete_callback
        self.popup = None
        self.input_fields = {}
        
    def show(self):
        """Display the transaction details popup."""
        content = self._create_content()
        
        self.popup = Popup(
            title=f"Transaction Details - {self.transaction_data.get('TRANSDATE', 'Unknown Date')}",
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )
        self.popup.open()
        
    def _create_content(self):
        """Create the main content layout for the popup."""
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Create scroll view for form fields
        scroll = ScrollView()
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        
        # Define field configurations
        field_configs = [
            ('Transaction ID', 'TRANSID', False),  # Read-only
            ('Date', 'TRANSDATE', True),
            ('Account', 'ACCOUNTNAME', False),  # Read-only for now
            ('Payee', 'PAYEENAME', True),
            ('Category', 'CATEGNAME', True),
            ('Amount', 'TRANSAMOUNT', True),
            ('Transaction Code', 'TRANSCODE', True),
            ('Notes', 'NOTES', True),
            ('Tags', 'TAGNAMES', True),
            ('Status', 'STATUS', True),
            ('Follow Up', 'FOLLOWUPID', True)
        ]
        
        # Create form fields
        for label_text, field_key, editable in field_configs:
            # Add label
            label = Label(
                text=f"{label_text}:",
                size_hint_y=None,
                height=40,
                halign='right',
                valign='middle'
            )
            label.bind(size=label.setter('text_size'))
            form_layout.add_widget(label)
            
            # Add input field
            value = str(self.transaction_data.get(field_key, '')) if self.transaction_data.get(field_key) is not None else ''
            
            if field_key == 'NOTES':
                # Multi-line text input for notes
                text_input = TextInput(
                    text=value,
                    multiline=True,
                    size_hint_y=None,
                    height=80,
                    readonly=not editable
                )
            elif field_key == 'TRANSCODE':
                # Dropdown for transaction code
                spinner = Spinner(
                    text=value if value else 'Withdrawal',
                    values=['Withdrawal', 'Deposit', 'Transfer'],
                    size_hint_y=None,
                    height=40,
                    disabled=not editable
                )
                self.input_fields[field_key] = spinner
                form_layout.add_widget(spinner)
                continue
            elif field_key == 'STATUS':
                # Dropdown for status
                spinner = Spinner(
                    text=value if value else 'None',
                    values=['None', 'Reconciled', 'Void', 'Follow up', 'Duplicate'],
                    size_hint_y=None,
                    height=40,
                    disabled=not editable
                )
                self.input_fields[field_key] = spinner
                form_layout.add_widget(spinner)
                continue
            else:
                # Regular text input
                text_input = TextInput(
                    text=value,
                    multiline=False,
                    size_hint_y=None,
                    height=40,
                    readonly=not editable
                )
            
            self.input_fields[field_key] = text_input
            form_layout.add_widget(text_input)
        
        scroll.add_widget(form_layout)
        main_layout.add_widget(scroll)
        
        # Add button layout
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        # Save button
        save_btn = Button(text='Save Changes', size_hint_x=0.3)
        save_btn.bind(on_press=self._on_save)
        button_layout.add_widget(save_btn)
        
        # Delete button
        delete_btn = Button(text='Delete', size_hint_x=0.3)
        delete_btn.bind(on_press=self._on_delete)
        button_layout.add_widget(delete_btn)
        
        # Cancel button
        cancel_btn = Button(text='Cancel', size_hint_x=0.3)
        cancel_btn.bind(on_press=self._on_cancel)
        button_layout.add_widget(cancel_btn)
        
        main_layout.add_widget(button_layout)
        
        return main_layout
    
    def _on_save(self, instance):
        """Handle save button press."""
        # Collect updated data from input fields
        updated_data = self.transaction_data.copy()
        
        for field_key, widget in self.input_fields.items():
            if hasattr(widget, 'text'):
                updated_data[field_key] = widget.text
            elif hasattr(widget, 'text') and isinstance(widget, Spinner):
                updated_data[field_key] = widget.text
        
        # Validate required fields
        if not updated_data.get('TRANSDATE'):
            show_popup('Validation Error', 'Transaction date is required.')
            return
            
        if not updated_data.get('TRANSAMOUNT'):
            show_popup('Validation Error', 'Transaction amount is required.')
            return
        
        # Try to convert amount to float
        try:
            amount_str = updated_data.get('TRANSAMOUNT', '0')
            if isinstance(amount_str, str):
                # Remove currency symbols and convert
                amount_str = amount_str.replace('$', '').replace(',', '')
            float(amount_str)
            updated_data['TRANSAMOUNT'] = amount_str
        except ValueError:
            show_popup('Validation Error', 'Invalid amount format.')
            return
        
        # Call save callback if provided
        if self.on_save_callback:
            self.on_save_callback(updated_data)
        
        self.popup.dismiss()
    
    def _on_delete(self, instance):
        """Handle delete button press."""
        # Show confirmation dialog
        def confirm_delete(confirm_instance):
            if self.on_delete_callback:
                self.on_delete_callback(self.transaction_data)
            confirm_popup.dismiss()
            self.popup.dismiss()
        
        def cancel_delete(cancel_instance):
            confirm_popup.dismiss()
        
        confirm_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        confirm_layout.add_widget(Label(text='Are you sure you want to delete this transaction?'))
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        yes_btn = Button(text='Yes, Delete')
        yes_btn.bind(on_press=confirm_delete)
        button_layout.add_widget(yes_btn)
        
        no_btn = Button(text='Cancel')
        no_btn.bind(on_press=cancel_delete)
        button_layout.add_widget(no_btn)
        
        confirm_layout.add_widget(button_layout)
        
        confirm_popup = Popup(
            title='Confirm Delete',
            content=confirm_layout,
            size_hint=(0.6, 0.4),
            auto_dismiss=False
        )
        confirm_popup.open()
    
    def _on_cancel(self, instance):
        """Handle cancel button press."""
        self.popup.dismiss()
            
        grid.add_widget(label)
        
    # Bind size to update text_size
    def update_text_size(label, *args):
        label.text_size = (label.width, None)
    
    label.bind(width=update_text_size)
    
    grid.add_widget(label)
        