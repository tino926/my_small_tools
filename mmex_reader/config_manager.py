"""Configuration Management Module for MMEX Reader Application - Final Refactor.

This module now serves as a clean interface to the configuration system,
with concerns separated into model, logic, and UI modules.
"""

from mmex_reader.config_model import AppConfig
from mmex_reader.config_logic import ConfigManager
from mmex_reader.config_ui import SettingsPopup

# Global config manager instance to be used across the application
config_manager = ConfigManager()
