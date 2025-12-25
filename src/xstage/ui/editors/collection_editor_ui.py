"""
Collection Editor UI
Edit collection membership and properties
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QLineEdit, QComboBox, QGroupBox, QFormLayout,
    QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from typing import Optional

from ...managers.collections import CollectionManager


class CollectionEditorWidget(QWidget):
    """Widget for editing collections"""
    
    collection_changed = Signal(str)  # Emits collection name when changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.current_collection_api = None
        self.current_prim = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Collection Editor</b>")
        layout.addWidget(title)
        
        # Collection list
        list_label = QLabel("Collections:")
        layout.addWidget(list_label)
        
        self.collection_tree = QTreeWidget()
        self.collection_tree.setHeaderLabels(["Collection", "Mode", "Prim"])
        self.collection_tree.itemSelectionChanged.connect(self.on_collection_selected)
        layout.addWidget(self.collection_tree)
        
        # Collection properties
        props_group = QGroupBox("Collection Properties")
        props_layout = QFormLayout()
        
        self.collection_name_label = QLabel("No collection selected")
        props_layout.addRow("Collection:", self.collection_name_label)
        
        self.expansion_rule_combo = QComboBox()
        self.expansion_rule_combo.addItems(["explicitOnly", "expandPrims", "expandPrimsAndProperties"])
        self.expansion_rule_combo.currentTextChanged.connect(self.on_property_changed)
        props_layout.addRow("Expansion Rule:", self.expansion_rule_combo)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        # Members
        members_group = QGroupBox("Collection Members")
        members_layout = QVBoxLayout()
        
        self.members_list = QListWidget()
        members_layout.addWidget(self.members_list)
        
        member_buttons = QHBoxLayout()
        add_btn = QPushButton("Add Prim")
        add_btn.clicked.connect(self.add_member)
        member_buttons.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_member)
        member_buttons.addWidget(remove_btn)
        
        members_layout.addLayout(member_buttons)
        members_group.setLayout(members_layout)
        layout.addWidget(members_group)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        self.stage = stage
        self.refresh()
    
    def refresh(self):
        """Refresh collection list"""
        self.collection_tree.clear()
        
        if not self.stage:
            return
        
        # Find all collections
        for prim in self.stage.Traverse():
            collections = CollectionManager.get_collections(prim)
            if collections:
                for collection_data in collections:
                    item = QTreeWidgetItem([
                        collection_data['name'],
                        collection_data['mode'],
                        prim.GetPath().pathString
                    ])
                    item.setData(0, Qt.ItemDataRole.UserRole, {
                        'prim_path': prim.GetPath().pathString,
                        'collection_name': collection_data['name'],
                    })
                    self.collection_tree.addTopLevelItem(item)
    
    def on_collection_selected(self):
        """Handle collection selection"""
        selected = self.collection_tree.currentItem()
        if not selected:
            return
        
        data = selected.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        # Get prim and collection
        prim = self.stage.GetPrimAtPath(data['prim_path'])
        if not prim:
            return
        
        self.current_prim = prim
        
        # Get collection API
        from pxr import UsdCollectionAPI
        self.current_collection_api = UsdCollectionAPI(prim, data['collection_name'])
        
        # Load collection properties
        collection = self.current_collection_api.GetCollection()
        self.collection_name_label.setText(f"{data['collection_name']} on {prim.GetName()}")
        
        expansion_rule = str(collection.GetExpansionRule())
        index = self.expansion_rule_combo.findText(expansion_rule)
        if index >= 0:
            self.expansion_rule_combo.setCurrentIndex(index)
        
        # Load members
        self.members_list.clear()
        includes = collection.GetIncludesRel().GetTargets()
        for target in includes:
            self.members_list.addItem(str(target))
    
    def on_property_changed(self):
        """Handle property change"""
        if not self.current_collection_api:
            return
        
        expansion_rule = self.expansion_rule_combo.currentText()
        collection = self.current_collection_api.GetCollection()
        collection.SetExpansionRule(expansion_rule)
        self.collection_changed.emit(self.current_collection_api.GetCollectionName())
    
    def add_member(self):
        """Add a prim to the collection"""
        if not self.current_collection_api:
            return
        
        from PySide6.QtWidgets import QInputDialog
        prim_path, ok = QInputDialog.getText(self, "Add Prim", "Prim path:")
        if ok and prim_path:
            from pxr import Sdf
            CollectionManager.add_to_collection(
                self.current_collection_api, Sdf.Path(prim_path)
            )
            self.on_collection_selected()  # Refresh
    
    def remove_member(self):
        """Remove selected member from collection"""
        if not self.current_collection_api:
            return
        
        selected = self.members_list.currentItem()
        if selected:
            from pxr import Sdf
            CollectionManager.remove_from_collection(
                self.current_collection_api, Sdf.Path(selected.text())
            )
            self.on_collection_selected()  # Refresh

