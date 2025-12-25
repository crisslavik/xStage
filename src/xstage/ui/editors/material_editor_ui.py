"""
Material Preview & Editor UI
Visual material editing with property editor and preview
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QLineEdit, QDoubleSpinBox, QColorDialog,
    QGroupBox, QFormLayout, QComboBox, QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Optional, Dict

from ...managers.materials import MaterialManager


class MaterialEditorWidget(QWidget):
    """Material editor widget with property editing"""
    
    material_changed = Signal(str)  # Emits material path when changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.current_material = None
        self.current_material_prim = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Material Editor</b>")
        layout.addWidget(title)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Material list
        list_widget = QWidget()
        list_layout = QVBoxLayout()
        
        list_label = QLabel("Materials:")
        list_layout.addWidget(list_label)
        
        self.material_tree = QTreeWidget()
        self.material_tree.setHeaderLabels(["Material", "Path"])
        self.material_tree.itemSelectionChanged.connect(self.on_material_selected)
        list_layout.addWidget(self.material_tree)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        list_layout.addWidget(refresh_btn)
        
        list_widget.setLayout(list_layout)
        splitter.addWidget(list_widget)
        
        # Right: Material properties
        props_widget = QWidget()
        props_layout = QVBoxLayout()
        
        self.material_name_label = QLabel("No material selected")
        props_layout.addWidget(self.material_name_label)
        
        # Properties editor
        self.properties_group = QGroupBox("Properties")
        self.properties_layout = QFormLayout()
        self.properties_group.setLayout(self.properties_layout)
        props_layout.addWidget(self.properties_group)
        
        # Shader network
        shader_group = QGroupBox("Shader Network")
        shader_layout = QVBoxLayout()
        
        self.shader_text = QTextEdit()
        self.shader_text.setReadOnly(True)
        self.shader_text.setMaximumHeight(150)
        shader_layout.addWidget(self.shader_text)
        
        shader_group.setLayout(shader_layout)
        props_layout.addWidget(shader_group)
        
        props_layout.addStretch()
        props_widget.setLayout(props_layout)
        splitter.addWidget(props_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        self.stage = stage
        self.refresh()
    
    def refresh(self):
        """Refresh material list"""
        self.material_tree.clear()
        
        if not self.stage:
            return
        
        # Get all materials
        materials = MaterialManager.find_all_materials(self.stage)
        
        for material_prim in materials:
            item = QTreeWidgetItem([
                material_prim.GetName(),
                material_prim.GetPath().pathString
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, material_prim.GetPath().pathString)
            self.material_tree.addTopLevelItem(item)
    
    def on_material_selected(self):
        """Handle material selection"""
        selected = self.material_tree.currentItem()
        if not selected:
            return
        
        prim_path = selected.data(0, Qt.ItemDataRole.UserRole)
        if not prim_path:
            return
        
        # Get material prim
        material_prim = self.stage.GetPrimAtPath(prim_path)
        if not material_prim:
            return
        
        self.current_material_prim = material_prim
        
        # Extract material data
        material_data = MaterialManager.extract_material(material_prim, 0.0)
        if material_data:
            self.current_material = material_data
            self.display_material(material_data)
    
    def display_material(self, material_data: Dict):
        """Display material properties"""
        # Clear previous properties
        while self.properties_layout.rowCount() > 0:
            self.properties_layout.removeRow(0)
        
        # Set name
        self.material_name_label.setText(f"Material: {material_data['name']}")
        
        # Display inputs
        if 'inputs' in material_data:
            for input_name, input_data in material_data['inputs'].items():
                value = input_data.get('value')
                input_type = input_data.get('type', '')
                
                # Create appropriate widget based on type
                if 'Color' in input_type or 'Vec3' in input_type:
                    # Color input
                    color_btn = QPushButton("Color")
                    if isinstance(value, (list, tuple)) and len(value) >= 3:
                        color = QColor(int(value[0] * 255), int(value[1] * 255), int(value[2] * 255))
                        color_btn.setStyleSheet(f"background-color: {color.name()}")
                        color_btn.clicked.connect(lambda checked, name=input_name: self.edit_color_input(name))
                    self.properties_layout.addRow(input_name + ":", color_btn)
                elif 'Float' in input_type:
                    # Float input
                    spinbox = QDoubleSpinBox()
                    spinbox.setRange(-1000000, 1000000)
                    spinbox.setDecimals(3)
                    if isinstance(value, (int, float)):
                        spinbox.setValue(value)
                    spinbox.valueChanged.connect(lambda v, name=input_name: self.set_input_value(name, v))
                    self.properties_layout.addRow(input_name + ":", spinbox)
                elif 'String' in input_type or 'Token' in input_type:
                    # String input
                    line_edit = QLineEdit(str(value) if value else "")
                    line_edit.textChanged.connect(lambda text, name=input_name: self.set_input_value(name, text))
                    self.properties_layout.addRow(input_name + ":", line_edit)
                else:
                    # Generic display
                    label = QLabel(str(value) if value else "N/A")
                    self.properties_layout.addRow(input_name + ":", label)
        
        # Display shader network
        shader_text = "Shader Network:\n"
        if 'shader_network' in material_data and material_data['shader_network']:
            for shader in material_data['shader_network']:
                shader_text += f"\nShader: {shader.get('name', 'N/A')}\n"
                shader_text += f"  ID: {shader.get('id', 'N/A')}\n"
                if 'inputs' in shader:
                    shader_text += "  Inputs:\n"
                    for input_name, input_data in shader['inputs'].items():
                        if input_data.get('connected'):
                            shader_text += f"    {input_name}: Connected to {input_data.get('source', 'N/A')}\n"
                        else:
                            shader_text += f"    {input_name}: {input_data.get('value', 'N/A')}\n"
        else:
            shader_text += "No shader network"
        
        self.shader_text.setText(shader_text)
    
    def edit_color_input(self, input_name: str):
        """Edit color input"""
        if not self.current_material_prim:
            return
        
        # Get current value
        material = MaterialManager.extract_material(self.current_material_prim, 0.0)
        if not material or 'inputs' not in material:
            return
        
        input_data = material['inputs'].get(input_name)
        if not input_data:
            return
        
        value = input_data.get('value')
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            color = QColor(int(value[0] * 255), int(value[1] * 255), int(value[2] * 255))
        else:
            color = QColor(255, 255, 255)
        
        # Open color dialog
        color = QColorDialog.getColor(color, self, f"Select {input_name}")
        if color.isValid():
            rgb = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self.set_input_value(input_name, rgb)
    
    def set_input_value(self, input_name: str, value):
        """Set material input value"""
        if not self.current_material_prim:
            return
        
        try:
            from pxr import UsdShade
            material = UsdShade.Material(self.current_material_prim)
            input_attr = material.GetInput(input_name)
            if input_attr:
                input_attr.Set(value)
                self.material_changed.emit(self.current_material_prim.GetPath().pathString)
                # Refresh display
                self.on_material_selected()
        except Exception as e:
            print(f"Error setting input value: {e}")

