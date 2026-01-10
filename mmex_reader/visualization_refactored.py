"""
Visualization utilities for the MMEX Kivy application.

This module provides classes and functions for creating and displaying
financial data visualizations using Matplotlib and Kivy.

DEPRECATED: This module has been split into smaller, more focused modules:
- visualization_cache_new.py: Caching functionality
- visualization_errors_new.py: Custom exception classes
- visualization_utils_new.py: Utility functions
- visualization_charts_new.py: Chart creation functions
- visualization_tab_new.py: Visualization tab UI component

For new code, import directly from the specific modules above.
This module is maintained for backward compatibility.
"""

# Import all components from new modules to maintain backward compatibility
from visualization_cache_new import VisualizationCache
from visualization_errors_new import VisualizationError, DataValidationError, ChartCreationError
from visualization_utils_new import (
    handle_chart_error,
    create_cache_key,
    validate_dataframe,
    safe_numeric_conversion,
    optimize_chart_data,
    apply_intelligent_sampling
)
from visualization_charts_new import (
    create_spending_by_category_chart,
    create_spending_over_time_chart,
    create_income_vs_expenses_chart,
    create_top_payees_chart,
    create_asset_distribution_chart,
    create_monthly_budget_comparison_chart,
    create_transaction_frequency_chart,
    create_cashflow_chart,
    create_summary_statistics_widget
)
from visualization_tab_new import VisualizationTab

# Define __all__ to specify what gets imported with "from visualization import *"
__all__ = [
    'VisualizationCache',
    'VisualizationError',
    'DataValidationError',
    'ChartCreationError',
    'handle_chart_error',
    'create_cache_key',
    'validate_dataframe',
    'safe_numeric_conversion',
    'optimize_chart_data',
    'apply_intelligent_sampling',
    'create_spending_by_category_chart',
    'create_spending_over_time_chart',
    'create_income_vs_expenses_chart',
    'create_top_payees_chart',
    'create_asset_distribution_chart',
    'create_monthly_budget_comparison_chart',
    'create_transaction_frequency_chart',
    'create_cashflow_chart',
    'create_summary_statistics_widget',
    'VisualizationTab'
]