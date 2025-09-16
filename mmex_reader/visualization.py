"""Visualization utilities for the MMEX Kivy application.

This module provides classes and functions for creating and displaying
financial data visualizations using Matplotlib and Kivy.
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

# UI color constants
BG_COLOR = (0.9, 0.9, 0.9, 1)  # Light gray background
HEADER_COLOR = (0.2, 0.6, 0.8, 1)  # Blue header
BUTTON_COLOR = (0.3, 0.5, 0.7, 1)  # Slightly darker blue for buttons
HIGHLIGHT_COLOR = (0.1, 0.7, 0.1, 1)  # Green for highlights

class VisualizationTab(BoxLayout):
    """A tab for displaying financial data visualizations."""
    
    def __init__(self, **kwargs):
        super(VisualizationTab, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        self.chart_type = "Spending by Category"  # Default chart type
        self.parent_app = None  # Will be set by parent
        
        # Chart type selection layout
        self.selection_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        
        # Chart type button
        self.chart_type_btn = Button(
            text=f"Chart Type: {self.chart_type}",
            size_hint=(0.8, 1),
            background_color=BUTTON_COLOR
        )
        self.chart_type_btn.bind(on_release=self.show_chart_options)
        self.selection_layout.add_widget(self.chart_type_btn)
        
        # Add selection layout to main layout
        self.add_widget(self.selection_layout)
        
        # Chart display area
        self.chart_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.9))
        self.info_label = Label(
            text="Select a chart type to visualize your financial data",
            size_hint=(1, 1)
        )
        self.chart_layout.add_widget(self.info_label)
        self.add_widget(self.chart_layout)
    
    def set_parent_app(self, app):
        """Set the parent application reference."""
        self.parent_app = app
    
    def show_chart_error(self, error_msg):
        """Display an error message in the chart area."""
        error_label = Label(
            text=error_msg,
            size_hint=(1, 1),
            color=(1, 0, 0, 1)  # Red color for error
        )
        self.chart_layout.clear_widgets()
        self.chart_layout.add_widget(error_label)
    
    def update_chart(self, transactions_df):
        """Update the chart with new transaction data."""
        try:
            if self.chart_type == "Spending by Category":
                chart = create_spending_by_category_chart(transactions_df)
            elif self.chart_type == "Spending Over Time":
                chart = create_spending_over_time_chart(transactions_df)
            elif self.chart_type == "Income vs Expenses":
                chart = create_income_vs_expenses_chart(transactions_df)
            elif self.chart_type == "Top Payees by Spending":
                chart = create_top_payees_chart(transactions_df)
            else:
                # Default to spending by category
                chart = create_spending_by_category_chart(transactions_df)
            
            self.chart_layout.clear_widgets()
            self.chart_layout.add_widget(chart)
        except Exception as chart_error:
            self.show_chart_error(f"Error generating chart: {str(chart_error)}")

    def show_chart(self, transactions_df):
        """Display the current chart with transaction data."""
        self.update_chart(transactions_df)

    def show_chart_options(self, instance):
        """Show chart options in a popup."""
        popup_layout = BoxLayout(orientation='vertical', padding=10)
        
        chart_types = [
            "Spending by Category",
            "Spending Over Time", 
            "Income vs Expenses",
            "Top Payees by Spending"
        ]
        
        for chart_type in chart_types:
            btn = Button(
                text=chart_type,
                size_hint=(1, None),
                height=40
            )
            btn.bind(on_press=lambda button_instance, chart_type_name=chart_type: self.set_chart_type(chart_type_name))
            popup_layout.add_widget(btn)
        
        close_btn = Button(text="Close", size_hint=(1, None), height=40)
        close_btn.bind(on_press=lambda button_instance: self.popup.dismiss())
        popup_layout.add_widget(close_btn)
        
        self.popup = Popup(
            title="Select Chart Type",
            content=popup_layout,
            size_hint=(0.8, 0.8)
        )
        self.popup.open()

    def set_chart_type(self, chart_type):
        """Set the current chart type."""
        self.chart_type = chart_type
        self.chart_type_btn.text = f"Chart Type: {chart_type}"
        self.popup.dismiss()

def create_spending_by_category_chart(transactions_df):
    """Create a pie chart showing spending by category.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    if transactions_df.empty:
        return Label(text="No transaction data available")
    
    try:
        # Filter for withdrawals (expenses)
        expenses_df = transactions_df[transactions_df['TRANSCODE'] == 'Withdrawal']
        
        if expenses_df.empty:
            return Label(text="No expense data available for the selected period")
        
        # Group by category and sum amounts
        category_spending = expenses_df.groupby('CATEGNAME')['TRANSAMOUNT'].sum().reset_index()
        
        # Sort by amount and get top categories
        category_spending = category_spending.sort_values('TRANSAMOUNT', ascending=False)
        
        # Take top 10 categories
        top_categories = category_spending.head(10)
        
        # Create figure and axis
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            top_categories['TRANSAMOUNT'],
            labels=top_categories['CATEGNAME'],
            autopct='%1.1f%%',
            shadow=True,
            startangle=90
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        
        # Set title
        ax.set_title('Spending by Category')
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except Exception as chart_creation_error:
            return Label(text=f"Error creating chart: {str(chart_creation_error)}")

