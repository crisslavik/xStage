"""
Scene Graph Search & Filter UI
Search and filter interface for USD scene graph
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QComboBox, QGroupBox,
    QCheckBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, List

from .scene_search import SceneSearchManager


class SceneSearchWidget(QWidget):
    """Widget for searching and filtering scene graph"""
    
    selection_changed = Signal(str)  # Emits prim path when selection changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_manager = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Scene Search & Filter</b>")
        layout.addWidget(title)
        
        # Search box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search prims...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Name", "Path", "Type", "All"])
        self.search_type_combo.currentTextChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_type_combo)
        
        layout.addLayout(search_layout)
        
        # Filter options
        filter_group = QGroupBox("Filters")
        filter_layout = QVBoxLayout()
        
        # Type filter
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItem("All")
        self.type_filter_combo.currentTextChanged.connect(self.apply_filters)
        type_layout.addWidget(self.type_filter_combo)
        filter_layout.addLayout(type_layout)
        
        # Metadata filter
        metadata_layout = QHBoxLayout()
        metadata_layout.addWidget(QLabel("Metadata:"))
        self.metadata_key_combo = QComboBox()
        self.metadata_key_combo.addItem("None")
        self.metadata_key_combo.currentTextChanged.connect(self.apply_filters)
        metadata_layout.addWidget(self.metadata_key_combo)
        
        self.metadata_value_edit = QLineEdit()
        self.metadata_value_edit.setPlaceholderText("Value (optional)")
        self.metadata_value_edit.textChanged.connect(self.apply_filters)
        metadata_layout.addWidget(self.metadata_value_edit)
        filter_layout.addLayout(metadata_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Results
        results_label = QLabel("Results:")
        layout.addWidget(results_label)
        
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Prim", "Type", "Path"])
        self.results_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.results_tree)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        layout.addWidget(clear_btn)
        
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        if stage:
            self.search_manager = SceneSearchManager(stage)
            self.refresh_filters()
        else:
            self.search_manager = None
            self.clear()
    
    def refresh_filters(self):
        """Refresh filter options"""
        if not self.search_manager:
            return
        
        # Update type filter
        self.type_filter_combo.clear()
        self.type_filter_combo.addItem("All")
        types = self.search_manager.get_prim_types()
        self.type_filter_combo.addItems(types)
        
        # Update metadata filter
        self.metadata_key_combo.clear()
        self.metadata_key_combo.addItem("None")
        metadata_keys = self.search_manager.get_metadata_keys()
        self.metadata_key_combo.addItems(metadata_keys)
    
    def on_search_changed(self):
        """Handle search text change"""
        self.apply_filters()
    
    def apply_filters(self):
        """Apply all filters and update results"""
        self.results_tree.clear()
        
        if not self.search_manager:
            return
        
        # Get search query
        query = self.search_input.text()
        search_type = self.search_type_combo.currentText().lower()
        
        # Perform search
        if query:
            results = self.search_manager.search_prims(query, search_type)
        else:
            # No search, get all prims
            results = list(self.search_manager.stage.Traverse())
        
        # Apply type filter
        type_filter = self.type_filter_combo.currentText()
        if type_filter != "All":
            results = [p for p in results if p.GetTypeName() == type_filter]
        
        # Apply metadata filter
        metadata_key = self.metadata_key_combo.currentText()
        if metadata_key != "None":
            metadata_value = self.metadata_value_edit.text()
            if metadata_value:
                results = self.search_manager.filter_by_metadata(metadata_key, metadata_value)
            else:
                results = self.search_manager.filter_by_metadata(metadata_key)
        
        # Display results
        for prim in results:
            item = QTreeWidgetItem([
                prim.GetName(),
                prim.GetTypeName(),
                prim.GetPath().pathString
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, prim.GetPath().pathString)
            self.results_tree.addTopLevelItem(item)
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double-click"""
        prim_path = item.data(0, Qt.ItemDataRole.UserRole)
        if prim_path:
            self.selection_changed.emit(prim_path)
    
    def clear(self):
        """Clear search and results"""
        self.search_input.clear()
        self.results_tree.clear()

