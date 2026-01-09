"""
Visualization charts for the MMEX Kivy application.

This module provides functions for creating various types of financial data visualizations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import logging
from typing import Dict, Any, Optional

from visualization_utils_new import (
    handle_chart_error, validate_dataframe, safe_numeric_conversion, 
    optimize_chart_data, apply_intelligent_sampling
)
from visualization_errors_new import VisualizationError, DataValidationError, ChartCreationError

# Configure logging for visualization module
logger = logging.getLogger(__name__)


@handle_chart_error
def create_spending_by_category_chart(transactions_df):
    """
    Create a pie chart showing spending by category.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating spending by category chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['CATEGNAME', 'TRANSAMOUNT'])
    
    # Filter for expenses (negative amounts)
    expenses_df = transactions_df[transactions_df['TRANSAMOUNT'] < 0].copy()
    
    if expenses_df.empty:
        raise DataValidationError("No expense transactions found")
    
    # Convert TRANSAMOUNT to numeric
    expenses_df['TRANSAMOUNT'] = safe_numeric_conversion(expenses_df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Group by category and sum amounts (using absolute values for positive display)
    category_spending = expenses_df.groupby('CATEGNAME')['TRANSAMOUNT'].sum().abs()
    
    # Optimize data for charting
    category_spending = optimize_chart_data(
        pd.DataFrame({'CATEGORY': category_spending.index, 'TRANSAMOUNT': category_spending.values}),
        max_categories=8
    ).groupby('CATEGORY')['TRANSAMOUNT'].sum()
    
    # Create figure and axis
    fig = Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        category_spending.values,
        labels=category_spending.index,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 8}
    )
    
    # Improve readability
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('Spending by Category', fontsize=14, pad=20)
    
    # Add legend with values
    legend_labels = [f'{cat}: ${amt:.2f}' for cat, amt in zip(category_spending.index, category_spending.values)]
    ax.legend(wedges, legend_labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    # Adjust layout to prevent clipping
    fig.tight_layout()
    
    logger.debug("Spending by category chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_spending_over_time_chart(transactions_df):
    """
    Create a line chart showing spending over time.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating spending over time chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['TRANSDATE', 'TRANSAMOUNT'])
    
    # Make a copy to avoid modifying original
    df = transactions_df.copy()
    
    # Convert date column to datetime
    df['TRANSDATE'] = pd.to_datetime(df['TRANSDATE'])
    
    # Convert amount to numeric
    df['TRANSAMOUNT'] = safe_numeric_conversion(df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Filter for expenses
    expenses_df = df[df['TRANSAMOUNT'] < 0].copy()
    
    if expenses_df.empty:
        raise DataValidationError("No expense transactions found")
    
    # Group by date and sum expenses (using absolute values)
    daily_spending = expenses_df.groupby('TRANSDATE')['TRANSAMOUNT'].sum().abs().resample('D').sum()
    
    # Optimize data for charting
    if len(daily_spending) > 100:  # If too many data points, resample to weekly
        daily_spending = daily_spending.resample('W').sum()
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create line chart
    ax.plot(daily_spending.index, daily_spending.values, marker='o', linestyle='-', linewidth=2, markersize=4)
    
    # Format the plot
    ax.set_title('Spending Over Time', fontsize=14)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Spending Amount ($)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # Rotate x-axis labels for better readability
    fig.autofmt_xdate()
    
    logger.debug("Spending over time chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_income_vs_expenses_chart(transactions_df):
    """
    Create a bar chart comparing income vs expenses over time.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating income vs expenses chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['TRANSDATE', 'TRANSAMOUNT'])
    
    # Make a copy to avoid modifying original
    df = transactions_df.copy()
    
    # Convert date column to datetime
    df['TRANSDATE'] = pd.to_datetime(df['TRANSDATE'])
    
    # Convert amount to numeric
    df['TRANSAMOUNT'] = safe_numeric_conversion(df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Separate income and expenses
    income_df = df[df['TRANSAMOUNT'] > 0].copy()
    expenses_df = df[df['TRANSAMOUNT'] < 0].copy()
    
    # Group by month for both income and expenses
    monthly_income = income_df.groupby(df['TRANSDATE'].dt.to_period('M'))['TRANSAMOUNT'].sum()
    monthly_expenses = expenses_df.groupby(df['TRANSDATE'].dt.to_period('M'))['TRANSAMOUNT'].sum().abs()  # Absolute value for expenses
    
    # Combine into a single DataFrame
    comparison_df = pd.DataFrame({
        'Income': monthly_income,
        'Expenses': monthly_expenses
    }).fillna(0)
    
    # Optimize data for charting
    comparison_df = optimize_chart_data(comparison_df, max_data_points=12)  # Limit to 12 months
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create bar chart
    x = range(len(comparison_df))
    width = 0.35
    
    ax.bar([i - width/2 for i in x], comparison_df['Income'], width, label='Income', alpha=0.8)
    ax.bar([i + width/2 for i in x], comparison_df['Expenses'], width, label='Expenses', alpha=0.8)
    
    # Format the plot
    ax.set_title('Income vs Expenses by Month', fontsize=14)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Amount ($)', fontsize=12)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Set x-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels([str(period) for period in comparison_df.index], rotation=45, ha='right')
    
    logger.debug("Income vs expenses chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_top_payees_chart(transactions_df):
    """
    Create a horizontal bar chart showing top payees by spending.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating top payees chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['PAYEENAME', 'TRANSAMOUNT'])
    
    # Filter for expenses (negative amounts)
    expenses_df = transactions_df[transactions_df['TRANSAMOUNT'] < 0].copy()
    
    if expenses_df.empty:
        raise DataValidationError("No expense transactions found")
    
    # Convert TRANSAMOUNT to numeric
    expenses_df['TRANSAMOUNT'] = safe_numeric_conversion(expenses_df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Group by payee and sum amounts (using absolute values)
    payee_spending = expenses_df.groupby('PAYEENAME')['TRANSAMOUNT'].sum().abs().nlargest(10)
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create horizontal bar chart
    ax.barh(range(len(payee_spending)), payee_spending.values, align='center')
    ax.set_yticks(range(len(payee_spending)))
    ax.set_yticklabels(payee_spending.index)
    ax.invert_yaxis()  # Labels read top-to-bottom
    ax.set_xlabel('Spending Amount ($)', fontsize=12)
    ax.set_title('Top 10 Payees by Spending', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Add value labels on bars
    for i, v in enumerate(payee_spending.values):
        ax.text(v + max(payee_spending.values) * 0.01, i, f'${v:.2f}', va='center', fontsize=9)
    
    logger.debug("Top payees chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_asset_distribution_chart(transactions_df):
    """
    Create a pie chart showing asset distribution by account.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating asset distribution chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['ACCOUNTNAME', 'TRANSAMOUNT'])
    
    # Group by account and sum amounts
    account_balances = transactions_df.groupby('ACCOUNTNAME')['TRANSAMOUNT'].sum().abs()
    
    # Optimize data for charting (limit to top accounts)
    if len(account_balances) > 8:
        account_balances = account_balances.nlargest(8)
    
    # Create figure and axis
    fig = Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        account_balances.values,
        labels=account_balances.index,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 8}
    )
    
    # Improve readability
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('Asset Distribution by Account', fontsize=14, pad=20)
    
    # Add legend with values
    legend_labels = [f'{acc}: ${bal:.2f}' for acc, bal in zip(account_balances.index, account_balances.values)]
    ax.legend(wedges, legend_labels, title="Accounts", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    # Adjust layout to prevent clipping
    fig.tight_layout()
    
    logger.debug("Asset distribution chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_monthly_budget_comparison_chart(transactions_df, budget_amount=None):
    """
    Create a chart comparing monthly spending to budget.
    
    Args:
        transactions_df: DataFrame containing transaction data
        budget_amount: Monthly budget amount (if None, will be calculated)
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating monthly budget comparison chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['TRANSDATE', 'TRANSAMOUNT'])
    
    # Make a copy to avoid modifying original
    df = transactions_df.copy()
    
    # Convert date column to datetime
    df['TRANSDATE'] = pd.to_datetime(df['TRANSDATE'])
    
    # Convert amount to numeric
    df['TRANSAMOUNT'] = safe_numeric_conversion(df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Filter for expenses
    expenses_df = df[df['TRANSAMOUNT'] < 0].copy()
    
    if expenses_df.empty:
        raise DataValidationError("No expense transactions found")
    
    # Group by month and sum expenses (using absolute values)
    monthly_expenses = expenses_df.groupby(df['TRANSDATE'].dt.to_period('M'))['TRANSAMOUNT'].sum().abs()
    
    # If no budget amount provided, calculate average monthly spending
    if budget_amount is None:
        budget_amount = monthly_expenses.mean() if not monthly_expenses.empty else 1000
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create bar chart
    x = range(len(monthly_expenses))
    ax.bar(x, monthly_expenses.values, label='Actual Spending', alpha=0.7)
    
    # Add budget line
    ax.axhline(y=budget_amount, color='red', linestyle='--', label=f'Budget (${budget_amount:.2f})', linewidth=2)
    
    # Format the plot
    ax.set_title('Monthly Budget Comparison', fontsize=14)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Amount ($)', fontsize=12)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Set x-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels([str(period) for period in monthly_expenses.index], rotation=45, ha='right')
    
    # Add budget variance indicators
    for i, (month, actual) in enumerate(monthly_expenses.items()):
        variance = actual - budget_amount
        color = 'green' if variance <= 0 else 'red'
        ax.text(i, actual + abs(variance) * 0.05, f'${variance:+.2f}', ha='center', va='bottom', color=color, weight='bold')
    
    logger.debug("Monthly budget comparison chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_transaction_frequency_chart(transactions_df):
    """
    Create a histogram showing transaction frequency by day of week.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating transaction frequency chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['TRANSDATE'])
    
    # Make a copy to avoid modifying original
    df = transactions_df.copy()
    
    # Convert date column to datetime
    df['TRANSDATE'] = pd.to_datetime(df['TRANSDATE'])
    
    # Extract day of week (Monday=0, Sunday=6)
    df['DAY_OF_WEEK'] = df['TRANSDATE'].dt.dayofweek
    
    # Count transactions by day of week
    day_counts = df['DAY_OF_WEEK'].value_counts().sort_index()
    
    # Create day names
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Ensure all days are represented (fill missing with 0)
    all_days = pd.Series(index=range(7), dtype='float64').fillna(0)
    all_days.update(day_counts)
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create bar chart
    bars = ax.bar(day_names, all_days.values, color=plt.cm.viridis(np.linspace(0, 1, 7)))
    
    # Format the plot
    ax.set_title('Transaction Frequency by Day of Week', fontsize=14)
    ax.set_xlabel('Day of Week', fontsize=12)
    ax.set_ylabel('Number of Transactions', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Add value labels on bars
    for bar, count in zip(bars, all_days.values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(count)}', ha='center', va='bottom', fontsize=9)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')
    
    logger.debug("Transaction frequency chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_cashflow_chart(transactions_df):
    """
    Create a line chart showing cash flow over time.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating cashflow chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['TRANSDATE', 'TRANSAMOUNT'])
    
    # Make a copy to avoid modifying original
    df = transactions_df.copy()
    
    # Convert date column to datetime
    df['TRANSDATE'] = pd.to_datetime(df['TRANSDATE'])
    
    # Convert amount to numeric
    df['TRANSAMOUNT'] = safe_numeric_conversion(df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Sort by date
    df = df.sort_values('TRANSDATE')
    
    # Calculate cumulative cash flow
    df['CUMULATIVE_CF'] = df['TRANSAMOUNT'].cumsum()
    
    # Group by date and calculate cumulative sum
    daily_cf = df.groupby('TRANSDATE')['TRANSAMOUNT'].sum().sort_index()
    cumulative_cf = daily_cf.cumsum()
    
    # Optimize data for charting
    if len(cumulative_cf) > 100:  # If too many data points, resample to weekly
        cumulative_cf = cumulative_cf.resample('W').last().ffill()
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create line chart
    ax.plot(cumulative_cf.index, cumulative_cf.values, marker='o', linestyle='-', linewidth=2, markersize=4)
    
    # Format the plot
    ax.set_title('Cumulative Cash Flow Over Time', fontsize=14)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Cash Flow ($)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # Add color coding for positive/negative values
    for i in range(len(cumulative_cf)-1):
        color = 'green' if cumulative_cf.iloc[i] >= 0 else 'red'
        ax.plot(cumulative_cf.index[i:i+2], cumulative_cf.values[i:i+2], color=color, linewidth=2)
    
    # Rotate x-axis labels for better readability
    fig.autofmt_xdate()
    
    logger.debug("Cashflow chart created successfully")
    return FigureCanvasKivyAgg(fig)


def create_summary_statistics_widget(transactions_df):
    """
    Create a widget with summary statistics.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        BoxLayout: The summary statistics widget
    """
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['TRANSAMOUNT'])
    
    # Make a copy to avoid modifying original
    df = transactions_df.copy()
    
    # Convert amount to numeric
    df['TRANSAMOUNT'] = safe_numeric_conversion(df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Calculate statistics
    total_transactions = len(df)
    total_income = df[df['TRANSAMOUNT'] > 0]['TRANSAMOUNT'].sum()
    total_expenses = df[df['TRANSAMOUNT'] < 0]['TRANSAMOUNT'].sum()
    net_cash_flow = total_income + total_expenses
    avg_transaction = df['TRANSAMOUNT'].mean()
    
    # Create layout
    stats_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=200)
    
    def create_stat_label(title, value, color=(0, 0, 0, 1)):
        """Helper function to create a styled label for statistics."""
        label = Label(
            text=f"[b]{title}:[/b] {value}",
            markup=True,
            size_hint_y=None,
            height=30,
            color=color
        )
        return label
    
    # Add statistic labels
    stats_layout.add_widget(create_stat_label("Total Transactions", f"{total_transactions:,}"))
    stats_layout.add_widget(create_stat_label("Total Income", f"${total_income:,.2f}", (0, 0.7, 0, 1)))
    stats_layout.add_widget(create_stat_label("Total Expenses", f"${total_expenses:,.2f}", (0.7, 0, 0, 1)))
    stats_layout.add_widget(create_stat_label("Net Cash Flow", f"${net_cash_flow:,.2f}", 
                                             (0, 0.7, 0, 1) if net_cash_flow >= 0 else (0.7, 0, 0, 1)))
    stats_layout.add_widget(create_stat_label("Average Transaction", f"${avg_transaction:,.2f}"))
    
    return stats_layout