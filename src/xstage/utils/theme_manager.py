"""
Theme Management System
Dark/Light theme support with customization
"""

from typing import Dict, Optional
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from enum import Enum

from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QColor, QPalette


class ThemeMode(Enum):
    """Theme modes"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system
    CUSTOM = "custom"


@dataclass
class ThemeColors:
    """Theme color palette"""
    # Window colors
    window_bg: str = "#ffffff"
    window_fg: str = "#000000"
    
    # Base colors
    base_bg: str = "#ffffff"
    base_fg: str = "#000000"
    
    # Alternate colors
    alternate_bg: str = "#f0f0f0"
    alternate_fg: str = "#000000"
    
    # Button colors
    button_bg: str = "#e0e0e0"
    button_fg: str = "#000000"
    button_hover: str = "#d0d0d0"
    button_pressed: str = "#c0c0c0"
    
    # Highlight colors
    highlight: str = "#0078d4"
    highlight_text: str = "#ffffff"
    
    # Link colors
    link: str = "#0066cc"
    link_visited: str = "#551a8b"
    
    # Tooltip colors
    tooltip_bg: str = "#ffffdc"
    tooltip_fg: str = "#000000"
    
    # Disabled colors
    disabled_bg: str = "#e0e0e0"
    disabled_fg: str = "#808080"
    
    # Viewport colors
    viewport_bg: str = "#2b2b2b"
    viewport_grid: str = "#404040"
    viewport_axis_x: str = "#ff0000"
    viewport_axis_y: str = "#00ff00"
    viewport_axis_z: str = "#0000ff"


class ThemeManager(QObject):
    """Manages application themes"""
    
    theme_changed = Signal(str)  # Emits theme name
    
    # Built-in themes
    DARK_THEME = ThemeColors(
        window_bg="#2b2b2b",
        window_fg="#ffffff",
        base_bg="#1e1e1e",
        base_fg="#d4d4d4",
        alternate_bg="#252526",
        alternate_fg="#cccccc",
        button_bg="#3c3c3c",
        button_fg="#cccccc",
        button_hover="#505050",
        button_pressed="#606060",
        highlight="#0078d4",
        highlight_text="#ffffff",
        link="#4ec9b0",
        link_visited="#c586c0",
        tooltip_bg="#252526",
        tooltip_fg="#cccccc",
        disabled_bg="#2d2d30",
        disabled_fg="#6a6a6a",
        viewport_bg="#1e1e1e",
        viewport_grid="#404040",
        viewport_axis_x="#ff6b6b",
        viewport_axis_y="#51cf66",
        viewport_axis_z="#4dabf7",
    )
    
    LIGHT_THEME = ThemeColors(
        window_bg="#ffffff",
        window_fg="#000000",
        base_bg="#ffffff",
        base_fg="#000000",
        alternate_bg="#f5f5f5",
        alternate_fg="#000000",
        button_bg="#e0e0e0",
        button_fg="#000000",
        button_hover="#d0d0d0",
        button_pressed="#c0c0c0",
        highlight="#0078d4",
        highlight_text="#ffffff",
        link="#0066cc",
        link_visited="#551a8b",
        tooltip_bg="#ffffdc",
        tooltip_fg="#000000",
        disabled_bg="#f0f0f0",
        disabled_fg="#808080",
        viewport_bg="#f5f5f5",
        viewport_grid="#d0d0d0",
        viewport_axis_x="#ff0000",
        viewport_axis_y="#00ff00",
        viewport_axis_z="#0000ff",
    )
    
    HIGH_CONTRAST_THEME = ThemeColors(
        window_bg="#000000",
        window_fg="#ffffff",
        base_bg="#000000",
        base_fg="#ffffff",
        alternate_bg="#1a1a1a",
        alternate_fg="#ffffff",
        button_bg="#333333",
        button_fg="#ffffff",
        button_hover="#444444",
        button_pressed="#555555",
        highlight="#ffff00",
        highlight_text="#000000",
        link="#00ffff",
        link_visited="#ff00ff",
        tooltip_bg="#000000",
        tooltip_fg="#ffffff",
        disabled_bg="#1a1a1a",
        disabled_fg="#888888",
        viewport_bg="#000000",
        viewport_grid="#333333",
        viewport_axis_x="#ff0000",
        viewport_axis_y="#00ff00",
        viewport_axis_z="#0000ff",
    )
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("xStage", "Theme")
        self.current_theme: ThemeColors = self.DARK_THEME
        self.custom_themes: Dict[str, ThemeColors] = {}
        self.current_theme_name = "dark"
        self.load_settings()
    
    def load_settings(self):
        """Load theme settings from disk"""
        theme_name = self.settings.value("theme", "dark", type=str)
        mode = self.settings.value("theme_mode", "dark", type=str)
        
        # Load custom themes
        custom_themes_path = Path.home() / ".xstage" / "themes.json"
        if custom_themes_path.exists():
            try:
                with open(custom_themes_path, 'r') as f:
                    data = json.load(f)
                    for name, colors_dict in data.get("custom_themes", {}).items():
                        self.custom_themes[name] = ThemeColors(**colors_dict)
            except Exception as e:
                print(f"Error loading custom themes: {e}")
        
        self.set_theme(theme_name)
    
    def save_settings(self):
        """Save theme settings to disk"""
        self.settings.setValue("theme", self.current_theme_name)
        
        # Save custom themes
        custom_themes_path = Path.home() / ".xstage" / "themes.json"
        custom_themes_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {
                "custom_themes": {
                    name: asdict(colors) for name, colors in self.custom_themes.items()
                }
            }
            with open(custom_themes_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving custom themes: {e}")
    
    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name == "dark":
            self.current_theme = self.DARK_THEME
        elif theme_name == "light":
            self.current_theme = self.LIGHT_THEME
        elif theme_name == "high_contrast":
            self.current_theme = self.HIGH_CONTRAST_THEME
        elif theme_name in self.custom_themes:
            self.current_theme = self.custom_themes[theme_name]
        else:
            # Default to dark
            self.current_theme = self.DARK_THEME
            theme_name = "dark"
        
        self.current_theme_name = theme_name
        self.theme_changed.emit(theme_name)
        self.save_settings()
    
    def get_theme(self) -> ThemeColors:
        """Get current theme colors"""
        return self.current_theme
    
    def apply_theme_to_palette(self, palette: QPalette):
        """Apply theme colors to QPalette"""
        colors = self.current_theme
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(colors.window_bg))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.window_fg))
        
        # Base colors
        palette.setColor(QPalette.ColorRole.Base, QColor(colors.base_bg))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors.base_fg))
        
        # Alternate colors
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.alternate_bg))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(colors.button_bg))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.button_fg))
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.highlight))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.highlight_text))
        
        # Link colors
        palette.setColor(QPalette.ColorRole.Link, QColor(colors.link))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(colors.link_visited))
        
        # Tooltip colors
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.tooltip_bg))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.tooltip_fg))
    
    def save_custom_theme(self, name: str, colors: ThemeColors):
        """Save a custom theme"""
        self.custom_themes[name] = colors
        self.save_settings()
    
    def delete_custom_theme(self, name: str):
        """Delete a custom theme"""
        if name in self.custom_themes:
            del self.custom_themes[name]
            self.save_settings()
    
    def get_available_themes(self) -> list:
        """Get list of available theme names"""
        themes = ["dark", "light", "high_contrast"]
        themes.extend(self.custom_themes.keys())
        return themes

