"""Base classes for UI components."""

from typing import Optional, Callable
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

from .config import ui_config

# Import show_popup via lazy import or circular dependency handling if needed
# For now, we'll assume show_popup is available via a mixin or helper
# Actually, the original BaseUIComponent called show_popup which was a global function.
# We will need to handle this. Maybe move show_popup to a separate 'dialogs.py' or 'utils.py'.
# But 'widgets.py' is a good place for generic widgets and dialogs.
# Let's import show_popup inside methods to avoid circular imports if it ends up in widgets.py

class BaseUIComponent(BoxLayout):
    """Base class for all UI components with common functionality."""
    
    def __init__(self, **kwargs):
        super(BaseUIComponent, self).__init__(**kwargs)
        self.ui_config = ui_config
        self._setup_base_properties()
    
    def _setup_base_properties(self):
        """Setup base properties for the component."""
        self.padding = self.ui_config.responsive.padding
        self.spacing = self.ui_config.responsive.spacing
    
    def create_label(self, text: str, **kwargs) -> Label:
        """Create a standardized label with consistent styling."""
        default_props = {
            'text': text,
            'size_hint_y': None,
            'height': self.ui_config.responsive.button_height,
            'halign': 'left',
            'valign': 'middle'
        }
        default_props.update(kwargs)
        
        label = Label(**default_props)
        label.bind(size=label.setter('text_size'))
        return label
    
    def create_button(self, text: str, callback: Optional[Callable] = None, **kwargs) -> Button:
        """Create a standardized button with consistent styling."""
        default_props = {
            'text': text,
            'size_hint_y': None,
            'height': self.ui_config.responsive.button_height,
            'background_color': self.ui_config.colors.button
        }
        default_props.update(kwargs)
        
        button = Button(**default_props)
        if callback:
            button.bind(on_release=callback)
        return button
    
    def create_text_input(self, text: str = '', **kwargs) -> TextInput:
        """Create a standardized text input with consistent styling."""
        default_props = {
            'text': text,
            'size_hint_y': None,
            'height': self.ui_config.responsive.input_height,
            'multiline': False
        }
        default_props.update(kwargs)
        
        return TextInput(**default_props)
    
    def show_error(self, message: str, title: str = "Error"):
        """Show an error popup with consistent styling."""
        from .widgets import show_popup
        show_popup(title, message, popup_type='error')
    
    def show_success(self, message: str, title: str = "Success"):
        """Show a success popup with consistent styling."""
        from .widgets import show_popup
        show_popup(title, message, popup_type='success')
