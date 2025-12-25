"""
OpenExec UI
Display and manage computed attributes
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QGroupBox, QFormLayout, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from typing import Optional

from .openexec_support import OpenExecManager


class OpenExecWidget(QWidget):
    """Widget for managing OpenExec computed attributes"""
    
    extent_computed = Signal(str)  # Emits prim path when extent is computed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.openexec_manager = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>OpenExec - Computed Attributes</b>")
        layout.addWidget(title)
        
        # Info
        info_label = QLabel(
            "OpenExec enables computed attributes and automatic extent calculations. "
            "Computed attributes are calculated at runtime rather than stored."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Computed attributes list
        attrs_group = QGroupBox("Computed Attributes")
        attrs_layout = QVBoxLayout()
        
        self.attrs_tree = QTreeWidget()
        self.attrs_tree.setHeaderLabels(["Prim", "Attribute", "Status", "Value"])
        attrs_layout.addWidget(self.attrs_tree)
        
        refresh_attrs_btn = QPushButton("Refresh Computed Attributes")
        refresh_attrs_btn.clicked.connect(self.refresh_computed_attributes)
        attrs_layout.addWidget(refresh_attrs_btn)
        
        attrs_group.setLayout(attrs_layout)
        layout.addWidget(attrs_group)
        
        # Extent computation
        extent_group = QGroupBox("Extent Computation")
        extent_layout = QVBoxLayout()
        
        extent_info = QLabel(
            "Extent (bounding box) can be computed automatically for geometry prims. "
            "This ensures accurate bounding boxes even when geometry changes."
        )
        extent_info.setWordWrap(True)
        extent_layout.addWidget(extent_info)
        
        self.compute_all_extents_check = QCheckBox("Compute extents for all boundable prims")
        self.compute_all_extents_check.setChecked(False)
        extent_layout.addWidget(self.compute_all_extents_check)
        
        compute_btn = QPushButton("Compute Extents")
        compute_btn.clicked.connect(self.compute_extents)
        extent_layout.addWidget(compute_btn)
        
        extent_group.setLayout(extent_layout)
        layout.addWidget(extent_group)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        self.stage = stage
        if stage:
            self.openexec_manager = OpenExecManager(stage)
            self.refresh_computed_attributes()
        else:
            self.openexec_manager = None
            self.attrs_tree.clear()
    
    def refresh_computed_attributes(self):
        """Refresh list of computed attributes"""
        self.attrs_tree.clear()
        
        if not self.stage or not self.openexec_manager:
            return
        
        try:
            # Find all prims with computed attributes
            for prim in self.stage.Traverse():
                computed_attrs = self.openexec_manager.get_all_computed_attributes(prim)
                
                if computed_attrs:
                    prim_item = QTreeWidgetItem([prim.GetPath().pathString, "", "", ""])
                    
                    for attr_name in computed_attrs:
                        info = self.openexec_manager.get_computed_attribute_info(prim, attr_name)
                        
                        status = "Computed" if info.get('is_computed') else "Can Compute"
                        value_str = str(info.get('computed_value', 'N/A'))
                        if len(value_str) > 50:
                            value_str = value_str[:50] + "..."
                        
                        attr_item = QTreeWidgetItem([
                            "",
                            attr_name,
                            status,
                            value_str
                        ])
                        prim_item.addChild(attr_item)
                    
                    self.attrs_tree.addTopLevelItem(prim_item)
            
            self.attrs_tree.expandAll()
            self.status_label.setText(f"Found {self.attrs_tree.topLevelItemCount()} prims with computed attributes")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
    
    def compute_extents(self):
        """Compute extents for prims"""
        if not self.stage or not self.openexec_manager:
            return
        
        try:
            from .progress_manager import ProgressDialogManager
            
            progress_mgr = ProgressDialogManager(self)
            reporter = progress_mgr.show_progress("Computing Extents...", cancelable=False)
            
            def progress_callback(progress, message):
                reporter.report(progress, message)
            
            results = self.openexec_manager.compute_all_extents(
                time_code=0.0,
                progress_callback=progress_callback
            )
            
            reporter.finish(True, "Extent computation complete")
            
            # Count successes
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            
            self.status_label.setText(
                f"Computed extents: {success_count}/{total_count} prims"
            )
            
            # Refresh computed attributes
            self.refresh_computed_attributes()
            
            QMessageBox.information(
                self, "Extent Computation",
                f"Computed extents for {success_count} out of {total_count} prims"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compute extents: {e}")
            self.status_label.setText(f"Error: {e}")

