"""
Preferences/Settings Dialog
User preferences and configuration
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QLineEdit, QFileDialog, QGroupBox,
    QFormLayout, QCheckBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QSettings
from typing import Optional
from pathlib import Path


class PreferencesDialog(QDialog):
    """Preferences/Settings dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("xStage", "xStage")
        self.setWindowTitle("Preferences")
        self.setMinimumSize(600, 500)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Tab widget for different preference categories
        tabs = QTabWidget()
        
        # OCIO Preferences Tab
        ocio_tab = self.create_ocio_tab()
        tabs.addTab(ocio_tab, "Color Management (OCIO)")
        
        # Add more tabs as needed
        # tabs.addTab(self.create_general_tab(), "General")
        # tabs.addTab(self.create_viewport_tab(), "Viewport")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_and_save)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_ocio_tab(self) -> QWidget:
        """Create OCIO preferences tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "Configure OpenColorIO (OCIO) settings.\n"
            "• Use bundled PyOpenColorIO (default) - works out of the box\n"
            "• Custom OCIO library path - point to company's OCIO installation\n"
            "• OCIO config file - specify which .ocio config file to use\n"
            "• Use OCIO environment variable - respect $OCIO if set"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info_label)
        
        # OCIO Library Path
        ocio_group = QGroupBox("OCIO Library Configuration")
        ocio_layout = QFormLayout()
        
        # Use bundled vs custom
        self.use_bundled_ocio = QCheckBox("Use bundled PyOpenColorIO")
        self.use_bundled_ocio.setChecked(True)
        self.use_bundled_ocio.toggled.connect(self.on_ocio_source_changed)
        ocio_layout.addRow("", self.use_bundled_ocio)
        
        # Custom OCIO path
        custom_path_layout = QHBoxLayout()
        self.custom_ocio_path_edit = QLineEdit()
        self.custom_ocio_path_edit.setPlaceholderText("Path to custom OCIO library directory")
        self.custom_ocio_path_edit.setEnabled(False)
        custom_path_layout.addWidget(self.custom_ocio_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_ocio_path)
        browse_btn.setEnabled(False)
        self.browse_ocio_btn = browse_btn
        custom_path_layout.addWidget(browse_btn)
        
        ocio_layout.addRow("Custom OCIO Path:", custom_path_layout)
        
        # OCIO Config File Path (separate from library)
        self.ocio_config_path_edit = QLineEdit()
        self.ocio_config_path_edit.setPlaceholderText("Path to OCIO config file (.ocio)")
        config_path_layout = QHBoxLayout()
        config_path_layout.addWidget(self.ocio_config_path_edit)
        
        browse_config_btn = QPushButton("Browse...")
        browse_config_btn.clicked.connect(self.browse_ocio_config)
        config_path_layout.addWidget(browse_config_btn)
        
        ocio_layout.addRow("OCIO Config File:", config_path_layout)
        
        # Environment variable option
        self.use_ocio_env = QCheckBox("Use OCIO environment variable (if set)")
        self.use_ocio_env.setChecked(True)
        ocio_layout.addRow("", self.use_ocio_env)
        
        ocio_group.setLayout(ocio_layout)
        layout.addWidget(ocio_group)
        
        # Current Status
        status_group = QGroupBox("Current Status")
        status_layout = QFormLayout()
        
        self.ocio_status_label = QLabel("Not checked")
        status_layout.addRow("OCIO Status:", self.ocio_status_label)
        
        self.ocio_version_label = QLabel("-")
        status_layout.addRow("OCIO Version:", self.ocio_version_label)
        
        test_btn = QPushButton("Test OCIO Configuration")
        test_btn.clicked.connect(self.test_ocio)
        status_layout.addRow("", test_btn)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def on_ocio_source_changed(self, checked: bool):
        """Handle OCIO source change"""
        self.custom_ocio_path_edit.setEnabled(not checked)
        self.browse_ocio_btn.setEnabled(not checked)
    
    def browse_ocio_path(self):
        """Browse for custom OCIO library directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select OCIO Library Directory",
            self.custom_ocio_path_edit.text() or str(Path.home())
        )
        if directory:
            self.custom_ocio_path_edit.setText(directory)
    
    def browse_ocio_config(self):
        """Browse for OCIO config file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select OCIO Config File",
            self.ocio_config_path_edit.text() or str(Path.home()),
            "OCIO Config Files (*.ocio);;All Files (*)"
        )
        if filepath:
            self.ocio_config_path_edit.setText(filepath)
    
    def test_ocio(self):
        """Test OCIO configuration"""
        try:
            from ..utils.ocio_manager import OCIOManager
            
            # Get settings
            use_bundled = self.use_bundled_ocio.isChecked()
            custom_path = self.custom_ocio_path_edit.text().strip() if not use_bundled else None
            config_path = self.ocio_config_path_edit.text().strip() or None
            use_env = self.use_ocio_env.isChecked()
            
            # Check for custom OCIO library path
            if custom_path and not use_bundled:
                # Note: Custom OCIO library loading requires:
                # 1. Setting LD_LIBRARY_PATH (Linux) or DYLD_LIBRARY_PATH (macOS) or PATH (Windows)
                # 2. Or using ctypes to load the library before importing PyOpenColorIO
                # For now, we'll show a message about this
                QMessageBox.information(
                    self,
                    "Custom OCIO Library Path",
                    "Custom OCIO library path is saved in preferences.\n\n"
                    "To use a custom OCIO library:\n"
                    "1. Set environment variable before launching xStage:\n"
                    "   - Linux: export LD_LIBRARY_PATH=/path/to/ocio/lib:$LD_LIBRARY_PATH\n"
                    "   - macOS: export DYLD_LIBRARY_PATH=/path/to/ocio/lib:$DYLD_LIBRARY_PATH\n"
                    "   - Windows: Add to PATH\n"
                    "2. Or restart xStage after setting the path\n\n"
                    "The OCIO config file path can be set independently."
                )
            
            # Test with bundled OCIO (or custom if env is set)
            # If use_env is checked, it will use OCIO env var if set
            if use_env and not config_path:
                # Let OCIOManager use environment variable
                manager = OCIOManager(config_path=None)
            else:
                manager = OCIOManager(config_path=config_path)
            
            if manager.is_available():
                version_info = manager.get_version_info()
                self.ocio_status_label.setText("✓ Available")
                self.ocio_status_label.setStyleSheet("color: green;")
                self.ocio_version_label.setText(version_info.get('version_string', 'Unknown'))
                
                QMessageBox.information(
                    self,
                    "OCIO Test Successful",
                    f"OCIO is working correctly!\n\n"
                    f"Version: {version_info.get('version_string', 'Unknown')}\n"
                    f"Config: {manager.get_config_name()}"
                )
            else:
                self.ocio_status_label.setText("✗ Not Available")
                self.ocio_status_label.setStyleSheet("color: red;")
                self.ocio_version_label.setText("-")
                
                QMessageBox.warning(
                    self,
                    "OCIO Test Failed",
                    "OCIO is not available.\n\n"
                    "Install with: pip install PyOpenColorIO"
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Test Error",
                f"Error testing OCIO:\n{e}"
            )
    
    def load_settings(self):
        """Load settings from QSettings"""
        # OCIO settings
        use_bundled = self.settings.value("ocio/use_bundled", True, type=bool)
        custom_path = self.settings.value("ocio/custom_path", "", type=str)
        config_path = self.settings.value("ocio/config_path", "", type=str)
        use_env = self.settings.value("ocio/use_env", True, type=bool)
        
        self.use_bundled_ocio.setChecked(use_bundled)
        self.custom_ocio_path_edit.setText(custom_path)
        self.ocio_config_path_edit.setText(config_path)
        self.use_ocio_env.setChecked(use_env)
        
        self.on_ocio_source_changed(use_bundled)
    
    def apply_settings(self):
        """Apply settings without closing dialog"""
        self.save_settings()
        QMessageBox.information(
            self,
            "Settings Applied",
            "Settings have been saved.\n\n"
            "Restart xStage for OCIO library path changes to take effect."
        )
    
    def accept_and_save(self):
        """Save settings and close"""
        self.save_settings()
        self.accept()
    
    def save_settings(self):
        """Save settings to QSettings"""
        # OCIO settings
        self.settings.setValue("ocio/use_bundled", self.use_bundled_ocio.isChecked())
        self.settings.setValue("ocio/custom_path", self.custom_ocio_path_edit.text())
        self.settings.setValue("ocio/config_path", self.ocio_config_path_edit.text())
        self.settings.setValue("ocio/use_env", self.use_ocio_env.isChecked())
        
        self.settings.sync()

