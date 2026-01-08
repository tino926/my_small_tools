"""
Visualization errors for the MMEX Kivy application.

This module defines custom exception classes for visualization-related errors.
"""

class VisualizationError(Exception):
    """Base exception class for visualization errors."""
    pass


class DataValidationError(VisualizationError):
    """Exception raised when data validation fails."""
    pass


class ChartCreationError(VisualizationError):
    """Exception raised when chart creation fails."""
    pass