"""Visualization utilities for the MMEX Kivy application.

This module provides classes and functions for creating and displaying
financial data visualizations using Matplotlib and Kivy.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import logging

# Configure logging for visualization module
logger = logging.getLogger(__name__)

# UI color constants
BG_COLOR = (0.9, 0.9, 0.9, 1)  # Light gray background
HEADER_COLOR = (0.2, 0.6, 0.8, 1)  # Blue header
BUTTON_COLOR = (0.3, 0.5, 0.7, 1)  # Slightly darker blue for buttons
HIGHLIGHT_COLOR = (0.1, 0.7, 0.1, 1)  # Green for highlights


class VisualizationError(Exception):
    """Custom exception for visualization-related errors."""
    pass


class DataValidationError(VisualizationError):
    """Exception raised when data validation fails."""
    pass


class ChartCreationError(VisualizationError):
    """Exception raised when chart creation fails."""
    pass


def handle_chart_error(func):
    """Decorator to handle chart creation errors consistently."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DataValidationError as e:
            logger.warning(f"Data validation error in {func.__name__}: {str(e)}")
            return Label(text=f"Data validation error: {str(e)}", color=(1, 0.5, 0, 1))
        except ChartCreationError as e:
            logger.error(f"Chart creation error in {func.__name__}: {str(e)}")
            return Label(text=f"Chart creation error: {str(e)}", color=(1, 0, 0, 1))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return Label(text=f"Unexpected error: {str(e)}", color=(1, 0, 0, 1))
    return wrapper


def validate_dataframe(df, required_columns=None, min_rows=1):
    """Validate DataFrame for chart creation.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        min_rows: Minimum number of rows required
        
    Raises:
        DataValidationError: If validation fails
    """
    if df is None:
        raise DataValidationError("DataFrame is None")
    
    if df.empty:
        raise DataValidationError("No transaction data available")
    
    if len(df) < min_rows:
        raise DataValidationError(f"Insufficient data: need at least {min_rows} rows, got {len(df)}")
    
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise DataValidationError(f"Missing required columns: {missing_columns}")
    
    # Check for null values in required columns
    if required_columns:
        for col in required_columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"Column '{col}' has {null_count} null values")


def safe_numeric_conversion(series, column_name):
    """Safely convert series to numeric values while preserving row alignment.
    
    Args:
        series: Pandas series to convert
        column_name: Name of the column for error reporting
        
    Returns:
        Converted numeric series (same index as input)
        
    Raises:
        DataValidationError: If all values are non-numeric
    """
    try:
        # Convert to numeric, coercing errors to NaN, and preserve original index
        numeric_series = pd.to_numeric(series, errors='coerce')
        
        # Log non-numeric conversions
        nan_count = numeric_series.isna().sum()
        if nan_count > 0:
            logger.warning(
                f"Column '{column_name}' has {nan_count} non-numeric values converted to NaN"
            )
        
        # If all values are NaN after conversion, raise a validation error
        if numeric_series.notna().sum() == 0:
            raise DataValidationError(f"No valid numeric data in column '{column_name}'")
        
        return numeric_series
    except Exception as e:
        raise DataValidationError(
            f"Failed to convert column '{column_name}' to numeric: {str(e)}"
        )


def optimize_chart_data(df, max_categories=10, min_amount_threshold=0.01):
    """Optimize data for chart display by limiting categories and filtering small amounts.
    
    Args:
        df: DataFrame to optimize
        max_categories: Maximum number of categories to display
        min_amount_threshold: Minimum amount threshold (as percentage of total)
        
    Returns:
        Optimized DataFrame
    """
    if df.empty:
        return df
    
    # Calculate total amount for threshold calculation
    total_amount = df['TRANSAMOUNT'].sum()
    min_amount = total_amount * min_amount_threshold
    
    # Filter out very small amounts
    filtered_df = df[df['TRANSAMOUNT'] >= min_amount]
    
    # If we still have too many categories, keep only the top ones
    if len(filtered_df) > max_categories:
        filtered_df = filtered_df.head(max_categories)
        
        # Add "Others" category for remaining amounts
        remaining_amount = df[~df.index.isin(filtered_df.index)]['TRANSAMOUNT'].sum()
        if remaining_amount > 0:
            others_row = pd.DataFrame({
                'CATEGNAME': ['Others'],
                'TRANSAMOUNT': [remaining_amount]
            })
            filtered_df = pd.concat([filtered_df, others_row], ignore_index=True)
    
    return filtered_df


