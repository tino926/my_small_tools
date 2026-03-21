"""Core Logic for Configuration Management."""

import json
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from mmex_reader.config_model import AppConfig


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
        self._config_hash = None  # Initialize as None to force a load on first access
        self.load_config()

    def _calculate_config_hash(self) -> str:
        """Calculate a hash of the current configuration to detect changes."""
        # Use pickle for faster serialization than JSON if available, otherwise fallback to JSON
        try:
            import pickle
            # Use pickle for faster serialization, then hash the bytes
            serialized = pickle.dumps(self.config.to_dict(), protocol=pickle.HIGHEST_PROTOCOL)
            return hashlib.md5(serialized).hexdigest()
        except Exception:
            # Fallback to JSON if pickle fails
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
                from mmex_reader.db_utils import load_db_path
                # Avoid initializing connection pool during config loading to prevent side effects
                env_db_path = load_db_path(initialize_pool=False)
                if env_db_path:
                    old_db_path = self.config.db_file_path
                    self.config.db_file_path = env_db_path
                    # Only update the hash if the DB path actually changed
                    if old_db_path != env_db_path:
                        self._calculate_config_hash()
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
            # Use a more unique temp file name to prevent conflicts
            tmp_path = self.config_file.with_name(f"{self.config_file.stem}.tmp.{os.getpid()}")
            with open(tmp_path, 'w', encoding='utf-8') as f:
                # Use more efficient JSON writing with sorted keys for consistent hashing
                json.dump(self.config.to_dict(), f, indent=2, sort_keys=True)
            os.replace(tmp_path, self.config_file)
            # Update the hash after successful save
            self._config_hash = current_hash
        except Exception as e:
            # Attempt cleanup of temp file on failure
            try:
                if 'tmp_path' in locals() and tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            print(f"Error saving config: {e}")
    
    def get_config(self) -> AppConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """Update configuration with new values, with validation."""
        self._validate_updates(kwargs)

        # Track which values actually changed to avoid redundant saves
        changes_made = False
        old_values = {}  # Store old values for potential rollback if needed

        for key, value in kwargs.items():
            if hasattr(self.config, key):
                old_value = getattr(self.config, key)
                # Only update if value is different to avoid unnecessary operations
                if old_value != value:
                    old_values[key] = old_value
                    setattr(self.config, key, value)
                    changes_made = True

        # Only save if there were actual changes
        if changes_made:
            self.save_config()

    def force_save_config(self) -> None:
        """Force save the configuration even if no changes are detected."""
        current_hash = self._calculate_config_hash()
        try:
            # Write atomically: write to temp file then replace
            # Use a more unique temp file name to prevent conflicts
            tmp_path = self.config_file.with_name(f"{self.config_file.stem}.tmp.{os.getpid()}")
            with open(tmp_path, 'w', encoding='utf-8') as f:
                # Use more efficient JSON writing with sorted keys for consistent hashing
                json.dump(self.config.to_dict(), f, indent=2, sort_keys=True)
            os.replace(tmp_path, self.config_file)
            # Update the hash after successful save
            self._config_hash = current_hash
        except Exception as e:
            # Attempt cleanup of temp file on failure
            try:
                if 'tmp_path' in locals() and tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
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
