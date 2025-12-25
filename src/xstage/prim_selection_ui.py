"""
Prim Selection & Manipulation UI
Properties panel and transform editor for selected prims
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QDoubleSpinBox, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, List
from pxr import Gf

from .prim_selection import PrimSelectionManager


class PrimPropertiesWidget(QWidget):
    """Widget for displaying and editing prim properties"""
    
    property_changed = Signal(str, str, object)  # Emits (prim_path, property_name, value)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selection_manager = None
        self.current_prim = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Prim Properties</b>")
        layout.addWidget(title)
        
        # Prim info
        self.prim_name_label = QLabel("No prim selected")
        layout.addWidget(self.prim_name_label)
        
        # Transform group
        transform_group = QGroupBox("Transform")
        transform_layout = QFormLayout()
        
        # Translation
        self.translate_x_spin = QDoubleSpinBox()
        self.translate_x_spin.setRange(-100000, 100000)
        self.translate_x_spin.setDecimals(3)
        self.translate_x_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Translate X:", self.translate_x_spin)
        
        self.translate_y_spin = QDoubleSpinBox()
        self.translate_y_spin.setRange(-100000, 100000)
        self.translate_y_spin.setDecimals(3)
        self.translate_y_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Translate Y:", self.translate_y_spin)
        
        self.translate_z_spin = QDoubleSpinBox()
        self.translate_z_spin.setRange(-100000, 100000)
        self.translate_z_spin.setDecimals(3)
        self.translate_z_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Translate Z:", self.translate_z_spin)
        
        # Rotation
        self.rotate_x_spin = QDoubleSpinBox()
        self.rotate_x_spin.setRange(-360, 360)
        self.rotate_x_spin.setDecimals(2)
        self.rotate_x_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Rotate X:", self.rotate_x_spin)
        
        self.rotate_y_spin = QDoubleSpinBox()
        self.rotate_y_spin.setRange(-360, 360)
        self.rotate_y_spin.setDecimals(2)
        self.rotate_y_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Rotate Y:", self.rotate_y_spin)
        
        self.rotate_z_spin = QDoubleSpinBox()
        self.rotate_z_spin.setRange(-360, 360)
        self.rotate_z_spin.setDecimals(2)
        self.rotate_z_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Rotate Z:", self.rotate_z_spin)
        
        # Scale
        self.scale_x_spin = QDoubleSpinBox()
        self.scale_x_spin.setRange(0.001, 1000)
        self.scale_x_spin.setDecimals(3)
        self.scale_x_spin.setValue(1.0)
        self.scale_x_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Scale X:", self.scale_x_spin)
        
        self.scale_y_spin = QDoubleSpinBox()
        self.scale_y_spin.setRange(0.001, 1000)
        self.scale_y_spin.setDecimals(3)
        self.scale_y_spin.setValue(1.0)
        self.scale_y_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Scale Y:", self.scale_y_spin)
        
        self.scale_z_spin = QDoubleSpinBox()
        self.scale_z_spin.setRange(0.001, 1000)
        self.scale_z_spin.setDecimals(3)
        self.scale_z_spin.setValue(1.0)
        self.scale_z_spin.valueChanged.connect(self.on_transform_changed)
        transform_layout.addRow("Scale Z:", self.scale_z_spin)
        
        transform_group.setLayout(transform_layout)
        layout.addWidget(transform_group)
        
        # Attributes group
        attrs_group = QGroupBox("Attributes")
        attrs_layout = QVBoxLayout()
        
        self.attributes_text = QTextEdit()
        self.attributes_text.setReadOnly(True)
        self.attributes_text.setMaximumHeight(200)
        attrs_layout.addWidget(self.attributes_text)
        
        attrs_group.setLayout(attrs_layout)
        layout.addWidget(attrs_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_selection_manager(self, manager: PrimSelectionManager):
        """Set the selection manager"""
        self.selection_manager = manager
    
    def update_selection(self, prim_path: Optional[str]):
        """Update display for selected prim"""
        if not prim_path or not self.selection_manager:
            self.prim_name_label.setText("No prim selected")
            return
        
        prim = self.selection_manager.stage.GetPrimAtPath(prim_path)
        if not prim:
            return
        
        self.current_prim = prim
        self.prim_name_label.setText(f"Prim: {prim.GetName()}\nPath: {prim_path}")
        
        # Get transform
        transform = self.selection_manager.get_prim_transform(prim)
        if transform:
            # Extract translation
            translation = transform.ExtractTranslation()
            self.translate_x_spin.setValue(translation[0])
            self.translate_y_spin.setValue(translation[1])
            self.translate_z_spin.setValue(translation[2])
            
            # Extract rotation (simplified - full rotation extraction is complex)
            # For now, just show 0,0,0 and let user edit
            self.rotate_x_spin.setValue(0.0)
            self.rotate_y_spin.setValue(0.0)
            self.rotate_z_spin.setValue(0.0)
            
            # Extract scale
            scale = transform.ExtractScale()
            self.scale_x_spin.setValue(scale[0])
            self.scale_y_spin.setValue(scale[1])
            self.scale_z_spin.setValue(scale[2])
        
        # Display attributes
        attrs_text = "Attributes:\n"
        for attr in prim.GetAttributes():
            try:
                value = attr.Get()
                attrs_text += f"\n{attr.GetName()}: {value} ({attr.GetTypeName()})"
            except:
                pass
        
        self.attributes_text.setText(attrs_text)
    
    def on_transform_changed(self):
        """Handle transform change"""
        if not self.current_prim or not self.selection_manager:
            return
        
        # Apply transform changes
        translation = Gf.Vec3d(
            self.translate_x_spin.value(),
            self.translate_y_spin.value(),
            self.translate_z_spin.value()
        )
        self.selection_manager.translate_prim(self.current_prim, translation)
        
        rotation = Gf.Vec3f(
            self.rotate_x_spin.value(),
            self.rotate_y_spin.value(),
            self.rotate_z_spin.value()
        )
        self.selection_manager.rotate_prim(self.current_prim, rotation)
        
        scale = Gf.Vec3f(
            self.scale_x_spin.value(),
            self.scale_y_spin.value(),
            self.scale_z_spin.value()
        )
        self.selection_manager.scale_prim(self.current_prim, scale)

