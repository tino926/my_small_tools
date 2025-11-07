"""Kivy Language compatible UI components for the MMEX application.

This module provides UI components that are designed to work with Kivy Language (.kv) files,
allowing for better separation of UI definition and application logic.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
import pandas as pd


class DateInputLayout(BoxLayout):
    """Layout for date input controls with start and end date fields."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        
    def get_start_date(self):
        """Get the start date from the input field."""
        return self.ids.start_date_input.text
        
    def get_end_date(self):
        """Get the end date from the input field."""
        return self.ids.end_date_input.text
        
    def set_start_date(self, date_str):
        """Set the start date in the input field."""
        self.ids.start_date_input.text = date_str
        
    def set_end_date(self, date_str):
        """Set the end date in the input field."""
        self.ids.end_date_input.text = date_str


class SearchFilterLayout(BoxLayout):
    """Layout for search and filter controls."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        
    def get_search_text(self):
        """Get the search text from the input field."""
        return self.ids.search_input.text
        
    def set_search_text(self, text):
        """Set the search text in the input field."""
        self.ids.search_input.text = text
        
    def clear_search(self):
        """Clear the search input field."""
        self.ids.search_input.text = ""


class TransactionGrid(GridLayout):
    """Grid layout for displaying transaction data."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 7  # Date, Account, Payee, Category, Tags, Notes, Amount
        
    def _on_header_press(self, instance, header, callback):
        """處理標題按鈕點擊事件，確保正確傳遞列名稱到排序回調函數。
        
        Args:
            instance: 按鈕實例
            header: 列標題名稱
            callback: 排序回調函數
        """
        callback(header)
        
    def populate_with_dataframe(self, df, headers, sort_callback=None, row_click_callback=None):
        """Populate the grid with DataFrame data."""
        self.clear_widgets()
        
        # Add headers
        for header in headers:
            header_btn = Button(
                text=header,
                size_hint_y=None,
                height=35,
                background_color=(0.8, 0.8, 0.8, 1)
            )
            if sort_callback:
                # 使用 functools.partial 來確保正確捕獲每個列名稱
                from functools import partial
                header_btn.bind(on_press=partial(self._on_header_press, header=header, callback=sort_callback))
            self.add_widget(header_btn)
        
        # Add data rows
        for index, row in df.iterrows():
            for col in headers:
                value = str(row.get(col, ''))
                cell_btn = Button(
                    text=value,
                    size_hint_y=None,
                    height=35,
                    background_color=(1, 1, 1, 1),
                    color=(0, 0, 0, 1)
                )
                if row_click_callback:
                    cell_btn.bind(on_press=lambda x, r=row: row_click_callback(r))
                self.add_widget(cell_btn)


class PaginationControls(BoxLayout):
    """Controls for pagination navigation."""
    
    current_page = NumericProperty(1)
    total_pages = NumericProperty(1)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        
    def update_pagination_info(self, current_page, total_pages, total_items, page_size):
        """Update pagination information display."""
        self.current_page = current_page
        self.total_pages = total_pages
        
        start_item = (current_page - 1) * page_size + 1
        end_item = min(current_page * page_size, total_items)
        
        info_text = f"Page {current_page} of {total_pages} (Items {start_item}-{end_item} of {total_items})"
        self.ids.pagination_info.text = info_text
        self.ids.page_input.text = str(current_page)
        
        # Update button states
        self.ids.prev_button.disabled = (current_page <= 1)
        self.ids.next_button.disabled = (current_page >= total_pages)
        
    def on_previous_page(self):
        """Handle previous page button click."""
        if self.current_page > 1:
            return self.current_page - 1
        return self.current_page
        
    def on_next_page(self):
        """Handle next page button click."""
        if self.current_page < self.total_pages:
            return self.current_page + 1
        return self.current_page
        
    def on_page_input(self):
        """Handle direct page input."""
        try:
            page = int(self.ids.page_input.text)
            if 1 <= page <= self.total_pages:
                return page
        except ValueError:
            pass
        return self.current_page


class AccountTabContent(BoxLayout):
    """Content for account-specific tabs."""
    
    account_name = StringProperty("")
    account_balance = StringProperty("$0.00")
    
    def __init__(self, account_id, account_name, initial_balance=0, **kwargs):
        super().__init__(**kwargs)
        self.account_id = account_id
        self.account_name = account_name
        self.account_balance = f"${initial_balance:.2f}"
        self.orientation = 'vertical'
        
    def update_balance(self, balance):
        """Update the account balance display."""
        self.account_balance = f"${balance:.2f}"
        if hasattr(self, 'ids') and 'balance_label' in self.ids:
            self.ids.balance_label.text = self.account_balance
            
    def update_status(self, status_text):
        """Update the status label."""
        if hasattr(self, 'ids') and 'status_label' in self.ids:
            self.ids.status_label.text = status_text
            
    def populate_transactions(self, df, headers, sort_callback=None, row_click_callback=None):
        """Populate the results grid with transaction data."""
        if hasattr(self, 'ids') and 'results_grid' in self.ids:
            grid = self.ids.results_grid
            grid.clear_widgets()
            
            # Add headers
            for header in headers:
                header_btn = Button(
                    text=header,
                    size_hint_y=None,
                    height=35,
                    background_color=(0.8, 0.8, 0.8, 1)
                )
                if sort_callback:
                    header_btn.bind(on_press=lambda x, col=header: sort_callback(col))
                grid.add_widget(header_btn)
            
            # Add data rows
            for index, row in df.iterrows():
                for col in headers:
                    value = str(row.get(col, ''))
                    cell_btn = Button(
                        text=value,
                        size_hint_y=None,
                        height=35,
                        background_color=(1, 1, 1, 1),
                        color=(0, 0, 0, 1)
                    )
                    if row_click_callback:
                        cell_btn.bind(on_press=lambda x, r=row: row_click_callback(r))
                    grid.add_widget(cell_btn)


class VisualizationContent(BoxLayout):
    """Content for data visualization with chart controls."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
    def update_chart(self, transactions_df):
        """Update the chart based on selected chart type and data."""
        if hasattr(self, 'ids') and 'chart_layout' in self.ids:
            chart_layout = self.ids.chart_layout
            chart_layout.clear_widgets()
            
            if transactions_df.empty:
                chart_layout.add_widget(
                    Label(text="No transaction data available for visualization")
                )
                return
                
            # Get selected chart type
            chart_type = "Monthly Spending"  # Default
            if hasattr(self, 'ids') and 'chart_type_spinner' in self.ids:
                chart_type = self.ids.chart_type_spinner.text
                
            # Create appropriate chart based on type
            try:
                from visualization import create_chart_widget
                chart_widget = create_chart_widget(transactions_df, chart_type)
                chart_layout.add_widget(chart_widget)
            except ImportError:
                chart_layout.add_widget(
                    Label(text=f"Chart: {chart_type}\n(Visualization module not available)")
                )
            except Exception as e:
                chart_layout.add_widget(
                    Label(text=f"Error creating chart: {str(e)}")
                )