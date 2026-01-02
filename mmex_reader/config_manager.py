"""Configuration Management Module for MMEX Reader Application.

This module provides a centralized configuration management system that supports
both file-based configuration (.env files) and GUI-based settings management.
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from ui_components import show_popup
except Exception:
    def show_popup(title, text, popup_type='info'):
        print(f"{title}: {text}")

try:
    from kivy.uix.popup import Popup as BasePopup
except Exception:
    class BasePopup:
        pass


@dataclass
class AppConfig:
    """Application configuration data class."""
    
    # Database settings
    db_file_path: str = ""
    
    # UI settings
    page_size: int = 50
    default_font_size: int = 14
    theme_mode: str = "light"  # "light" or "dark"
    
    # Date settings
    date_format: str = "%Y-%m-%d"
    default_date_range_days: int = 30
    
    # Performance settings
    enable_caching: bool = True
    cache_timeout_minutes: int = 15
    max_cache_size_mb: int = 100
    
    # Export settings
    default_export_format: str = "csv"  # "csv", "json", "pdf"
    export_directory: str = ""
    
    # Chart settings
    default_chart_type: str = "Monthly Spending"
    chart_color_scheme: str = "default"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create config from dictionary."""
        return cls(**data)


import hashlib

class ConfigManager:
    """Manages application configuration with file persistence."""

    def __init__(self, config_file: str = "mmex_config.json"):
        # Use user's home directory for configuration
        home_dir = Path.home() / ".mmex_reader"
        # Create config directory if it doesn't exist
        home_dir.mkdir(exist_ok=True, parents=True)
        self.config_file = home_dir / config_file
        self.config = AppConfig()
        # Add a config hash to track changes and prevent unnecessary writes
        self._config_hash = self._calculate_config_hash()
        self.load_config()

    def _calculate_config_hash(self) -> str:
        """Calculate a hash of the current configuration to detect changes."""
        config_dict = self.config.to_dict()
        # Convert config to a consistent JSON string for hashing
        config_str = json.dumps(config_dict, sort_keys=True, default=str)
        # Create hash of the configuration string
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = AppConfig.from_dict(data)
                    # Update the hash after loading
                    self._config_hash = self._calculate_config_hash()
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                # Backup the corrupt/invalid config to preserve user data, then reset to defaults
                print(f"Error loading config: {e}. Using defaults.")
                try:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_name = f"{self.config_file.stem}.corrupt_{ts}{self.config_file.suffix}"
                    backup_path = self.config_file.with_name(backup_name)
                    os.replace(self.config_file, backup_path)
                    print(f"Backed up invalid config to: {backup_path}")
                except Exception as backup_err:
                    print(f"Failed to backup invalid config: {backup_err}")
                self.config = AppConfig()
                # Update the hash after resetting to defaults
                self._config_hash = self._calculate_config_hash()

        # Load database path from .env if not set in config
        if not self.config.db_file_path:
            try:
                from db_utils import load_db_path
                # Avoid initializing connection pool during config loading to prevent side effects
                env_db_path = load_db_path(initialize_pool=False)
                if env_db_path:
                    self.config.db_file_path = env_db_path
                    # Update the hash after setting db path from env
                    self._config_hash = self._calculate_config_hash()
            except ImportError:
                # Fallback in case db_utils is not available
                pass
    
    def save_config(self) -> None:
        """Save configuration to file, only if changes have occurred."""
        # Check if config has actually changed before saving
        current_hash = self._calculate_config_hash()
        if current_hash == self._config_hash:
            # No changes, skip saving
            return

        try:
            # Write atomically: write to temp file then replace
            tmp_path = self.config_file.with_suffix(self.config_file.suffix + ".tmp")
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            os.replace(tmp_path, self.config_file)
            # Update the hash after successful save
            self._config_hash = current_hash
        except Exception as e:
            # Attempt cleanup of temp file on failure
            try:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            print(f"Error saving config: {e}")
    
    def get_config(self) -> AppConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """Update configuration with new values, with validation."""
        self._validate_updates(kwargs)
        config_changed = False
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                old_value = getattr(self.config, key)
                setattr(self.config, key, value)
                # Check if the value actually changed
                if old_value != value:
                    config_changed = True

        # Only save if there were actual changes
        if config_changed:
            self.save_config()

    def force_save_config(self) -> None:
        """Force save the configuration even if no changes are detected."""
        current_hash = self._calculate_config_hash()
        try:
            # Write atomically: write to temp file then replace
            tmp_path = self.config_file.with_suffix(self.config_file.suffix + ".tmp")
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            os.replace(tmp_path, self.config_file)
            # Update the hash after successful save
            self._config_hash = current_hash
        except Exception as e:
            # Attempt cleanup of temp file on failure
            try:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            print(f"Error saving config: {e}")

    def _validate_updates(self, updates: Dict[str, Any]) -> None:
        """Validate incoming configuration updates and raise on invalid values."""
        errors = []
        # Allowed option sets
        allowed_theme_modes = ("light", "dark")
        allowed_export_formats = ("csv", "json", "pdf")
        allowed_chart_types = ("Monthly Spending", "Category Distribution", "Account Balance", "Income vs Expense")
        allowed_color_schemes = ("default", "pastel", "bright", "monochrome")
        # Numeric fields must be positive integers
        numeric_positive_keys = (
            "page_size",
            "default_font_size",
            "default_date_range_days",
            "cache_timeout_minutes",
            "max_cache_size_mb",
        )
        for key in numeric_positive_keys:
            if key in updates:
                val = updates[key]
                if not isinstance(val, int) or val <= 0:
                    errors.append(f"{key} must be a positive integer")
        # db_file_path must exist if provided
        if "db_file_path" in updates:
            db_path = updates["db_file_path"]
            if not isinstance(db_path, str) or not db_path:
                errors.append("db_file_path must be a non-empty string")
            else:
                import os as _os
                if not _os.path.exists(db_path):
                    errors.append(f"Database file not found: {db_path}")
        # export_directory must be an existing directory if provided
        if "export_directory" in updates:
            export_dir = updates["export_directory"]
            if export_dir:
                import os as _os
                if not _os.path.isdir(export_dir):
                    errors.append(f"Export directory not found: {export_dir}")
        # date_format must be non-empty string
        if "date_format" in updates:
            dfmt = updates["date_format"]
            if not isinstance(dfmt, str) or not dfmt.strip():
                errors.append("date_format must be a non-empty string")
        # Enum-like options
        if "theme_mode" in updates and updates["theme_mode"] not in allowed_theme_modes:
            errors.append(f"theme_mode must be one of {allowed_theme_modes}")
        if "default_export_format" in updates and updates["default_export_format"] not in allowed_export_formats:
            errors.append(f"default_export_format must be one of {allowed_export_formats}")
        if "default_chart_type" in updates and updates["default_chart_type"] not in allowed_chart_types:
            errors.append(f"default_chart_type must be one of {allowed_chart_types}")
        if "chart_color_scheme" in updates and updates["chart_color_scheme"] not in allowed_color_schemes:
            errors.append(f"chart_color_scheme must be one of {allowed_color_schemes}")
        # Raise if any problems
        if errors:
            raise ValueError("; ".join(errors))


