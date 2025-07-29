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
    
    def show_chart_options(self, instance):
        """Show a popup with chart type options."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Chart options
        options = [
            "Spending by Category",
            "Spending Over Time",
            "Income vs Expenses",
            "Top Payees"
        ]
        
        for option in options:
            btn = Button(text=option, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn, opt=option: self.select_chart_option(opt, popup))
            content.add_widget(btn)
        
        # Cancel button
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40)
        cancel_btn.bind(on_release=lambda x: popup.dismiss())
        content.add_widget(cancel_btn)
        
        popup = Popup(title="Select Chart Type", content=content, size_hint=(0.8, 0.8))
        popup.open()
    
    def select_chart_option(self, option, popup):
        """Select a chart type and update the display."""
        self.chart_type = option
        self.chart_type_btn.text = f"Chart Type: {option}"
        popup.dismiss()
        
        # Notify parent to update the chart
        if self.parent_app:
            self.parent_app.update_visualization()
    
    def update_chart(self, transactions_df):
        """Update the chart based on the selected chart type.
        
        Args:
            transactions_df: DataFrame containing transaction data
        """
        # Clear existing chart
        self.chart_layout.clear_widgets()
        
        # Create chart based on selected type
        if self.chart_type == "Spending by Category":
            chart = create_category_spending_chart(transactions_df)
            self.chart_layout.add_widget(chart)
        
        elif self.chart_type == "Spending Over Time":
            chart = create_spending_over_time_chart(transactions_df)
            self.chart_layout.add_widget(chart)
        
        elif self.chart_type == "Income vs Expenses":
            chart = create_income_vs_expenses_chart(transactions_df)
            self.chart_layout.add_widget(chart)
        
        elif self.chart_type == "Top Payees":
            chart = create_top_payees_chart(transactions_df)
            self.chart_layout.add_widget(chart)

def create_category_spending_chart(transactions_df):
    """Create a pie chart showing spending by category.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    if transactions_df.empty:
        return Label(text="No transaction data available")
    
    # Filter for withdrawals (expenses)
    expenses_df = transactions_df[transactions_df['TRANSCODE'] == 'Withdrawal']
    
    if expenses_df.empty:
        return Label(text="No expense data available for the selected period")
    
    # Group by category and sum amounts
    category_spending = expenses_df.groupby('CATEGNAME')['TRANSAMOUNT'].sum().reset_index()
    
    # Sort by amount and get top categories
    category_spending = category_spending.sort_values('TRANSAMOUNT', ascending=False)
    
    # If there are too many categories, group smaller ones as "Other"
    top_n = 7  # Show top 7 categories
    if len(category_spending) > top_n:
        top_categories = category_spending.head(top_n)
        other_sum = category_spending.iloc[top_n:]['TRANSAMOUNT'].sum()
        
        # Add "Other" category
        other_row = pd.DataFrame({'CATEGNAME': ['Other'], 'TRANSAMOUNT': [other_sum]})
        category_spending = pd.concat([top_categories, other_row], ignore_index=True)
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        category_spending['TRANSAMOUNT'],
        labels=category_spending['CATEGNAME'],
        autopct='%1.1f%%',
        startangle=90,
        shadow=True
    )
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')
    
    # Set title
    ax.set_title('Spending by Category')
    
    # Create canvas
    canvas = FigureCanvasKivyAgg(fig)
    return canvas

def create_spending_over_time_chart(transactions_df):
    """Create a line chart showing spending over time.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    if transactions_df.empty:
        return Label(text="No transaction data available")
    
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
        linewidth=2
    )
    
    # Set labels and title
    ax.set_xlabel('Month')
    ax.set_ylabel('Amount')
    ax.set_title('Spending Over Time')
    
    # Rotate x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Adjust layout
    fig.tight_layout()
    
    # Create canvas
    canvas = FigureCanvasKivyAgg(fig)
    return canvas

def create_income_vs_expenses_chart(transactions_df):
    """Create a bar chart comparing income vs expenses.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    if transactions_df.empty:
        return Label(text="No transaction data available")
    
    # Convert TRANSDATE to datetime
    transactions_df['TRANSDATE'] = pd.to_datetime(transactions_df['TRANSDATE'])
    
    # Add month column
    transactions_df['Month'] = transactions_df['TRANSDATE'].dt.to_period('M')
    
    # Group by month and transaction type, then sum amounts
    income_df = transactions_df[transactions_df['TRANSCODE'] == 'Deposit']
    expenses_df = transactions_df[transactions_df['TRANSCODE'] == 'Withdrawal']
    
    if income_df.empty and expenses_df.empty:
        return Label(text="No income or expense data available for the selected period")
    
    monthly_income = income_df.groupby('Month')['TRANSAMOUNT'].sum()
    monthly_expenses = expenses_df.groupby('Month')['TRANSAMOUNT'].sum()
    
    # Combine into a single DataFrame
    monthly_data = pd.DataFrame({
        'Income': monthly_income,
        'Expenses': monthly_expenses
    }).fillna(0)
    
    # Sort by date
    monthly_data = monthly_data.sort_index()
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create bar chart
    x = range(len(monthly_data))
    width = 0.35
    
    ax.bar(
        [i - width/2 for i in x],
        monthly_data['Income'],
        width,
        label='Income',
        color='green'
    )
    ax.bar(
        [i + width/2 for i in x],
        monthly_data['Expenses'],
        width,
        label='Expenses',
        color='red'
    )
    
    # Set labels and title
    ax.set_xlabel('Month')
    ax.set_ylabel('Amount')
    ax.set_title('Income vs Expenses')
    ax.set_xticks(x)
    ax.set_xticklabels([str(period) for period in monthly_data.index])
    ax.legend()
    
    # Rotate x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Adjust layout
    fig.tight_layout()
    
    # Create canvas
    canvas = FigureCanvasKivyAgg(fig)
    return canvas

def create_top_payees_chart(transactions_df):
    """Create a horizontal bar chart showing top payees by spending.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    if transactions_df.empty:
        return Label(text="No transaction data available")
    
    # Filter for withdrawals (expenses)
    expenses_df = transactions_df[transactions_df['TRANSCODE'] == 'Withdrawal']
    
    if expenses_df.empty:
        return Label(text="No expense data available for the selected period")
    
    # Group by payee and sum amounts
    payee_spending = expenses_df.groupby('PAYEENAME')['TRANSAMOUNT'].sum().reset_index()
    
    # Sort by amount and get top payees
    payee_spending = payee_spending.sort_values('TRANSAMOUNT', ascending=False)
    
    # Take top 10 payees
    top_payees = payee_spending.head(10)
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create horizontal bar chart
    ax.barh(
        top_payees['PAYEENAME'],
        top_payees['TRANSAMOUNT'],
        color='blue'
    )
    
    # Set labels and title
    ax.set_xlabel('Amount')
    ax.set_ylabel('Payee')
    ax.set_title('Top Payees by Spending')
    
    # Invert y-axis to show highest spending at the top
    ax.invert_yaxis()
    
    # Adjust layout
    fig.tight_layout()
    
    # Create canvas
    canvas = FigureCanvasKivyAgg(fig)
    return canvas