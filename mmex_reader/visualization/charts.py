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

from visualization.utils import (
    handle_chart_error, validate_dataframe, safe_numeric_conversion, 
    optimize_chart_data, apply_intelligent_sampling, format_currency, get_date_range
)
from visualization.errors import VisualizationError, DataValidationError, ChartCreationError

# Configure logging for visualization module
logger = logging.getLogger(__name__)


@handle_chart_error
def create_monthly_spending_chart(transactions_df):
    """
    Create a bar chart showing monthly spending.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating monthly spending chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['TRANSDATE', 'TRANSAMOUNT'])
    
    # Make a copy to avoid modifying original
    df = transactions_df.copy()
    
    # Convert date column to datetime
    df['TRANSDATE'] = pd.to_datetime(df['TRANSDATE'])
    
    # Convert amount to numeric
    df['TRANSAMOUNT'] = safe_numeric_conversion(df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Filter for expenses (negative amounts)
    expenses_df = df[df['TRANSAMOUNT'] < 0].copy()
    
    if expenses_df.empty:
        raise DataValidationError("No expense transactions found")
    
    # Group by month and sum amounts (using absolute values)
    monthly_spending = expenses_df.groupby(df['TRANSDATE'].dt.to_period('M'))['TRANSAMOUNT'].sum().abs()
    
    # Optimize data for charting
    monthly_spending = optimize_chart_data(
        pd.DataFrame({'Month': monthly_spending.index.astype(str), 'Spending': monthly_spending.values}),
        max_data_points=12
    )
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    # Create bar chart
    ax.bar(monthly_spending['Month'], monthly_spending['Spending'], color='skyblue', alpha=0.8)
    
    # Format the plot
    ax.set_title('Monthly Spending', fontsize=14)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Spending Amount ($)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Rotate x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Add value labels on bars
    for i, (month, amount) in enumerate(zip(monthly_spending['Month'], monthly_spending['Spending'])):
        ax.text(i, amount + max(monthly_spending['Spending']) * 0.01, 
                format_currency(amount), ha='center', va='bottom', fontsize=9)
    
    logger.debug("Monthly spending chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_category_breakdown_chart(transactions_df):
    """
    Create a pie chart showing spending by category.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating category breakdown chart")
    
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
        pd.DataFrame({'Category': category_spending.index, 'Amount': category_spending.values}),
        max_categories=8
    ).groupby('Category')['Amount'].sum()
    
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
    legend_labels = [f'{cat}: {format_currency(amt)}' for cat, amt in zip(category_spending.index, category_spending.values)]
    ax.legend(wedges, legend_labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    # Adjust layout to prevent clipping
    fig.tight_layout()
    
    logger.debug("Category breakdown chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_account_balance_chart(transactions_df):
    """
    Create a line chart showing account balance over time.
    
    Args:
        transactions_df: DataFrame containing transaction data
        
    Returns:
        FigureCanvasKivyAgg: The chart widget
    """
    logger.debug("Creating account balance chart")
    
    # Validate input data
    validate_dataframe(transactions_df, required_columns=['TRANSDATE', 'TRANSAMOUNT', 'ACCOUNTNAME'])
    
    # Make a copy to avoid modifying original
    df = transactions_df.copy()
    
    # Convert date column to datetime
    df['TRANSDATE'] = pd.to_datetime(df['TRANSDATE'])
    
    # Convert amount to numeric
    df['TRANSAMOUNT'] = safe_numeric_conversion(df['TRANSAMOUNT'], 'TRANSAMOUNT')
    
    # Sort by date
    df = df.sort_values('TRANSDATE')
    
    # Group by account and calculate cumulative balance for each account
    accounts = df['ACCOUNTNAME'].unique()
    
    # Create figure and axis
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(accounts)))
    
    for account, color in zip(accounts, colors):
        account_df = df[df['ACCOUNTNAME'] == account].copy()
        
        # Calculate cumulative balance
        account_df['CUMULATIVE_BALANCE'] = account_df['TRANSAMOUNT'].cumsum()
        
        # Create line chart
        ax.plot(account_df['TRANSDATE'], account_df['CUMULATIVE_BALANCE'], 
                label=account, color=color, linewidth=2, marker='o', markersize=4)
    
    # Format the plot
    ax.set_title('Account Balance Over Time', fontsize=14)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Balance ($)', fontsize=12)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # Rotate x-axis labels for better readability
    fig.autofmt_xdate()
    
    logger.debug("Account balance chart created successfully")
    return FigureCanvasKivyAgg(fig)


@handle_chart_error
def create_income_vs_expense_chart(transactions_df):
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