def create_spending_over_time_chart(transactions_df):
    """Create a line chart showing spending over time.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    if transactions_df.empty:
        return Label(text="No transaction data available")
    
    try:
        # Convert TRANSDATE to datetime
        transactions_df['TRANSDATE'] = pd.to_datetime(transactions_df['TRANSDATE'])
        
        # Filter for withdrawals (expenses)
        expenses_df = transactions_df[transactions_df['TRANSCODE'] == 'Withdrawal']
        
        if expenses_df.empty:
            return Label(text="No expense data available for the selected period")
        
        # Group by month and sum amounts
        expenses_df['Month'] = expenses_df['TRANSDATE'].dt.to_period('M')
        monthly_spending = expenses_df.groupby('Month')['TRANSAMOUNT'].sum()
        
        # Sort by date
        monthly_spending = monthly_spending.sort_index()
        
        # Create figure and axis
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Create line chart
        ax.plot(
            [str(period) for period in monthly_spending.index],
            monthly_spending.values,
            marker='o',
            linestyle='-',
            linewidth=2,
            color='blue'
        )
        
        # Set labels and title
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount ($)')
        ax.set_title('Spending Over Time')
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except Exception as chart_creation_error:
            return Label(text=f"Error creating chart: {str(chart_creation_error)}")

def create_income_vs_expenses_chart(transactions_df):
    """Create a bar chart comparing income and expenses.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    if transactions_df.empty:
        return Label(text="No transaction data available")
    
    try:
        # Convert TRANSDATE to datetime
        transactions_df['TRANSDATE'] = pd.to_datetime(transactions_df['TRANSDATE'])
        
        # Group by month and type (income/expense)
        monthly_data = transactions_df.groupby([
            transactions_df['TRANSDATE'].dt.to_period('M'),
            'TRANSCODE'
        ])['TRANSAMOUNT'].sum().unstack(fill_value=0)
        
        # Create figure and axis
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Create bar chart
        monthly_data.plot(kind='bar', ax=ax)
        
        # Set labels and title
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount ($)')
        ax.set_title('Income vs Expenses Over Time')
        ax.legend(['Income', 'Expenses'])
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except Exception as chart_creation_error:
            return Label(text=f"Error creating chart: {str(chart_creation_error)}")

def create_top_payees_chart(transactions_df):
    """Create a bar chart showing top payees.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    if transactions_df.empty:
        return Label(text="No transaction data available")
    
    try:
        # Filter for withdrawals (expenses)
        expenses_df = transactions_df[transactions_df['TRANSCODE'] == 'Withdrawal']
        
        if expenses_df.empty:
            return Label(text="No expense data available for the selected period")
        
        # Group by payee and sum amounts
        payee_spending = expenses_df.groupby('PAYEE')['TRANSAMOUNT'].sum().reset_index()
        
        # Sort by amount and get top payees
        payee_spending = payee_spending.sort_values('TRANSAMOUNT', ascending=False)
        
        # Take top 10 payees
        top_payees = payee_spending.head(10)
        
        # Create figure and axis
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Create bar chart
        bars = ax.bar(range(len(top_payees)), top_payees['TRANSAMOUNT'])
        
        # Set labels and title
        ax.set_xlabel('Payee')
        ax.set_ylabel('Amount ($)')
        ax.set_title('Top Payees by Spending')
        
        # Set x-axis labels
        ax.set_xticks(range(len(top_payees)))
        ax.set_xticklabels(top_payees['PAYEE'], rotation=45, ha='right')
        
        # Add value labels on bars
        for bar_index, (bar_rect, transaction_amount) in enumerate(zip(bars, top_payees['TRANSAMOUNT'])):
            ax.text(bar_rect.get_x() + bar_rect.get_width()/2, bar_rect.get_height() + 0.1,
                f'${transaction_amount:,.0f}', ha='center', va='bottom')
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except Exception as e:
        return Label(text=f"Error creating chart: {str(e)}")

# Note: The original functions were duplicated multiple times in the original code.
# This version has been cleaned up to avoid duplication while maintaining functionality.