class SettingsPopup(BasePopup):
    """Settings configuration popup window."""
    
    def __init__(self, config_manager: ConfigManager, **kwargs):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.label import Label
        from kivy.uix.popup import Popup
        from kivy.core.window import Window
        from kivy.uix.spinner import Spinner
        from kivy.uix.switch import Switch
        from kivy.uix.textinput import TextInput
        from kivy.uix.gridlayout import GridLayout
        from kivy.uix.scrollview import ScrollView

        super().__init__(**kwargs)
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        self.title = "Application Settings"
        self.size_hint = (0.8, 0.9)
        self.auto_dismiss = False
        
        # Create main layout
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Create scrollable content
        scroll = ScrollView()
        content_layout = GridLayout(cols=2, spacing=10, size_hint_y=None)
        content_layout.bind(minimum_height=content_layout.setter('height'))
        
        # Database settings
        self._add_section_header(content_layout, "Database Settings")
        self._add_file_picker(content_layout, "Database File:", self.config.db_file_path, "db_file_path")
        
        # UI settings
        self._add_section_header(content_layout, "UI Settings")
        self._add_number_input(content_layout, "Page Size:", str(self.config.page_size), "page_size")
        self._add_number_input(content_layout, "Font Size:", str(self.config.default_font_size), "default_font_size")
        self._add_spinner(content_layout, "Theme:", self.config.theme_mode, ["light", "dark"], "theme_mode")
        
        # Date settings
        self._add_section_header(content_layout, "Date Settings")
        self._add_text_input(content_layout, "Date Format:", self.config.date_format, "date_format")
        self._add_number_input(content_layout, "Default Range (days):", str(self.config.default_date_range_days), "default_date_range_days")
        
        # Performance settings
        self._add_section_header(content_layout, "Performance Settings")
        self._add_switch(content_layout, "Enable Caching:", self.config.enable_caching, "enable_caching")
        self._add_number_input(content_layout, "Cache Timeout (min):", str(self.config.cache_timeout_minutes), "cache_timeout_minutes")
        self._add_number_input(content_layout, "Max Cache Size (MB):", str(self.config.max_cache_size_mb), "max_cache_size_mb")
        
        # Export settings
        self._add_section_header(content_layout, "Export Settings")
        self._add_spinner(content_layout, "Default Format:", self.config.default_export_format, ["csv", "json", "pdf"], "default_export_format")
        self._add_file_picker(content_layout, "Export Directory:", self.config.export_directory, "export_directory", select_dir=True)
        
        # Chart settings
        self._add_section_header(content_layout, "Chart Settings")
        chart_types = ["Monthly Spending", "Category Distribution", "Account Balance", "Income vs Expense"]
        self._add_spinner(content_layout, "Default Chart:", self.config.default_chart_type, chart_types, "default_chart_type")
        color_schemes = ["default", "pastel", "bright", "monochrome"]
        self._add_spinner(content_layout, "Color Scheme:", self.config.chart_color_scheme, color_schemes, "chart_color_scheme")
        
        scroll.add_widget(content_layout)
        main_layout.add_widget(scroll)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        save_btn = Button(text="Save", background_color=(0.2, 0.8, 0.2, 1))
        save_btn.bind(on_press=self._save_settings)
        
        cancel_btn = Button(text="Cancel", background_color=(0.8, 0.2, 0.2, 1))
        cancel_btn.bind(on_press=self.dismiss)
        
        reset_btn = Button(text="Reset to Defaults", background_color=(0.8, 0.8, 0.2, 1))
        reset_btn.bind(on_press=self._reset_to_defaults)
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(reset_btn)
        
        main_layout.add_widget(button_layout)
        self.content = main_layout
        Window.bind(on_key_down=self._on_key_down)
        self.bind(on_dismiss=lambda instance: Window.unbind(on_key_down=self._on_key_down))
        
        # Store references to input widgets
        self.input_widgets = {}

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        if key == 27:
            try:
                self.dismiss()
            except Exception:
                pass
            return True
        return False
    
    def _add_section_header(self, layout, title):
        from kivy.uix.label import Label
        """Add a section header to the layout."""
        header = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            size_hint_y=None,
            height=40,
            color=(0.2, 0.2, 0.8, 1)
        )
        layout.add_widget(header)
        layout.add_widget(Label())  # Empty cell for spacing
    
    def _add_text_input(self, layout, label_text, value, config_key):
        from kivy.uix.label import Label
        from kivy.uix.textinput import TextInput
        """Add a text input field."""
        layout.add_widget(Label(text=label_text, size_hint_y=None, height=35))
        text_input = TextInput(text=str(value), multiline=False, size_hint_y=None, height=35)
        layout.add_widget(text_input)
        self.input_widgets[config_key] = text_input
    
    def _add_number_input(self, layout, label_text, value, config_key):
        from kivy.uix.label import Label
        from kivy.uix.textinput import TextInput
        """Add a number input field."""
        layout.add_widget(Label(text=label_text, size_hint_y=None, height=35))
        number_input = TextInput(text=str(value), multiline=False, input_filter='int', size_hint_y=None, height=35)
        layout.add_widget(number_input)
        self.input_widgets[config_key] = number_input
    
    def _add_switch(self, layout, label_text, value, config_key):
        from kivy.uix.label import Label
        from kivy.uix.switch import Switch
        """Add a switch (boolean) input."""
        layout.add_widget(Label(text=label_text, size_hint_y=None, height=35))
        switch = Switch(active=value, size_hint_y=None, height=35)
        layout.add_widget(switch)
        self.input_widgets[config_key] = switch
    
    def _add_spinner(self, layout, label_text, value, options, config_key):
        from kivy.uix.label import Label
        from kivy.uix.spinner import Spinner
        """Add a spinner (dropdown) input."""
        layout.add_widget(Label(text=label_text, size_hint_y=None, height=35))
        spinner = Spinner(text=str(value), values=options, size_hint_y=None, height=35)
        layout.add_widget(spinner)
        self.input_widgets[config_key] = spinner
    
    def _add_file_picker(self, layout, label_text, value, config_key, select_dir=False):
        from kivy.uix.label import Label
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        """Add a file picker input."""
        layout.add_widget(Label(text=label_text, size_hint_y=None, height=35))
        
        file_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        text_input = TextInput(text=str(value), multiline=False)
        browse_btn = Button(text="Browse", size_hint_x=None, width=80)
        
        def open_file_chooser(instance):
            self._show_file_chooser(text_input, select_dir)
        
        browse_btn.bind(on_press=open_file_chooser)
        
        file_layout.add_widget(text_input)
        file_layout.add_widget(browse_btn)
        layout.add_widget(file_layout)
        
        self.input_widgets[config_key] = text_input
    
    def _show_file_chooser(self, text_input, select_dir=False):
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.popup import Popup
        """Show file chooser dialog."""
        file_chooser = FileChooserListView()
        if text_input.text and os.path.exists(text_input.text):
            file_chooser.path = os.path.dirname(text_input.text) if not select_dir else text_input.text
        
        popup_content = BoxLayout(orientation='vertical')
        popup_content.add_widget(file_chooser)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        select_btn = Button(text="Select")
        cancel_btn = Button(text="Cancel")
        
        button_layout.add_widget(select_btn)
        button_layout.add_widget(cancel_btn)
        popup_content.add_widget(button_layout)
        
        file_popup = Popup(title="Select File" if not select_dir else "Select Directory",
                          content=popup_content, size_hint=(0.8, 0.8))
        
        def select_file(instance):
            if select_dir:
                text_input.text = file_chooser.path
            else:
                if file_chooser.selection:
                    text_input.text = file_chooser.selection[0]
            file_popup.dismiss()
        
        select_btn.bind(on_press=select_file)
        cancel_btn.bind(on_press=file_popup.dismiss)
        
        file_popup.open()
    
    def _save_settings(self, instance):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.textinput import TextInput
        from kivy.uix.spinner import Spinner
        from kivy.uix.switch import Switch
        from kivy.clock import Clock
        """Save the current settings."""
        try:
            # Collect values from input widgets
            updates = {}
            for key, widget in self.input_widgets.items():
                if isinstance(widget, TextInput):
                    value = widget.text
                    # Convert to appropriate type
                    if key in ['page_size', 'default_font_size', 'default_date_range_days', 
                              'cache_timeout_minutes', 'max_cache_size_mb']:
                        value = int(value) if value.isdigit() else getattr(self.config, key)
                    updates[key] = value
                elif isinstance(widget, Switch):
                    updates[key] = widget.active
                elif isinstance(widget, Spinner):
                    updates[key] = widget.text
            
            # Update configuration
            self.config_manager.update_config(**updates)
            
            # Show success message
            success_popup = Popup(
                title="Settings Saved",
                content=Label(text="Settings have been saved successfully!"),
                size_hint=(0.4, 0.3)
            )
            success_popup.open()
            
            # Close after a delay
            Clock.schedule_once(lambda dt: success_popup.dismiss(), 2)
            Clock.schedule_once(lambda dt: self.dismiss(), 2.5)
            
        except Exception as e:
            show_popup("Error", f"Error saving settings: {str(e)}", popup_type='error')
    
    def _reset_to_defaults(self, instance):
        from kivy.uix.textinput import TextInput
        from kivy.uix.switch import Switch
        from kivy.uix.spinner import Spinner
        """Reset all settings to default values."""
        default_config = AppConfig()
        
        # Update input widgets with default values
        for key, widget in self.input_widgets.items():
            default_value = getattr(default_config, key)
            if isinstance(widget, TextInput):
                widget.text = str(default_value)
            elif isinstance(widget, Switch):
                widget.active = default_value
            elif isinstance(widget, Spinner):
                widget.text = str(default_value)


# Global config manager instance
config_manager = ConfigManager()
