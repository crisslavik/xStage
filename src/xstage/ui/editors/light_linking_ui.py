"""
Light Linking UI
Interactive UI for managing light linking relationships
Based on USD 25.11 UsdLux.LightListAPI specifications
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QGroupBox, QFormLayout, QListWidget,
    QListWidgetItem, QMessageBox, QSplitter, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, List

try:
    from pxr import Usd, UsdLux, UsdGeom
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class LightLinkingWidget(QWidget):
    """Widget for managing light linking"""
    
    linking_changed = Signal()  # Emits when light links change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.light_linking_manager = None
        self.current_light_prim = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Light Linking</b>")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        info_label = QLabel(
            "Light linking controls which objects are affected by which lights.\n"
            "Select a light to see and manage its linked objects."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_label)
        
        # Splitter for light list and linked objects
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Light selection
        light_group = QGroupBox("Lights")
        light_layout = QVBoxLayout()
        
        self.light_list = QListWidget()
        self.light_list.itemSelectionChanged.connect(self.on_light_selected)
        light_layout.addWidget(self.light_list)
        
        refresh_lights_btn = QPushButton("Refresh Lights")
        refresh_lights_btn.clicked.connect(self.refresh_lights)
        light_layout.addWidget(refresh_lights_btn)
        
        light_group.setLayout(light_layout)
        splitter.addWidget(light_group)
        
        # Right: Linked objects
        linked_group = QGroupBox("Linked Objects")
        linked_layout = QVBoxLayout()
        
        self.linked_objects_tree = QTreeWidget()
        self.linked_objects_tree.setHeaderLabels(["Object", "Path", "Linked"])
        self.linked_objects_tree.setRootIsDecorated(True)
        self.linked_objects_tree.itemChanged.connect(self.on_link_toggled)
        linked_layout.addWidget(self.linked_objects_tree)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_link_btn = QPushButton("Add Link...")
        add_link_btn.clicked.connect(self.add_link)
        button_layout.addWidget(add_link_btn)
        
        remove_link_btn = QPushButton("Remove Selected")
        remove_link_btn.clicked.connect(self.remove_selected_links)
        button_layout.addWidget(remove_link_btn)
        
        clear_all_btn = QPushButton("Clear All Links")
        clear_all_btn.clicked.connect(self.clear_all_links)
        button_layout.addWidget(clear_all_btn)
        
        linked_layout.addLayout(button_layout)
        linked_group.setLayout(linked_layout)
        splitter.addWidget(linked_group)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        self.stage = stage
        if stage and USD_AVAILABLE:
            from ...managers.light_linking_manager import LightLinkingManager
            self.light_linking_manager = LightLinkingManager(stage)
        else:
            self.light_linking_manager = None
        self.refresh_lights()
    
    def refresh_lights(self):
        """Refresh light list"""
        self.light_list.clear()
        self.linked_objects_tree.clear()
        self.current_light_prim = None
        
        if not USD_AVAILABLE or not self.stage:
            return
        
        try:
            from ...utils.usd_lux_support import UsdLuxExtractor
            lights = UsdLuxExtractor.find_all_lights(self.stage)
            
            for light_prim in lights:
                item = QListWidgetItem(light_prim.GetPath().pathString)
                item.setData(Qt.ItemDataRole.UserRole, light_prim.GetPath().pathString)
                self.light_list.addItem(item)
        except Exception as e:
            print(f"Error refreshing lights: {e}")
    
    def on_light_selected(self):
        """Handle light selection"""
        selected = self.light_list.currentItem()
        if not selected or not self.light_linking_manager:
            return
        
        prim_path = selected.data(Qt.ItemDataRole.UserRole)
        if not prim_path:
            return
        
        light_prim = self.stage.GetPrimAtPath(prim_path)
        if not light_prim:
            return
        
        self.current_light_prim = light_prim
        self.refresh_linked_objects()
    
    def refresh_linked_objects(self):
        """Refresh linked objects tree"""
        self.linked_objects_tree.clear()
        
        if not self.current_light_prim or not self.light_linking_manager:
            return
        
        try:
            # Get currently linked objects
            linked_paths = self.light_linking_manager.get_light_links(self.current_light_prim)
            linked_paths_set = set(linked_paths)
            
            # Get all imageable prims (objects that can be linked)
            all_objects = []
            for prim in self.stage.Traverse():
                if prim.IsA(UsdGeom.Imageable):
                    all_objects.append(prim)
            
            # Populate tree
            for prim in all_objects:
                prim_path = str(prim.GetPath())
                is_linked = prim_path in linked_paths_set
                
                item = QTreeWidgetItem(self.linked_objects_tree)
                item.setText(0, prim.GetName())
                item.setText(1, prim_path)
                item.setCheckState(2, Qt.CheckState.Checked if is_linked else Qt.CheckState.Unchecked)
                item.setData(0, Qt.ItemDataRole.UserRole, prim_path)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            # Sort by name
            self.linked_objects_tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        except Exception as e:
            print(f"Error refreshing linked objects: {e}")
    
    def on_link_toggled(self, item: QTreeWidgetItem, column: int):
        """Handle link checkbox toggle"""
        if column != 2:  # Only handle the "Linked" column
            return
        
        if not self.current_light_prim or not self.light_linking_manager:
            return
        
        prim_path = item.data(0, Qt.ItemDataRole.UserRole)  # Get prim path
        is_checked = item.checkState(2) == Qt.CheckState.Checked
        
        try:
            success = self.light_linking_manager.set_light_link(
                self.current_light_prim,
                prim_path,
                is_checked
            )
            
            if success:
                self.linking_changed.emit()
            else:
                # Revert checkbox state
                item.setCheckState(2, Qt.CheckState.Unchecked if is_checked else Qt.CheckState.Checked)
                QMessageBox.warning(
                    self,
                    "Link Failed",
                    f"Failed to {'link' if is_checked else 'unlink'} object: {prim_path}"
                )
        except Exception as e:
            print(f"Error toggling link: {e}")
            # Revert checkbox state
            item.setCheckState(2, Qt.CheckState.Unchecked if is_checked else Qt.CheckState.Checked)
    
    def add_link(self):
        """Add a new light link"""
        if not self.current_light_prim:
            QMessageBox.warning(
                self,
                "No Light Selected",
                "Please select a light first."
            )
            return
        
        from PySide6.QtWidgets import QInputDialog
        
        # Get all prim paths
        prim_paths = []
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Imageable):
                prim_paths.append(str(prim.GetPath()))
        
        if not prim_paths:
            QMessageBox.information(
                self,
                "No Objects",
                "No imageable objects found in the stage."
            )
            return
        
        # Show dialog to select prim
        prim_path, ok = QInputDialog.getItem(
            self,
            "Add Light Link",
            "Select object to link:",
            prim_paths,
            0,
            False
        )
        
        if ok and prim_path:
            try:
                success = self.light_linking_manager.set_light_link(
                    self.current_light_prim,
                    prim_path,
                    True
                )
                
                if success:
                    self.refresh_linked_objects()
                    self.linking_changed.emit()
                else:
                    QMessageBox.warning(
                        self,
                        "Link Failed",
                        f"Failed to link object: {prim_path}"
                    )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error adding link:\n{e}"
                )
    
    def remove_selected_links(self):
        """Remove selected links"""
        if not self.current_light_prim:
            return
        
        selected_items = self.linked_objects_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select objects to unlink."
            )
            return
        
        try:
            for item in selected_items:
                prim_path = item.data(0, Qt.ItemDataRole.UserRole)
                if prim_path:
                    self.light_linking_manager.set_light_link(
                        self.current_light_prim,
                        prim_path,
                        False
                    )
            
            self.refresh_linked_objects()
            self.linking_changed.emit()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error removing links:\n{e}"
            )
    
    def clear_all_links(self):
        """Clear all links for current light"""
        if not self.current_light_prim:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear All Links",
            "Are you sure you want to clear all links for this light?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.light_linking_manager.clear_light_links(self.current_light_prim)
                if success:
                    self.refresh_linked_objects()
                    self.linking_changed.emit()
                else:
                    QMessageBox.warning(
                        self,
                        "Clear Failed",
                        "Failed to clear light links."
                    )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error clearing links:\n{e}"
                )

