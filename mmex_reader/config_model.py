"""Configuration Model for MMEX Reader."""

from dataclasses import dataclass, asdict
from typing import Dict, Any


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
