"""
Viewport Header Widget
Professional viewport controls like Omniverse (camera selector, view buttons)
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QPushButton, QButtonGroup, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from typing import Optional, List
import numpy as np

try:
    from pxr import Usd, UsdGeom
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class ViewportHeader(QWidget):
    """Viewport header with camera and view controls (Omniverse-style)"""
    
    # Signals
    camera_changed = Signal(str)  # Emits camera path or "Perspective"
    view_changed = Signal(str)  # Emits view name: "Perspective", "Top", "Front", etc.
    overlay_toggled = Signal(bool)  # Emits overlay visibility state
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.current_camera = "Perspective"
        self.current_view = "Perspective"
        self.cameras = []  # List of USD camera prims
        self.overlay_visible = True  # Default: overlay visible
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Camera selector label
        camera_label = QLabel("Camera:")
        camera_label.setStyleSheet("color: palette(window-text); font-weight: bold;")
        layout.addWidget(camera_label)
        
        # Camera dropdown
        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumWidth(150)
        self.camera_combo.setStyleSheet("""
            QComboBox {
                background-color: palette(button);
                color: palette(button-text);
                border: 1px solid palette(mid);
                border-radius: 3px;
                padding: 3px 8px;
            }
            QComboBox:hover {
                border: 1px solid palette(highlight);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.camera_combo.currentTextChanged.connect(self.on_camera_changed)
        layout.addWidget(self.camera_combo)
        
        layout.addSpacing(10)
        
        # View buttons group (like Omniverse)
        view_label = QLabel("View:")
        view_label.setStyleSheet("color: palette(window-text); font-weight: bold;")
        layout.addWidget(view_label)
        
        self.view_button_group = QButtonGroup(self)
        self.view_button_group.setExclusive(True)
        
        # View buttons
        views = [
            ("Perspective", "Perspective"),
            ("Top", "Top"),
            ("Front", "Front"),
            ("Left", "Left"),
            ("Back", "Back"),
            ("Right", "Right"),
        ]
        
        for view_name, tooltip in views:
            btn = QPushButton(view_name)
            btn.setCheckable(True)
            btn.setToolTip(f"Switch to {tooltip} view")
            btn.setFixedHeight(24)
            btn.setMinimumWidth(60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: palette(button);
                    color: palette(button-text);
                    border: 1px solid palette(mid);
                    border-radius: 3px;
                    padding: 2px 8px;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: palette(button);
                    border: 1px solid palette(highlight);
                }
                QPushButton:checked {
                    background-color: palette(highlight);
                    color: palette(highlighted-text);
                    border: 1px solid palette(highlight);
                }
            """)
            self.view_button_group.addButton(btn)
            btn.clicked.connect(lambda checked, v=view_name: self.on_view_changed(v) if checked else None)
            layout.addWidget(btn)
        
        # Set Perspective as default
        if self.view_button_group.buttons():
            self.view_button_group.buttons()[0].setChecked(True)
        
        layout.addSpacing(20)
        
        # Overlay toggle (show/hide FPS, stats, etc.)
        overlay_label = QLabel("Info:")
        overlay_label.setStyleSheet("color: palette(window-text); font-weight: bold;")
        layout.addWidget(overlay_label)
        
        self.overlay_checkbox = QCheckBox("Show Info")
        self.overlay_checkbox.setChecked(True)  # Default: visible
        self.overlay_checkbox.setToolTip("Toggle viewport overlay information (FPS, stats, etc.)")
        self.overlay_checkbox.setStyleSheet("""
            QCheckBox {
                color: palette(window-text);
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid palette(mid);
                border-radius: 3px;
                background-color: palette(base);
            }
            QCheckBox::indicator:checked {
                background-color: palette(highlight);
                border: 1px solid palette(highlight);
            }
            QCheckBox::indicator:hover {
                border: 1px solid palette(highlight);
            }
        """)
        self.overlay_checkbox.toggled.connect(self.on_overlay_toggled)
        layout.addWidget(self.overlay_checkbox)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedHeight(32)
        
        # Style the header background
        self.setStyleSheet("""
            ViewportHeader {
                background-color: palette(base);
                border-bottom: 1px solid palette(mid);
            }
        """)
    
    def set_stage(self, stage):
        """Set USD stage and update camera list"""
        self.stage = stage
        self.update_camera_list()
    
    def update_camera_list(self):
        """Update camera dropdown with USD cameras"""
        # Check if widget still exists before accessing
        if not self.camera_combo or not hasattr(self.camera_combo, 'clear'):
            return
        
        try:
            self.camera_combo.clear()
        except RuntimeError:
            # Widget already deleted
            return
        
        # Always add Perspective (free camera)
        self.camera_combo.addItem("Perspective", "Perspective")
        
        if not USD_AVAILABLE or not self.stage:
            return
        
        # Find all cameras in stage
        self.cameras = []
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Camera):
                camera_name = prim.GetName()
                camera_path = prim.GetPath().pathString
                self.cameras.append(prim)
                self.camera_combo.addItem(camera_name, camera_path)
    
    def on_camera_changed(self, text):
        """Handle camera selection change"""
        if not text:
            return
        
        camera_data = self.camera_combo.currentData()
        if camera_data:
            self.current_camera = camera_data
            self.camera_changed.emit(camera_data)
    
    def on_view_changed(self, view_name):
        """Handle view button click"""
        self.current_view = view_name
        self.view_changed.emit(view_name)
    
    def set_current_view(self, view_name):
        """Programmatically set current view"""
        self.current_view = view_name
        for btn in self.view_button_group.buttons():
            if btn.text() == view_name:
                btn.setChecked(True)
                break
    
    def on_overlay_toggled(self, checked: bool):
        """Handle overlay visibility toggle"""
        self.overlay_visible = checked
        self.overlay_toggled.emit(checked)
    
    def set_overlay_visible(self, visible: bool):
        """Programmatically set overlay visibility"""
        self.overlay_checkbox.setChecked(visible)
        self.overlay_visible = visible
