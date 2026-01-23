"""
Visualization utilities for the MMEX Kivy application.

This module provides utility functions for creating and displaying
financial data visualizations using Matplotlib and Kivy.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import logging
import hashlib
import time
from typing import Dict, Any, Optional, Callable
import functools

from visualization_errors_new import VisualizationError, DataValidationError, ChartCreationError

# Configure logging for visualization module
logger = logging.getLogger(__name__)


def handle_chart_error(func: Callable) -> Callable:
    """Decorator to handle chart creation errors gracefully."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ChartCreationError:
            # Re-raise known chart errors
            raise
        except Exception as e:
            # Wrap unexpected errors in ChartCreationError
            error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
            logger.error(error_msg)
            raise ChartCreationError(error_msg) from e
    return wrapper


def create_cache_key(chart_type: str, df: pd.DataFrame) -> str:
    """Create a unique cache key for a chart based on chart type and data."""
    # Create a hash of the dataframe content and chart type
    df_hash = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()
    cache_key = f"{chart_type}_{df_hash}"
    logger.debug(f"Generated cache key: {cache_key}")
    return cache_key


def validate_dataframe(df, required_columns=None, min_rows=1):
    """
    Validate that the dataframe meets requirements for chart creation.
    
    Args:
        df: The dataframe to validate
        required_columns: List of required column names
        min_rows: Minimum number of rows required
        
    Raises:
        DataValidationError: If validation fails
    """
    if df is None:
        raise DataValidationError("DataFrame is None")
    
    if not isinstance(df, pd.DataFrame):
        raise DataValidationError(f"Expected DataFrame, got {type(df)}")
    
    if df.empty:
        raise DataValidationError("DataFrame is empty")
    
    if len(df) < min_rows:
        raise DataValidationError(f"DataFrame has {len(df)} rows, minimum {min_rows} required")
    
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise DataValidationError(f"Missing required columns: {missing_cols}")
    
    logger.debug(f"DataFrame validation passed: {len(df)} rows, {len(df.columns)} columns")


def safe_numeric_conversion(series, column_name):
    """
    Safely convert a series to numeric, handling errors gracefully.
    
    Args:
        series: Pandas Series to convert
        column_name: Name of the column (for error reporting)
        
    Returns:
        Converted numeric series
    """
    try:
        # Convert to numeric, coercing errors to NaN
        numeric_series = pd.to_numeric(series, errors='coerce')
        
        # Log warnings for any null values introduced
        null_count = numeric_series.isna().sum()
        if null_count > 0:
            logger.warning(f"Converted {null_count} non-numeric values to NaN in column '{column_name}'")
        
        return numeric_series
    except Exception as e:
        logger.error(f"Error converting column '{column_name}' to numeric: {e}")
        raise DataValidationError(f"Error converting column '{column_name}' to numeric: {e}") from e


def optimize_chart_data(df, max_categories=10, min_amount_threshold=0.01, max_data_points=100):
    """
    Optimize chart data by aggregating small categories and limiting data points.
    
    Args:
        df: Input dataframe
        max_categories: Maximum number of categories to show individually
        min_amount_threshold: Minimum threshold for individual display
        max_data_points: Maximum number of data points to return
        
    Returns:
        Optimized dataframe
    """
    logger.debug(f"Optimizing chart data: {len(df)} rows")
    
    # If we have too many data points, apply intelligent sampling
    if len(df) > max_data_points:
        df = apply_intelligent_sampling(df, max_data_points)
    
    # If we have categorical data, optimize categories
    if 'CATEGORY' in df.columns:
        # Group smaller categories into 'Other'
        if len(df['CATEGORY'].unique()) > max_categories:
            # Calculate total amounts by category
            category_totals = df.groupby('CATEGORY')['TRANSAMOUNT'].sum().abs().sort_values(ascending=False)
            
            # Identify top categories
            top_categories = category_totals.head(max_categories).index
            
            # Create optimized dataframe
            df_optimized = df.copy()
            df_optimized['CATEGORY'] = df_optimized['CATEGORY'].apply(
                lambda x: x if x in top_categories else 'Other'
            )
            
            logger.debug(f"Grouped categories from {len(category_totals)} to {len(top_categories) + ('Other' in df_optimized['CATEGORY'].values)}")
            return df_optimized
    
    logger.debug(f"Data optimization complete: {len(df)} rows")
    return df


def apply_intelligent_sampling(df, max_points):
    """
    Apply intelligent sampling to reduce data points while preserving trends.
    
    Args:
        df: Input dataframe
        max_points: Maximum number of points to return
        
    Returns:
        Sampled dataframe
    """
    if len(df) <= max_points:
        return df
    
    # For time series data, use stratified sampling
    if 'DATE' in df.columns:
        df_sorted = df.sort_values('DATE')
        step = len(df_sorted) // max_points
        sampled_df = df_sorted.iloc[::step]
    else:
        # For non-time series, use random sampling
        sampled_df = df.sample(n=max_points, random_state=42)
    
    logger.debug(f"Applied intelligent sampling: {len(df)} -> {len(sampled_df)} points")
    return sampled_df