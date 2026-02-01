"""Visualization Package for MMEX Kivy Application.

This package provides visualization components and utilities for the MMEX Kivy application.
"""

# Chart generation
from visualization.charts import (
    create_monthly_spending_chart,
    create_category_breakdown_chart,
    create_account_balance_chart,
    create_income_vs_expense_chart
)

# UI components
from visualization.view import VisualizationTab

# Caching
from visualization.cache import VisualizationCache

# Utilities
from visualization.utils import (
    validate_transaction_data,
    prepare_chart_data,
    format_currency,
    get_date_range
)

# Error handling
from visualization.errors import (
    VisualizationError,
    DataValidationError,
    ChartCreationError
)

__all__ = [
    # Chart generation functions
    'create_monthly_spending_chart',
    'create_category_breakdown_chart',
    'create_account_balance_chart',
    'create_income_vs_expense_chart',
    
    # UI components
    'VisualizationTab',
    
    # Caching
    'VisualizationCache',
    
    # Utilities
    'validate_transaction_data',
    'prepare_chart_data',
    'format_currency',
    'get_date_range',
    
    # Error classes
    'VisualizationError',
    'DataValidationError',
    'ChartCreationError'
]