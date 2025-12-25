"""
Primvar Editor UI
Edit primvar values and interpolation modes
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QComboBox, QGroupBox, QFormLayout, QTextEdit,
    QDoubleSpinBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from typing import Optional
from pxr import UsdGeom, Sdf

try:
    from pxr import UsdGeom, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class PrimvarEditorWidget(QWidget):
    """Widget for editing primvars"""
    
    primvar_changed = Signal(str, str)  # Emits (prim_path, primvar_name)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.current_prim = None
        self.current_primvar = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Primvar Editor</b>")
        layout.addWidget(title)
        
        # Prim selection
        prim_layout = QHBoxLayout()
        prim_layout.addWidget(QLabel("Prim Path:"))
        self.prim_path_edit = QLineEdit()
        self.prim_path_edit.setPlaceholderText("/World/MyPrim")
        self.prim_path_edit.returnPressed.connect(self.load_prim)
        prim_layout.addWidget(self.prim_path_edit)
        
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_prim)
        prim_layout.addWidget(load_btn)
        layout.addLayout(prim_layout)
        
        # Primvar list
        list_label = QLabel("Primvars:")
        layout.addWidget(list_label)
        
        self.primvar_tree = QTreeWidget()
        self.primvar_tree.setHeaderLabels(["Primvar", "Type", "Interpolation"])
        self.primvar_tree.itemSelectionChanged.connect(self.on_primvar_selected)
        layout.addWidget(self.primvar_tree)
        
        # Primvar properties
        props_group = QGroupBox("Primvar Properties")
        props_layout = QFormLayout()
        
        self.primvar_name_label = QLabel("No primvar selected")
        props_layout.addRow("Primvar:", self.primvar_name_label)
        
        self.interpolation_combo = QComboBox()
        self.interpolation_combo.addItems([
            "constant", "uniform", "varying", "vertex", "faceVarying"
        ])
        self.interpolation_combo.currentTextChanged.connect(self.on_property_changed)
        props_layout.addRow("Interpolation:", self.interpolation_combo)
        
        self.values_text = QTextEdit()
        self.values_text.setPlaceholderText("Enter values (one per line or comma-separated)")
        self.values_text.setMaximumHeight(100)
        props_layout.addRow("Values:", self.values_text)
        
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(self.apply_changes)
        props_layout.addRow("", apply_btn)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        self.stage = stage
    
    def load_prim(self):
        """Load prim and its primvars"""
        self.primvar_tree.clear()
        
        if not self.stage:
            return
        
        prim_path = self.prim_path_edit.text()
        if not prim_path:
            return
        
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim:
            return
        
        self.current_prim = prim
        
        # Get primvars
        primvars_api = UsdGeom.PrimvarsAPI(prim)
        primvars = primvars_api.GetPrimvars()
        
        for primvar in primvars:
            item = QTreeWidgetItem([
                primvar.GetPrimvarName(),
                str(primvar.GetTypeName()),
                str(primvar.GetInterpolation())
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, primvar.GetPrimvarName())
            self.primvar_tree.addTopLevelItem(item)
    
    def on_primvar_selected(self):
        """Handle primvar selection"""
        selected = self.primvar_tree.currentItem()
        if not selected or not self.current_prim:
            return
        
        primvar_name = selected.data(0, Qt.ItemDataRole.UserRole)
        if not primvar_name:
            return
        
        # Get primvar
        primvars_api = UsdGeom.PrimvarsAPI(self.current_prim)
        primvar = primvars_api.GetPrimvar(primvar_name)
        if not primvar:
            return
        
        self.current_primvar = primvar
        self.primvar_name_label.setText(primvar_name)
        
        # Set interpolation
        interpolation = str(primvar.GetInterpolation())
        index = self.interpolation_combo.findText(interpolation)
        if index >= 0:
            self.interpolation_combo.setCurrentIndex(index)
        
        # Get values
        try:
            values = primvar.Get()
            if values:
                if isinstance(values, (list, tuple)):
                    values_str = "\n".join(str(v) for v in values)
                else:
                    values_str = str(values)
                self.values_text.setText(values_str)
        except:
            self.values_text.clear()
    
    def on_property_changed(self):
        """Handle property change"""
        # Will be applied when user clicks Apply
        pass
    
    def apply_changes(self):
        """Apply primvar changes"""
        if not self.current_primvar or not self.current_prim:
            return
        
        try:
            # Set interpolation
            interpolation = UsdGeom.Tokens(self.interpolation_combo.currentText())
            self.current_primvar.SetInterpolation(interpolation)
            
            # Parse and set values
            values_text = self.values_text.toPlainText()
            if values_text.strip():
                # Try to parse values
                # This is simplified - real implementation would need proper type handling
                lines = [line.strip() for line in values_text.split('\n') if line.strip()]
                if lines:
                    # For now, just try to set as string
                    # Real implementation would parse based on primvar type
                    pass
            
            self.primvar_changed.emit(
                self.current_prim.GetPath().pathString,
                self.current_primvar.GetPrimvarName()
            )
        except Exception as e:
            print(f"Error applying primvar changes: {e}")

