"""
Visualization tab for the MMEX Kivy application.

This module provides the VisualizationTab class that creates the visualization interface.
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
from typing import Dict, Any, Optional

from visualization.cache import VisualizationCache
from visualization.errors import VisualizationError, DataValidationError, ChartCreationError
from visualization.charts import (
    create_monthly_spending_chart, create_category_breakdown_chart,
    create_account_balance_chart, create_income_vs_expense_chart
)
from ui.config import ui_config

# Configure logging for visualization module
logger = logging.getLogger(__name__)

class VisualizationTab(BoxLayout):
    """Tab for displaying financial data visualizations."""

    def __init__(self, **kwargs):
        super(VisualizationTab, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = ui_config.responsive.spacing
        self.padding = ui_config.responsive.padding
        
        # Initialize cache
        self.cache = VisualizationCache()
        
        # Reference to parent app (will be set later)
        self.parent_app = None
        
        # Current chart type
        self.current_chart_type = "Monthly Spending"
        
        # Create UI components
        self._create_toolbar()
        self._create_chart_container()
        self._create_status_bar()
        
        # Loading indicator
        self.loading_label = None

    def set_parent_app(self, app):
        """Set reference to parent application."""
        self.parent_app = app

    def show_loading(self):
        """Show loading indicator."""
        if self.loading_label:
            self.loading_label.text = "Loading chart..."
        else:
            # Create loading label if it doesn't exist
            self.loading_label = Label(
                text="Loading chart...",
                size_hint_y=None,
                height=ui_config.responsive.button_height
            )
            # Insert at position 1 (after toolbar, before chart container)
            self.add_widget(self.loading_label, index=1)

    def hide_loading(self):
        """Hide loading indicator."""
        if self.loading_label:
            self.remove_widget(self.loading_label)
            self.loading_label = None

    def show_chart_error(self, error_msg):
        """Show chart error message."""
        error_label = Label(
            text=f"Chart Error: {error_msg}",
            color=(0.8, 0.2, 0.2, 1),
            size_hint_y=None,
            height=ui_config.responsive.button_height * 2
        )
        
        # Clear chart container and add error message
        self.chart_container.clear_widgets()
        self.chart_container.add_widget(error_label)
        
        logger.error(f"Chart error: {error_msg}")

    def refresh_chart(self, instance=None):
        """Refresh the current chart."""
        if hasattr(self, 'current_df') and self.current_df is not None:
            self.show_chart(self.current_df)

    def update_chart(self, transactions_df):
        """Update the chart with new data."""
        self.show_chart(transactions_df)

    def show_chart(self, transactions_df):
        """Display a chart based on the selected chart type."""
        try:
            # Store reference to current data
            self.current_df = transactions_df
            
            # Show loading indicator
            self.show_loading()
            
            # Validate data
            if transactions_df is None or transactions_df.empty:
                self.show_chart_error("No data available for visualization")
                return
            
            # Create cache key
            cache_key = f"{self.current_chart_type}_{hash(str(transactions_df.shape))}"
            
            # Try to get chart from cache
            cached_chart = self.cache.get(cache_key)
            if cached_chart:
                logger.info(f"Using cached chart for: {self.current_chart_type}")
                self._display_chart(cached_chart)
                self.hide_loading()
                return
            
            # Create new chart
            logger.info(f"Creating new chart: {self.current_chart_type}")
            
            # Select chart creation function based on type
            chart_functions = {
                "Monthly Spending": create_monthly_spending_chart,
                "Category Breakdown": create_category_breakdown_chart,
                "Account Balance": create_account_balance_chart,
                "Income vs Expenses": create_income_vs_expense_chart
            }
            
            if self.current_chart_type not in chart_functions:
                raise ChartCreationError(f"Unknown chart type: {self.current_chart_type}")
            
            # Create the chart
            chart_func = chart_functions[self.current_chart_type]
            chart_widget = chart_func(transactions_df)
            
            # Cache the chart
            self.cache.set(cache_key, chart_widget)
            
            # Display the chart
            self._display_chart(chart_widget)
            
            # Hide loading indicator
            self.hide_loading()
            
        except DataValidationError as e:
            self.show_chart_error(f"Data validation error: {str(e)}")
        except ChartCreationError as e:
            self.show_chart_error(f"Chart creation error: {str(e)}")
        except Exception as e:
            self.show_chart_error(f"Unexpected error: {str(e)}")
            logger.exception("Unexpected error in show_chart")

    def _display_chart(self, chart_widget):
        """Display the chart in the container."""
        try:
            # Clear existing chart
            self.chart_container.clear_widgets()
            
            # Add chart widget to container
            self.chart_container.add_widget(chart_widget)
            
            # Update status
            self.status_label.text = f"Showing: {self.current_chart_type}"
            
        except Exception as e:
            logger.error(f"Error displaying chart: {e}")
            self.show_chart_error(f"Error displaying chart: {e}")

    def show_chart_options(self, instance):
        """Show chart type selection popup."""
        # Create popup content
        popup_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Chart type options
        chart_types = [
            "Monthly Spending",
            "Category Breakdown",
            "Account Balance",
            "Income vs Expenses"
        ]
        
        # Add buttons for each chart type
        for chart_type in chart_types:
            btn = Button(
                text=chart_type,
                size_hint_y=None,
                height=ui_config.responsive.button_height
            )
            
            def create_callback(ct):
                return lambda instance: self.set_chart_type(ct)
            
            btn.bind(on_release=create_callback(chart_type))
            popup_content.add_widget(btn)
        
        # Add close button
        close_btn = Button(
            text="Close",
            size_hint_y=None,
            height=ui_config.responsive.button_height,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        close_btn.bind(on_release=lambda instance: chart_popup.dismiss())
        popup_content.add_widget(close_btn)
        
        # Create and show popup
        chart_popup = Popup(
            title="Select Chart Type",
            content=popup_content,
            size_hint=(0.6, 0.8)
        )
        chart_popup.open()

    def set_chart_type(self, chart_type):
        """Set the current chart type and refresh the chart."""
        self.current_chart_type = chart_type
        if hasattr(self, 'current_df') and self.current_df is not None:
            self.show_chart(self.current_df)

    def _create_toolbar(self):
        """Create the toolbar with chart controls."""
        toolbar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=ui_config.responsive.button_height + 20,
            spacing=ui_config.responsive.spacing
        )
        
        # Chart type selector button
        chart_type_btn = Button(
            text=f"Chart: {self.current_chart_type}",
            size_hint_x=0.4
        )
        chart_type_btn.bind(on_release=self.show_chart_options)
        toolbar.add_widget(chart_type_btn)
        
        # Refresh button
        refresh_btn = Button(
            text="Refresh",
            size_hint_x=0.2
        )
        refresh_btn.bind(on_release=self.refresh_chart)
        toolbar.add_widget(refresh_btn)
        
        # Add some space
        toolbar.add_widget(Label(size_hint_x=0.3))
        
        # Add toolbar to main layout
        self.add_widget(toolbar)

    def _create_chart_container(self):
        """Create the container for the chart."""
        self.chart_container = BoxLayout(
            orientation='vertical',
            size_hint_y=0.8
        )
        
        # Add initial message
        initial_label = Label(
            text="Select a chart type to begin",
            color=(0.5, 0.5, 0.5, 1),
            font_size=16
        )
        self.chart_container.add_widget(initial_label)
        
        # Add chart container to main layout
        self.add_widget(self.chart_container)

    def _create_status_bar(self):
        """Create the status bar."""
        status_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=ui_config.responsive.button_height
        )
        
        self.status_label = Label(
            text="Ready",
            halign='left'
        )
        status_layout.add_widget(self.status_label)
        
        # Add status bar to main layout
        self.add_widget(status_layout)