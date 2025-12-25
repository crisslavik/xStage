"""
Render Settings Editor UI
Edit render settings, products, and AOVs
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QComboBox, QGroupBox, QFormLayout, QSpinBox,
    QDoubleSpinBox, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from typing import Optional

try:
    from pxr import UsdRender
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class RenderSettingsEditorWidget(QWidget):
    """Widget for editing render settings"""
    
    render_settings_changed = Signal(str)  # Emits render settings path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.current_render_settings = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Render Settings Editor</b>")
        layout.addWidget(title)
        
        # Render settings list
        list_label = QLabel("Render Settings:")
        layout.addWidget(list_label)
        
        self.settings_tree = QTreeWidget()
        self.settings_tree.setHeaderLabels(["Render Settings", "Path"])
        self.settings_tree.itemSelectionChanged.connect(self.on_settings_selected)
        layout.addWidget(self.settings_tree)
        
        # Render settings properties
        props_group = QGroupBox("Render Settings Properties")
        props_layout = QFormLayout()
        
        self.settings_name_label = QLabel("No render settings selected")
        props_layout.addRow("Settings:", self.settings_name_label)
        
        # Resolution
        resolution_layout = QHBoxLayout()
        self.resolution_x_spin = QSpinBox()
        self.resolution_x_spin.setRange(1, 10000)
        self.resolution_x_spin.setValue(1920)
        self.resolution_x_spin.valueChanged.connect(self.on_property_changed)
        resolution_layout.addWidget(self.resolution_x_spin)
        
        resolution_layout.addWidget(QLabel("x"))
        
        self.resolution_y_spin = QSpinBox()
        self.resolution_y_spin.setRange(1, 10000)
        self.resolution_y_spin.setValue(1080)
        self.resolution_y_spin.valueChanged.connect(self.on_property_changed)
        resolution_layout.addWidget(self.resolution_y_spin)
        
        props_layout.addRow("Resolution:", resolution_layout)
        
        # Pixel aspect ratio
        self.pixel_aspect_spin = QDoubleSpinBox()
        self.pixel_aspect_spin.setRange(0.1, 10.0)
        self.pixel_aspect_spin.setDecimals(3)
        self.pixel_aspect_spin.setValue(1.0)
        self.pixel_aspect_spin.valueChanged.connect(self.on_property_changed)
        props_layout.addRow("Pixel Aspect Ratio:", self.pixel_aspect_spin)
        
        # Camera
        self.camera_combo = QComboBox()
        self.camera_combo.setEditable(True)
        self.camera_combo.currentTextChanged.connect(self.on_property_changed)
        props_layout.addRow("Camera:", self.camera_combo)
        
        # Products
        products_group = QGroupBox("Render Products")
        products_layout = QVBoxLayout()
        
        self.products_list = QListWidget()
        products_layout.addWidget(self.products_list)
        
        products_group.setLayout(products_layout)
        props_layout.addRow("", products_group)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
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
        """Refresh render settings list"""
        self.settings_tree.clear()
        
        if not self.stage or not USD_AVAILABLE:
            return
        
        # Find all render settings
        for prim in self.stage.Traverse():
            if prim.IsA(UsdRender.RenderSettings):
                item = QTreeWidgetItem([
                    prim.GetName(),
                    prim.GetPath().pathString
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, prim.GetPath().pathString)
                self.settings_tree.addTopLevelItem(item)
        
        # Update camera list
        self.camera_combo.clear()
        self.camera_combo.addItem("")
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Camera):
                self.camera_combo.addItem(prim.GetPath().pathString)
    
    def on_settings_selected(self):
        """Handle render settings selection"""
        selected = self.settings_tree.currentItem()
        if not selected or not self.stage or not USD_AVAILABLE:
            return
        
        prim_path = selected.data(0, Qt.ItemDataRole.UserRole)
        if not prim_path:
            return
        
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim:
            return
        
        self.current_render_settings = UsdRender.RenderSettings(prim)
        self.settings_name_label.setText(prim.GetName())
        
        # Load properties
        if self.current_render_settings.GetResolutionAttr():
            resolution = self.current_render_settings.GetResolutionAttr().Get()
            if resolution:
                self.resolution_x_spin.setValue(resolution[0])
                self.resolution_y_spin.setValue(resolution[1])
        
        if self.current_render_settings.GetPixelAspectRatioAttr():
            aspect = self.current_render_settings.GetPixelAspectRatioAttr().Get()
            if aspect:
                self.pixel_aspect_spin.setValue(aspect)
        
        # Load camera
        if self.current_render_settings.GetCameraRel():
            cameras = self.current_render_settings.GetCameraRel().GetTargets()
            if cameras:
                index = self.camera_combo.findText(str(cameras[0]))
                if index >= 0:
                    self.camera_combo.setCurrentIndex(index)
        
        # Load products
        self.products_list.clear()
        if self.current_render_settings.GetProductsRel():
            products = self.current_render_settings.GetProductsRel().GetTargets()
            for product in products:
                self.products_list.addItem(str(product))
    
    def on_property_changed(self):
        """Handle property change"""
        if not self.current_render_settings:
            return
        
        try:
            # Set resolution
            from pxr import Gf
            resolution = Gf.Vec2i(
                self.resolution_x_spin.value(),
                self.resolution_y_spin.value()
            )
            self.current_render_settings.GetResolutionAttr().Set(resolution)
            
            # Set pixel aspect ratio
            self.current_render_settings.GetPixelAspectRatioAttr().Set(
                self.pixel_aspect_spin.value()
            )
            
            # Set camera
            camera_path = self.camera_combo.currentText()
            if camera_path:
                from pxr import Sdf
                self.current_render_settings.GetCameraRel().SetTargets([
                    Sdf.Path(camera_path)
                ])
            
            self.render_settings_changed.emit(
                self.current_render_settings.GetPrim().GetPath().pathString
            )
        except Exception as e:
            print(f"Error updating render settings: {e}")

