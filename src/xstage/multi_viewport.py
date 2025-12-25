"""
Multi-Viewport Support
Multiple synchronized viewports for professional workflow
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QComboBox,
    QLabel, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, List

from .viewer import USDStageManager
from .viewport import ViewportWidget
from .hydra_viewport import HydraViewportWidget


class MultiViewportWidget(QWidget):
    """Widget with multiple synchronized viewports"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage_manager = None
        self.viewports = []
        self.viewport_types = []  # 'perspective', 'top', 'front', 'side'
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Viewport layout selector
        layout_selector = QHBoxLayout()
        layout_selector.addWidget(QLabel("Layout:"))
        
        self.layout_combo = QComboBox()
        self.layout_combo.addItems([
            "Single Viewport",
            "Two Views (Horizontal)",
            "Two Views (Vertical)",
            "Four Views",
        ])
        self.layout_combo.currentTextChanged.connect(self.change_layout)
        layout_selector.addWidget(self.layout_combo)
        
        layout_selector.addStretch()
        layout.addLayout(layout_selector)
        
        # Viewport container
        self.viewport_container = QWidget()
        self.viewport_layout = QHBoxLayout()
        self.viewport_layout.setContentsMargins(0, 0, 0, 0)
        self.viewport_container.setLayout(self.viewport_layout)
        layout.addWidget(self.viewport_container)
        
        # Initialize with single viewport
        self.change_layout("Single Viewport")
        
        self.setLayout(layout)
    
    def set_stage_manager(self, manager: USDStageManager):
        """Set the USD stage manager"""
        self.stage_manager = manager
        for viewport in self.viewports:
            viewport.set_stage_manager(manager)
    
    def change_layout(self, layout_name: str):
        """Change viewport layout"""
        # Clear existing viewports
        for viewport in self.viewports:
            viewport.setParent(None)
            viewport.deleteLater()
        
        self.viewports = []
        self.viewport_types = []
        
        # Clear layout
        while self.viewport_layout.count():
            item = self.viewport_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if layout_name == "Single Viewport":
            viewport = ViewportWidget()
            viewport.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport)
            self.viewport_types.append('perspective')
            self.viewport_layout.addWidget(viewport)
        
        elif layout_name == "Two Views (Horizontal)":
            splitter = QSplitter(Qt.Orientation.Horizontal)
            
            viewport1 = ViewportWidget()
            viewport1.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport1)
            self.viewport_types.append('perspective')
            splitter.addWidget(viewport1)
            
            viewport2 = ViewportWidget()
            viewport2.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport2)
            self.viewport_types.append('top')
            splitter.addWidget(viewport2)
            
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 1)
            self.viewport_layout.addWidget(splitter)
        
        elif layout_name == "Two Views (Vertical)":
            splitter = QSplitter(Qt.Orientation.Vertical)
            
            viewport1 = ViewportWidget()
            viewport1.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport1)
            self.viewport_types.append('perspective')
            splitter.addWidget(viewport1)
            
            viewport2 = ViewportWidget()
            viewport2.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport2)
            self.viewport_types.append('top')
            splitter.addWidget(viewport2)
            
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 1)
            self.viewport_layout.addWidget(splitter)
        
        elif layout_name == "Four Views":
            # Top splitter
            top_splitter = QSplitter(Qt.Orientation.Horizontal)
            
            viewport1 = ViewportWidget()
            viewport1.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport1)
            self.viewport_types.append('perspective')
            top_splitter.addWidget(viewport1)
            
            viewport2 = ViewportWidget()
            viewport2.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport2)
            self.viewport_types.append('top')
            top_splitter.addWidget(viewport2)
            
            # Bottom splitter
            bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
            
            viewport3 = ViewportWidget()
            viewport3.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport3)
            self.viewport_types.append('front')
            bottom_splitter.addWidget(viewport3)
            
            viewport4 = ViewportWidget()
            viewport4.set_stage_manager(self.stage_manager)
            self.viewports.append(viewport4)
            self.viewport_types.append('side')
            bottom_splitter.addWidget(viewport4)
            
            # Main splitter
            main_splitter = QSplitter(Qt.Orientation.Vertical)
            main_splitter.addWidget(top_splitter)
            main_splitter.addWidget(bottom_splitter)
            main_splitter.setStretchFactor(0, 1)
            main_splitter.setStretchFactor(1, 1)
            
            self.viewport_layout.addWidget(main_splitter)
    
    def update_geometry(self, time_code: float):
        """Update all viewports"""
        for viewport in self.viewports:
            viewport.update_geometry(time_code)
    
    def get_viewport(self, index: int = 0) -> Optional[ViewportWidget]:
        """Get a specific viewport"""
        if 0 <= index < len(self.viewports):
            return self.viewports[index]
        return None

