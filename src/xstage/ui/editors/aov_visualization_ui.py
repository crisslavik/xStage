"""
AOV Visualization UI
Display and manage AOVs (Render Vars)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
    QComboBox, QCheckBox, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from typing import Optional

from ...managers.aov_manager import AOVManager, AOVDisplayMode


class AOVVisualizationWidget(QWidget):
    """Widget for AOV visualization"""
    
    aov_selected = Signal(str)  # Emits AOV name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aov_manager = AOVManager()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>AOV (Render Var) Visualization</b>")
        layout.addWidget(title)
        
        # Splitter for side-by-side layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: AOV list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        list_label = QLabel("Available AOVs:")
        left_layout.addWidget(list_label)
        
        self.aov_list = QListWidget()
        self.aov_list.itemSelectionChanged.connect(self.on_aov_selected)
        left_layout.addWidget(self.aov_list)
        
        # AOV controls
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout()
        
        enable_btn = QPushButton("Enable Selected")
        enable_btn.clicked.connect(self.enable_selected)
        controls_layout.addWidget(enable_btn)
        
        disable_btn = QPushButton("Disable Selected")
        disable_btn.clicked.connect(self.disable_selected)
        controls_layout.addWidget(disable_btn)
        
        refresh_btn = QPushButton("Refresh AOVs")
        refresh_btn.clicked.connect(self.refresh_aovs)
        controls_layout.addWidget(refresh_btn)
        
        controls_group.setLayout(controls_layout)
        left_layout.addWidget(controls_group)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # Right panel: AOV preview
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        preview_label = QLabel("AOV Preview:")
        right_layout.addWidget(preview_label)
        
        # Preview area (placeholder - would show AOV image)
        self.preview_widget = QLabel("AOV preview will appear here")
        self.preview_widget.setMinimumSize(400, 300)
        self.preview_widget.setStyleSheet("background-color: #1e1e1e; border: 1px solid #555;")
        self.preview_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.preview_widget)
        
        # Display mode
        mode_group = QGroupBox("Display Mode")
        mode_layout = QFormLayout()
        
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["RGB", "Grayscale", "Heatmap", "False Color"])
        self.display_mode_combo.currentIndexChanged.connect(self.on_display_mode_changed)
        mode_layout.addRow("Mode:", self.display_mode_combo)
        
        mode_group.setLayout(mode_layout)
        right_layout.addWidget(mode_group)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout()
        
        self.stats_labels = {}
        for key in ['total_aovs', 'enabled_aovs', 'disabled_aovs']:
            label = QLabel("0")
            self.stats_labels[key] = label
            stats_layout.addRow(key.replace('_', ' ').title() + ":", label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set USD stage"""
        self.aov_manager.stage = stage
        self.refresh_aovs()
    
    def refresh_aovs(self):
        """Refresh AOV list"""
        self.aov_manager.extract_aovs()
        self.aov_list.clear()
        
        for aov in self.aov_manager.get_aov_list():
            item_text = f"{aov.name} ({aov.data_type})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, aov.name)
            item.setCheckState(Qt.CheckState.Checked if aov.enabled else Qt.CheckState.Unchecked)
            self.aov_list.addItem(item)
        
        self.update_statistics()
    
    def on_aov_selected(self):
        """Handle AOV selection"""
        selected = self.aov_list.currentItem()
        if selected:
            aov_name = selected.data(Qt.ItemDataRole.UserRole)
            aov = self.aov_manager.get_aov_by_name(aov_name)
            if aov:
                self.preview_widget.setText(f"Preview: {aov.name}\nType: {aov.data_type}\nSource: {aov.source_name}")
                self.aov_selected.emit(aov_name)
    
    def enable_selected(self):
        """Enable selected AOVs"""
        for item in self.aov_list.selectedItems():
            aov_name = item.data(Qt.ItemDataRole.UserRole)
            self.aov_manager.enable_aov(aov_name, True)
            item.setCheckState(Qt.CheckState.Checked)
        self.update_statistics()
    
    def disable_selected(self):
        """Disable selected AOVs"""
        for item in self.aov_list.selectedItems():
            aov_name = item.data(Qt.ItemDataRole.UserRole)
            self.aov_manager.enable_aov(aov_name, False)
            item.setCheckState(Qt.CheckState.Unchecked)
        self.update_statistics()
    
    def on_display_mode_changed(self, index):
        """Handle display mode change"""
        modes = [AOVDisplayMode.RGB, AOVDisplayMode.GRAYSCALE, 
                AOVDisplayMode.HEATMAP, AOVDisplayMode.FALSE_COLOR]
        if 0 <= index < len(modes):
            self.aov_manager.set_display_mode(modes[index])
    
    def update_statistics(self):
        """Update statistics display"""
        stats = self.aov_manager.get_aov_statistics()
        for key, label in self.stats_labels.items():
            if key in stats:
                label.setText(str(stats[key]))

