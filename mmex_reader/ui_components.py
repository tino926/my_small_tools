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
from kivy.graphics import Color, Rectangle
import pandas as pd

# UI color constants
BG_COLOR = (0.9, 0.9, 0.9, 1)  # Light gray background
HEADER_COLOR = (0.2, 0.6, 0.8, 1)  # Blue header
BUTTON_COLOR = (0.3, 0.5, 0.7, 1)  # Slightly darker blue for buttons
HIGHLIGHT_COLOR = (0.1, 0.7, 0.1, 1)  # Green for highlights

class AccountTabContent(BoxLayout):
    """Content for an account-specific tab."""
    
    def __init__(self, account_id, account_name, **kwargs):
        super(AccountTabContent, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.account_id = account_id
        self.account_name = account_name
        self.padding = 10
        self.spacing = 10
        
        # Account info header
        self.header = BoxLayout(size_hint=(1, 0.1), spacing=10)
        
        # Account name label
        self.account_label = Label(
            text=f"Account: {account_name}",
            size_hint=(0.7, 1),
            halign='left',
            valign='middle',
            text_size=(None, None)  # Will be set in on_size
        )
        self.header.add_widget(self.account_label)
        
        # Balance label
        self.balance_label = Label(
            text="Balance: Loading...",
            size_hint=(0.3, 1),
            halign='right',
            valign='middle',
            text_size=(None, None)  # Will be set in on_size
        )
        self.header.add_widget(self.balance_label)
        
        self.add_widget(self.header)
        
        # Transactions grid in a scroll view
        self.scroll_view = ScrollView(size_hint=(1, 0.9))
        
        # Grid for transactions
        self.grid = GridLayout(cols=7, spacing=2, size_hint_y=None)
        # The height will be set based on the children
        self.grid.bind(minimum_height=self.grid.setter('height'))
        
        # Add grid to scroll view
        self.scroll_view.add_widget(self.grid)
        
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

def populate_grid_with_dataframe(grid, df, headers=None, sort_callback=None):
    """Populate a grid layout with data from a DataFrame.
    
    Args:
        grid: The GridLayout to populate
        df: The DataFrame containing the data
        headers: Optional list of column headers
        sort_callback: Optional callback function for sorting
    """
    # Clear existing widgets
    grid.clear_widgets()
    
    # Set number of columns based on headers or DataFrame columns
    if headers:
        grid.cols = len(headers)
    else:
        grid.cols = len(df.columns) if not df.empty else 1
    
    # Handle empty DataFrame
    if df.empty:
        grid.add_widget(Label(text="No data available", size_hint_y=None, height=40))
        return
    
    # Add headers if provided
    if headers:
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
        
        for header in headers:
            if sort_callback and header in column_mapping:
                # Create sortable header button
                header_btn = SortableHeaderButton(
                    text=header,
                    column_name=column_mapping[header],
                    sort_callback=sort_callback
                )
                grid.add_widget(header_btn)
            else:
                # Create regular header label
                grid.add_widget(create_header_label(header))
    
    # Add data rows
    for _, row in df.iterrows():
        for col in df.columns:
            value = row[col]
            # Format value based on column type
            if col == 'TRANSAMOUNT' or col == 'TOTRANSAMOUNT':
                text = f"${value:.2f}" if pd.notna(value) else ""
            elif col == 'TRANSDATE':
                text = str(value).split()[0] if pd.notna(value) else ""  # Just the date part
            else:
                text = str(value) if pd.notna(value) else ""
            
            label = Label(
                text=text,
                size_hint_y=None,
                height=30,
                text_size=(None, None),  # Will be set based on width
                halign='left',
                valign='middle'
            )
            
            # Bind size to update text_size
            def update_text_size(label, *args):
                label.text_size = (label.width, None)
            
            label.bind(width=update_text_size)
            
            grid.add_widget(label)