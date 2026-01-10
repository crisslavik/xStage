"""
OCIO Settings UI
Color management configuration dialog
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QGroupBox, QFormLayout, QComboBox,
    QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt

try:
    from ...utils.ocio_manager import OCIOManager
    OCIO_AVAILABLE = True
except ImportError:
    OCIO_AVAILABLE = False
    OCIOManager = None


class OCIOSettingsDialog(QDialog):
    """Dialog for configuring OpenColorIO settings"""
    
    def __init__(self, parent=None, ocio_manager: Optional[OCIOManager] = None):
        super().__init__(parent)
        self.ocio_manager = ocio_manager
        self.config_path = None
        self.init_ui()
        
        if self.ocio_manager:
            self.load_current_settings()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("OCIO Color Management Settings")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<h2>OpenColorIO (OCIO) Settings</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Info
        info_label = QLabel(
            "Configure color management for accurate asset review.\n"
            "OCIO ensures colors match other VFX tools (Nuke, Houdini, Maya, Blender)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info_label)
        
        # OCIO Status
        status_group = QGroupBox("OCIO Status")
        status_layout = QFormLayout()
        
        self.ocio_status_label = QLabel("Checking...")
        status_layout.addRow("Status:", self.ocio_status_label)
        
        self.config_name_label = QLabel("None")
        status_layout.addRow("Current Config:", self.config_name_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Config Selection
        config_group = QGroupBox("OCIO Config File")
        config_layout = QVBoxLayout()
        
        # Config path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Config File:"))
        
        self.config_path_edit = QLineEdit()
        self.config_path_edit.setPlaceholderText("Leave empty to use default/ACES")
        self.config_path_edit.setReadOnly(True)
        path_layout.addWidget(self.config_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_config_file)
        path_layout.addWidget(browse_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_config_file)
        path_layout.addWidget(clear_btn)
        
        config_layout.addLayout(path_layout)
        
        # Info about config
        config_info = QLabel(
            "Select an OCIO config file (.ocio) or leave empty to use:\n"
            "• OCIO environment variable (if set)\n"
            "• ACES 1.2/1.3 (if available)\n"
            "• Raw config (fallback)"
        )
        config_info.setWordWrap(True)
        config_info.setStyleSheet("color: gray; font-size: 9px; padding: 5px;")
        config_layout.addWidget(config_info)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Color Space Info
        if self.ocio_manager and self.ocio_manager.is_available():
            color_space_group = QGroupBox("Available Color Spaces")
            color_space_layout = QVBoxLayout()
            
            self.color_space_list = QTextEdit()
            self.color_space_list.setReadOnly(True)
            self.color_space_list.setMaximumHeight(150)
            color_space_layout.addWidget(self.color_space_list)
            
            color_space_group.setLayout(color_space_layout)
            layout.addWidget(color_space_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_current_settings(self):
        """Load current OCIO settings"""
        if not self.ocio_manager:
            self.ocio_status_label.setText("OCIO Manager not available")
            self.ocio_status_label.setStyleSheet("color: red;")
            return
        
        if self.ocio_manager.is_available():
            version_info = self.ocio_manager.get_version_info()
            version_str = version_info.get('version_string', 'Unknown')
            self.ocio_status_label.setText(f"✓ Available (OCIO {version_str})")
            self.ocio_status_label.setStyleSheet("color: green;")
            
            config_name = self.ocio_manager.get_config_name()
            self.config_name_label.setText(config_name)
            
            # Show available color spaces
            if hasattr(self, 'color_space_list'):
                color_spaces = self.ocio_manager.get_available_color_spaces()
                if color_spaces:
                    self.color_space_list.setText("\n".join(color_spaces[:50]))  # Show first 50
                else:
                    self.color_space_list.setText("No color spaces available")
        else:
            self.ocio_status_label.setText("✗ Not Available")
            self.ocio_status_label.setStyleSheet("color: red;")
            self.config_name_label.setText("Install PyOpenColorIO")
    
    def browse_config_file(self):
        """Browse for OCIO config file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select OCIO Config File",
            "",
            "OCIO Config Files (*.ocio);;All Files (*)"
        )
        
        if filepath:
            self.config_path_edit.setText(filepath)
            self.config_path = filepath
    
    def clear_config_file(self):
        """Clear config file selection"""
        self.config_path_edit.clear()
        self.config_path = None
    
    def apply_settings(self):
        """Apply OCIO settings"""
        if not self.ocio_manager:
            QMessageBox.warning(self, "OCIO Not Available", 
                              "OCIO Manager is not available.")
            return
        
        # Reload config if path changed
        if self.config_path != self.ocio_manager.config_path:
            success = self.ocio_manager.load_config(self.config_path)
            if success:
                QMessageBox.information(self, "Settings Applied", 
                                      f"OCIO config loaded: {self.ocio_manager.get_config_name()}")
                self.accept()
            else:
                QMessageBox.warning(self, "Config Load Failed", 
                                  "Failed to load OCIO config. Check the file path.")
        else:
            self.accept()
    
    def get_config_path(self) -> Optional[str]:
        """Get selected config path"""
        return self.config_path