class VisualizationTab(BoxLayout):
    """A tab for displaying financial data visualizations."""
    
    def __init__(self, **kwargs):
        super(VisualizationTab, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        self.chart_type = "Spending by Category"  # Default chart type
        self.parent_app = None  # Will be set by parent
        self.current_transactions_df = None  # Cache current data
        
        # Chart type selection layout
        self.selection_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        
        # Chart type button
        self.chart_type_btn = Button(
            text=f"Chart Type: {self.chart_type}",
            size_hint=(0.6, 1),
            background_color=BUTTON_COLOR
        )
        self.chart_type_btn.bind(on_release=self.show_chart_options)
        self.selection_layout.add_widget(self.chart_type_btn)
        
        # Refresh button
        self.refresh_btn = Button(
            text="Refresh Chart",
            size_hint=(0.2, 1),
            background_color=HIGHLIGHT_COLOR
        )
        self.refresh_btn.bind(on_release=self.refresh_chart)
        self.selection_layout.add_widget(self.refresh_btn)
        
        # Loading indicator (initially hidden)
        self.loading_label = Label(
            text="Loading...",
            size_hint=(0.2, 1),
            color=(0.5, 0.5, 0.5, 1)
        )
        # Don't add loading label initially
        
        # Add selection layout to main layout
        self.add_widget(self.selection_layout)
        
        # Chart display area with better styling
        self.chart_layout = BoxLayout(
            orientation='vertical', 
            size_hint=(1, 0.9),
            padding=5
        )
        
        # Welcome message with better styling
        self.info_label = Label(
            text="📊 Select a chart type to visualize your financial data\n\n"
                 "Available charts:\n"
                 "• Spending by Category - Pie chart of expense categories\n"
                 "• Spending Over Time - Line chart showing trends\n"
                 "• Income vs Expenses - Monthly comparison\n"
                 "• Top Payees - Bar chart of highest spending\n"
                 "• Asset Distribution - Pie chart of assets by account\n"
                 "• Monthly Budget Comparison - Compare spending to budget\n"
                 "• Transaction Frequency - Activity by day of week\n"
                 "• Cash Flow Analysis - Net cash flow over time",
            size_hint=(1, 1),
            text_size=(None, None),
            halign='center',
            valign='middle',
            color=(0.3, 0.3, 0.3, 1)
        )
        self.chart_layout.add_widget(self.info_label)
        self.add_widget(self.chart_layout)
    
    def set_parent_app(self, app):
        """Set the parent application reference."""
        self.parent_app = app
    
    def show_loading(self):
        """Show loading indicator."""
        # Replace refresh button with loading indicator
        if self.refresh_btn in self.selection_layout.children:
            self.selection_layout.remove_widget(self.refresh_btn)
            self.selection_layout.add_widget(self.loading_label)
    
    def hide_loading(self):
        """Hide loading indicator."""
        # Replace loading indicator with refresh button
        if self.loading_label in self.selection_layout.children:
            self.selection_layout.remove_widget(self.loading_label)
            self.selection_layout.add_widget(self.refresh_btn)
    
    def show_chart_error(self, error_msg):
        """Display an error message in the chart area with better styling."""
        error_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Error icon and title
        error_title = Label(
            text="⚠️ Chart Generation Error",
            size_hint=(1, 0.3),
            color=(1, 0.3, 0.3, 1),
            font_size='18sp'
        )
        error_layout.add_widget(error_title)
        
        # Error message
        error_label = Label(
            text=error_msg,
            size_hint=(1, 0.5),
            color=(0.8, 0.2, 0.2, 1),
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        error_layout.add_widget(error_label)
        
        # Suggestion
        suggestion_label = Label(
            text="💡 Try selecting different data or check if transactions are available",
            size_hint=(1, 0.2),
            color=(0.5, 0.5, 0.5, 1),
            font_size='14sp'
        )
        error_layout.add_widget(suggestion_label)
        
        self.chart_layout.clear_widgets()
        self.chart_layout.add_widget(error_layout)
        self.hide_loading()
    
    def refresh_chart(self, instance=None):
        """Refresh the current chart with cached data."""
        if self.current_transactions_df is not None:
            self.update_chart(self.current_transactions_df)
        else:
            self.show_chart_error("No data available to refresh. Please load some transactions first.")
    
    def update_chart(self, transactions_df):
        """Update the chart with new transaction data."""
        try:
            # Show loading indicator
            self.show_loading()
            
            # Cache the data for refresh functionality
            self.current_transactions_df = transactions_df
            
            chart_functions = {
                "Spending by Category": create_spending_by_category_chart,
                "Spending Over Time": create_spending_over_time_chart,
                "Income vs Expenses": create_income_vs_expenses_chart,
                "Top Payees by Spending": create_top_payees_chart,
                "Asset Distribution": create_asset_distribution_chart,
                "Monthly Budget Comparison": create_monthly_budget_comparison_chart,
                "Transaction Frequency": create_transaction_frequency_chart,
                "Cash Flow Analysis": create_cashflow_chart
            }
            
            chart_function = chart_functions.get(self.chart_type, create_spending_by_category_chart)
            chart = chart_function(transactions_df)
            
            self.chart_layout.clear_widgets()
            self.chart_layout.add_widget(chart)
            
            # Hide loading indicator
            self.hide_loading()
            
        except Exception as chart_error:
            logger.error(f"Error updating chart: {str(chart_error)}")
            self.show_chart_error(f"Error generating chart: {str(chart_error)}")

    def show_chart(self, transactions_df):
        """Display the current chart with transaction data."""
        self.update_chart(transactions_df)

    def show_chart_options(self, instance):
        """Show chart options in a popup with improved styling."""
        try:
            popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
            
            # Title
            title_label = Label(
                text="📊 Select Chart Type",
                size_hint=(1, 0.15),
                font_size='18sp',
                color=HEADER_COLOR
            )
            popup_layout.add_widget(title_label)
            
            chart_types = [
                ("Spending by Category", "🥧 Pie chart showing expense distribution"),
                ("Spending Over Time", "📈 Line chart showing spending trends"),
                ("Income vs Expenses", "📊 Monthly income and expense comparison"),
                ("Top Payees by Spending", "🏪 Bar chart of highest spending payees"),
                ("Asset Distribution", "💰 Pie chart showing asset distribution by account"),
                ("Monthly Budget Comparison", "📋 Compare monthly spending to budget"),
                ("Transaction Frequency", "📅 Transaction activity by day of week"),
                ("Cash Flow Analysis", "💸 Net cash flow analysis over time")
            ]
            
            for chart_type, description in chart_types:
                # Create a layout for each option
                option_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=80, spacing=5)
                
                btn = Button(
                    text=chart_type,
                    size_hint=(1, 0.6),
                    background_color=BUTTON_COLOR if chart_type != self.chart_type else HIGHLIGHT_COLOR
                )
                btn.bind(on_press=lambda button_instance, chart_type_name=chart_type: self.set_chart_type(chart_type_name))
                
                desc_label = Label(
                    text=description,
                    size_hint=(1, 0.4),
                    font_size='12sp',
                    color=(0.5, 0.5, 0.5, 1)
                )
                
                option_layout.add_widget(btn)
                option_layout.add_widget(desc_label)
                popup_layout.add_widget(option_layout)
            
            # Close button
            close_btn = Button(
                text="Close",
                size_hint=(1, 0.1),
                background_color=(0.7, 0.3, 0.3, 1)
            )
            close_btn.bind(on_press=lambda button_instance: self.popup.dismiss())
            popup_layout.add_widget(close_btn)
            
            self.popup = Popup(
                title="Chart Selection",
                content=popup_layout,
                size_hint=(0.9, 0.8),
                background_color=BG_COLOR
            )
            self.popup.open()
            
        except Exception as e:
            logger.error(f"Error showing chart options: {str(e)}")
            self.show_chart_error(f"Error showing chart options: {str(e)}")

    def set_chart_type(self, chart_type):
        """Set the current chart type and refresh if data is available."""
        try:
            self.chart_type = chart_type
            self.chart_type_btn.text = f"Chart Type: {chart_type}"
            self.popup.dismiss()
            
            # Auto-refresh chart if we have data
            if self.current_transactions_df is not None:
                self.update_chart(self.current_transactions_df)
                
        except Exception as e:
            logger.error(f"Error setting chart type: {str(e)}")


@handle_chart_error
def create_spending_by_category_chart(transactions_df):
    """Create a pie chart showing spending by category.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    validate_dataframe(transactions_df, ['TRANSCODE', 'CATEGNAME', 'TRANSAMOUNT'], min_rows=1)
    
    # Filter for withdrawals (expenses)
    expenses_df = transactions_df[transactions_df['TRANSCODE'] == 'Withdrawal'].copy()
    
    if expenses_df.empty:
        raise DataValidationError("No expense data available for the selected period")
    
    # Safely convert amounts to numeric
    expenses_df['TRANSAMOUNT'] = safe_numeric_conversion(expenses_df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Group by category and sum amounts
    category_spending = expenses_df.groupby('CATEGNAME')['TRANSAMOUNT'].sum().reset_index()
    
    if category_spending.empty:
        raise DataValidationError("No category spending data available")
    
    # Sort by amount and optimize data
    category_spending = category_spending.sort_values('TRANSAMOUNT', ascending=False)
    category_spending = optimize_chart_data(category_spending, max_categories=8)
    
    try:
        # Create figure with better layout
        fig = Figure(figsize=(12, 8), dpi=100)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        
        # Create pie chart with improved styling
        colors = plt.cm.Set3(range(len(category_spending)))
        wedges, texts, autotexts = ax.pie(
            category_spending['TRANSAMOUNT'],
            labels=category_spending['CATEGNAME'],
            autopct=lambda pct: f'${category_spending["TRANSAMOUNT"].sum() * pct / 100:,.0f}\n({pct:.1f}%)',
            colors=colors,
            shadow=True,
            startangle=90,
            explode=[0.05 if i == 0 else 0 for i in range(len(category_spending))]  # Explode largest slice
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        
        # Set title with total amount
        total_amount = category_spending['TRANSAMOUNT'].sum()
        ax.set_title(f'Spending by Category\nTotal: ${total_amount:,.2f}', fontsize=14, fontweight='bold')
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        
        for text in texts:
            text.set_fontsize(10)
        
        # Adjust layout to prevent label cutoff
        fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except Exception as e:
        raise ChartCreationError(f"Failed to create spending by category chart: {str(e)}")


@handle_chart_error
def create_spending_over_time_chart(transactions_df):
    """Create a line chart showing spending over time.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    validate_dataframe(transactions_df, ['TRANSDATE', 'TRANSCODE', 'TRANSAMOUNT'], min_rows=2)
    
    try:
        # Create a copy to avoid modifying original data
        df_copy = transactions_df.copy()
        
        # Convert TRANSDATE to datetime with error handling
        try:
            df_copy['TRANSDATE'] = pd.to_datetime(df_copy['TRANSDATE'])
        except Exception as e:
            raise DataValidationError(f"Failed to parse transaction dates: {str(e)}")
        
        # Filter for withdrawals (expenses)
        expenses_df = df_copy[df_copy['TRANSCODE'] == 'Withdrawal'].copy()
        
        if expenses_df.empty:
            raise DataValidationError("No expense data available for the selected period")
        
        # Safely convert amounts to numeric
        expenses_df['TRANSAMOUNT'] = safe_numeric_conversion(expenses_df['TRANSAMOUNT'], 'TRANSAMOUNT')
        
        # Group by month and sum amounts
        expenses_df['Month'] = expenses_df['TRANSDATE'].dt.to_period('M')
        monthly_spending = expenses_df.groupby('Month')['TRANSAMOUNT'].sum()
        
        if monthly_spending.empty:
            raise DataValidationError("No monthly spending data available")
        
        # Sort by date and fill missing months if needed
        monthly_spending = monthly_spending.sort_index()
        
        # If we have a large date range, consider resampling
        if len(monthly_spending) > 24:  # More than 2 years of data
            logger.info("Large dataset detected, showing last 24 months")
            monthly_spending = monthly_spending.tail(24)
        
        # Create figure with better layout
        fig = Figure(figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        
        # Create line chart with improved styling
        dates = [str(period) for period in monthly_spending.index]
        values = monthly_spending.values
        
        ax.plot(dates, values, marker='o', linestyle='-', linewidth=2.5, 
                markersize=6, color='#2E86AB', markerfacecolor='#A23B72')
        
        # Add trend line if we have enough data points
        if len(values) >= 3:
            z = np.polyfit(range(len(values)), values, 1)
            p = np.poly1d(z)
            ax.plot(dates, p(range(len(values))), "--", alpha=0.7, color='red', 
                   label=f'Trend: {"↗" if z[0] > 0 else "↘"}')
            ax.legend()
        
        # Set labels and title
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Amount ($)', fontsize=12)
        ax.set_title('Spending Over Time', fontsize=14, fontweight='bold')
        
        # Format y-axis to show currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Adjust layout
        fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except DataValidationError:
        raise
    except Exception as e:
        raise ChartCreationError(f"Failed to create spending over time chart: {str(e)}")


@handle_chart_error
def create_income_vs_expenses_chart(transactions_df):
    """Create a bar chart comparing income and expenses.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    validate_dataframe(transactions_df, ['TRANSDATE', 'TRANSCODE', 'TRANSAMOUNT'])
    
    try:
        # Convert TRANSDATE to datetime
        transactions_df = transactions_df.copy()
        transactions_df['TRANSDATE'] = pd.to_datetime(transactions_df['TRANSDATE'])
        
        # Group by month and type (income/expense)
        monthly_data = transactions_df.groupby([
            transactions_df['TRANSDATE'].dt.to_period('M'),
            'TRANSCODE'
        ])['TRANSAMOUNT'].sum().unstack(fill_value=0)
        
        if monthly_data.empty:
            raise DataValidationError("No monthly transaction data available")
        
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
        
    except DataValidationError:
        raise
    except Exception as e:
        raise ChartCreationError(f"Failed to create income vs expenses chart: {str(e)}")


@handle_chart_error
def create_top_payees_chart(transactions_df):
    """Create a bar chart showing top payees.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    validate_dataframe(transactions_df, ['TRANSCODE', 'PAYEE', 'TRANSAMOUNT'])
    
    # Filter for withdrawals (expenses)
    expenses_df = transactions_df[transactions_df['TRANSCODE'] == 'Withdrawal']
    
    if expenses_df.empty:
        raise DataValidationError("No expense data available for the selected period")
    
    # Group by payee and sum amounts
    payee_spending = expenses_df.groupby('PAYEE')['TRANSAMOUNT'].sum().reset_index()
    
    if payee_spending.empty:
        raise DataValidationError("No payee spending data available")
    
    # Sort by amount and get top payees
    payee_spending = payee_spending.sort_values('TRANSAMOUNT', ascending=False)
    
    # Take top 10 payees
    top_payees = payee_spending.head(10)
    
    try:
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
            ax.text(
                bar_rect.get_x() + bar_rect.get_width() / 2, 
                bar_rect.get_height() + 0.1,
                f'${transaction_amount:,.0f}', 
                ha='center', 
                va='bottom'
            )
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except Exception as e:
        raise ChartCreationError(f"Failed to create top payees chart: {str(e)}")


@handle_chart_error
def create_asset_distribution_chart(transactions_df):
    """Create a pie chart showing asset distribution by account.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    validate_dataframe(transactions_df, ['ACCOUNTNAME', 'TRANSAMOUNT'], min_rows=1)
    
    try:
        # Create a copy to avoid modifying original data
        df_copy = transactions_df.copy()
        
        # Safely convert amounts to numeric
        df_copy['TRANSAMOUNT'] = safe_numeric_conversion(df_copy['TRANSAMOUNT'], 'TRANSAMOUNT')
        
        # Group by account and sum amounts (positive values represent assets)
        account_balances = df_copy.groupby('ACCOUNTNAME')['TRANSAMOUNT'].sum().reset_index()
        
        # Filter for positive balances (assets)
        assets_df = account_balances[account_balances['TRANSAMOUNT'] > 0]
        
        if assets_df.empty:
            raise DataValidationError("No asset data available")
        
        # Sort by amount
        assets_df = assets_df.sort_values('TRANSAMOUNT', ascending=False)
        
        # Create figure with better layout
        fig = Figure(figsize=(12, 8), dpi=100)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        
        # Create pie chart with improved styling
        colors = plt.cm.Pastel1(range(len(assets_df)))
        wedges, texts, autotexts = ax.pie(
            assets_df['TRANSAMOUNT'],
            labels=assets_df['ACCOUNTNAME'],
            autopct=lambda pct: f'${assets_df["TRANSAMOUNT"].sum() * pct / 100:,.0f}\n({pct:.1f}%)',
            colors=colors,
            shadow=True,
            startangle=45
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        
        # Set title with total amount
        total_assets = assets_df['TRANSAMOUNT'].sum()
        ax.set_title(f'Asset Distribution by Account\nTotal Assets: ${total_assets:,.2f}', 
                    fontsize=14, fontweight='bold')
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        
        for text in texts:
            text.set_fontsize(10)
        
        # Adjust layout to prevent label cutoff
        fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except DataValidationError:
        raise
    except Exception as e:
        raise ChartCreationError(f"Failed to create asset distribution chart: {str(e)}")


@handle_chart_error
def create_monthly_budget_comparison_chart(transactions_df, budget_amount=None):
    """Create a bar chart comparing monthly spending to budget.
    
    Args:
        transactions_df: DataFrame containing transaction data
        budget_amount: Optional budget amount for comparison
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    validate_dataframe(transactions_df, ['TRANSDATE', 'TRANSCODE', 'TRANSAMOUNT'], min_rows=1)
    
    try:
        # Create a copy to avoid modifying original data
        df_copy = transactions_df.copy()
        
        # Convert TRANSDATE to datetime
        df_copy['TRANSDATE'] = pd.to_datetime(df_copy['TRANSDATE'])
        
        # Filter for withdrawals (expenses)
        expenses_df = df_copy[df_copy['TRANSCODE'] == 'Withdrawal'].copy()
        
        if expenses_df.empty:
            raise DataValidationError("No expense data available for budget comparison")
        
        # Safely convert amounts to numeric
        expenses_df['TRANSAMOUNT'] = safe_numeric_conversion(expenses_df['TRANSAMOUNT'], 'TRANSAMOUNT')
        
        # Group by month and sum amounts
        expenses_df['Month'] = expenses_df['TRANSDATE'].dt.to_period('M')
        monthly_spending = expenses_df.groupby('Month')['TRANSAMOUNT'].sum()
        
        if monthly_spending.empty:
            raise DataValidationError("No monthly spending data available")
        
        # Sort by date
        monthly_spending = monthly_spending.sort_index()
        
        # If no budget provided, use average spending as budget
        if budget_amount is None:
            budget_amount = monthly_spending.mean()
        
        # Create figure with better layout
        fig = Figure(figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        
        # Create bar chart
        dates = [str(period) for period in monthly_spending.index]
        values = monthly_spending.values
        
        # Color bars based on budget comparison
        colors = ['red' if val > budget_amount else 'green' for val in values]
        bars = ax.bar(dates, values, color=colors, alpha=0.7)
        
        # Add budget line
        ax.axhline(y=budget_amount, color='blue', linestyle='--', linewidth=2, 
                  label=f'Budget: ${budget_amount:,.0f}')
        
        # Set labels and title
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Amount ($)', fontsize=12)
        ax.set_title('Monthly Spending vs Budget', fontsize=14, fontweight='bold')
        
        # Format y-axis to show currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add legend
        ax.legend()
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + budget_amount * 0.01,
                   f'${value:,.0f}', ha='center', va='bottom', fontsize=8)
        
        # Adjust layout
        fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except DataValidationError:
        raise
    except Exception as e:
        raise ChartCreationError(f"Failed to create monthly budget comparison chart: {str(e)}")


@handle_chart_error
def create_transaction_frequency_chart(transactions_df):
    """Create a bar chart showing transaction frequency by day of week.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    validate_dataframe(transactions_df, ['TRANSDATE'], min_rows=1)
    
    try:
        # Create a copy to avoid modifying original data
        df_copy = transactions_df.copy()
        
        # Convert TRANSDATE to datetime
        df_copy['TRANSDATE'] = pd.to_datetime(df_copy['TRANSDATE'])
        
        # Extract day of week
        df_copy['DayOfWeek'] = df_copy['TRANSDATE'].dt.day_name()
        
        # Count transactions by day of week
        day_counts = df_copy['DayOfWeek'].value_counts()
        
        # Reorder by weekday
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = day_counts.reindex(weekday_order, fill_value=0)
        
        if day_counts.empty or day_counts.sum() == 0:
            raise DataValidationError("No transaction frequency data available")
        
        # Create figure with better layout
        fig = Figure(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        
        # Create bar chart with gradient colors
        colors = plt.cm.viridis(np.linspace(0, 1, len(day_counts)))
        bars = ax.bar(day_counts.index, day_counts.values, color=colors, alpha=0.8)
        
        # Set labels and title
        ax.set_xlabel('Day of Week', fontsize=12)
        ax.set_ylabel('Number of Transactions', fontsize=12)
        ax.set_title('Transaction Frequency by Day of Week', fontsize=14, fontweight='bold')
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, value in zip(bars, day_counts.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{int(value)}', ha='center', va='bottom', fontsize=10)
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3, axis='y')
        
        # Adjust layout
        fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except DataValidationError:
        raise
    except Exception as e:
        raise ChartCreationError(f"Failed to create transaction frequency chart: {str(e)}")


@handle_chart_error
def create_cashflow_chart(transactions_df):
    """Create a line chart showing cash flow over time.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        A FigureCanvasKivyAgg widget containing the chart
    """
    validate_dataframe(transactions_df, ['TRANSDATE', 'TRANSCODE', 'TRANSAMOUNT'], min_rows=2)
    
    try:
        # Create a copy to avoid modifying original data
        df_copy = transactions_df.copy()
        
        # Convert TRANSDATE to datetime
        df_copy['TRANSDATE'] = pd.to_datetime(df_copy['TRANSDATE'])
        
        # Safely convert amounts to numeric
        df_copy['TRANSAMOUNT'] = safe_numeric_conversion(df_copy['TRANSAMOUNT'], 'TRANSAMOUNT')
        
        # Separate income and expenses
        income_df = df_copy[df_copy['TRANSCODE'] == 'Deposit'].copy()
        expense_df = df_copy[df_copy['TRANSCODE'] == 'Withdrawal'].copy()
        
        # Group by month
        if not income_df.empty:
            income_df['Month'] = income_df['TRANSDATE'].dt.to_period('M')
            monthly_income = income_df.groupby('Month')['TRANSAMOUNT'].sum()
        else:
            monthly_income = pd.Series(dtype=float)
        
        if not expense_df.empty:
            expense_df['Month'] = expense_df['TRANSDATE'].dt.to_period('M')
            monthly_expenses = expense_df.groupby('Month')['TRANSAMOUNT'].sum()
        else:
            monthly_expenses = pd.Series(dtype=float)
        
        # Combine and calculate net cash flow
        all_months = pd.Index(list(monthly_income.index) + list(monthly_expenses.index)).unique()
        monthly_income = monthly_income.reindex(all_months, fill_value=0)
        monthly_expenses = monthly_expenses.reindex(all_months, fill_value=0)
        
        net_cashflow = monthly_income - monthly_expenses
        
        if net_cashflow.empty:
            raise DataValidationError("No cash flow data available")
        
        # Sort by date
        net_cashflow = net_cashflow.sort_index()
        
        # Create figure with better layout
        fig = Figure(figsize=(12, 6), dpi=100)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        
        # Create line chart
        dates = [str(period) for period in net_cashflow.index]
        values = net_cashflow.values
        
        # Color line based on positive/negative values
        ax.plot(dates, values, marker='o', linestyle='-', linewidth=2.5, markersize=6)
        
        # Fill areas above and below zero
        ax.fill_between(dates, values, 0, where=(values >= 0), color='green', alpha=0.3, label='Positive Cash Flow')
        ax.fill_between(dates, values, 0, where=(values < 0), color='red', alpha=0.3, label='Negative Cash Flow')
        
        # Add zero line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        # Set labels and title
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Net Cash Flow ($)', fontsize=12)
        ax.set_title('Monthly Cash Flow Analysis', fontsize=14, fontweight='bold')
        
        # Format y-axis to show currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Add legend
        ax.legend()
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Adjust layout
        fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasKivyAgg(fig)
        return canvas
        
    except DataValidationError:
        raise
    except Exception as e:
        raise ChartCreationError(f"Failed to create cash flow chart: {str(e)}")