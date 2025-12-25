"""
Camera Management UI
Camera list, switching, and properties editor
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QGroupBox, QFormLayout, QDoubleSpinBox,
    QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from typing import Optional

from .camera_manager import CameraManager


class CameraManagerWidget(QWidget):
    """Widget for managing cameras"""
    
    camera_selected = Signal(str)  # Emits camera path when selected
    camera_changed = Signal(str)  # Emits camera path when properties change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_manager = None
        self.current_camera_prim = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Camera Management</b>")
        layout.addWidget(title)
        
        # Camera list
        list_label = QLabel("Cameras:")
        layout.addWidget(list_label)
        
        self.camera_list = QListWidget()
        self.camera_list.itemSelectionChanged.connect(self.on_camera_selected)
        self.camera_list.itemDoubleClicked.connect(self.on_camera_double_clicked)
        layout.addWidget(self.camera_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(refresh_btn)
        
        create_btn = QPushButton("Create Camera")
        create_btn.clicked.connect(self.create_camera)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        # Camera properties
        props_group = QGroupBox("Camera Properties")
        props_layout = QFormLayout()
        
        self.camera_name_label = QLabel("No camera selected")
        props_layout.addRow("Camera:", self.camera_name_label)
        
        self.focal_length_spin = QDoubleSpinBox()
        self.focal_length_spin.setRange(1.0, 1000.0)
        self.focal_length_spin.setDecimals(2)
        self.focal_length_spin.valueChanged.connect(self.on_property_changed)
        props_layout.addRow("Focal Length:", self.focal_length_spin)
        
        self.h_aperture_spin = QDoubleSpinBox()
        self.h_aperture_spin.setRange(0.1, 100.0)
        self.h_aperture_spin.setDecimals(3)
        self.h_aperture_spin.valueChanged.connect(self.on_property_changed)
        props_layout.addRow("Horizontal Aperture:", self.h_aperture_spin)
        
        self.v_aperture_spin = QDoubleSpinBox()
        self.v_aperture_spin.setRange(0.1, 100.0)
        self.v_aperture_spin.setDecimals(3)
        self.v_aperture_spin.valueChanged.connect(self.on_property_changed)
        props_layout.addRow("Vertical Aperture:", self.v_aperture_spin)
        
        self.near_clip_spin = QDoubleSpinBox()
        self.near_clip_spin.setRange(0.001, 1000.0)
        self.near_clip_spin.setDecimals(3)
        self.near_clip_spin.valueChanged.connect(self.on_property_changed)
        props_layout.addRow("Near Clip:", self.near_clip_spin)
        
        self.far_clip_spin = QDoubleSpinBox()
        self.far_clip_spin.setRange(0.1, 100000.0)
        self.far_clip_spin.setDecimals(1)
        self.far_clip_spin.valueChanged.connect(self.on_property_changed)
        props_layout.addRow("Far Clip:", self.far_clip_spin)
        
        self.projection_combo = QComboBox()
        self.projection_combo.addItems(["perspective", "orthographic"])
        self.projection_combo.currentTextChanged.connect(self.on_property_changed)
        props_layout.addRow("Projection:", self.projection_combo)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        if stage:
            self.camera_manager = CameraManager(stage)
            self.refresh()
        else:
            self.camera_manager = None
            self.camera_list.clear()
    
    def refresh(self):
        """Refresh camera list"""
        self.camera_list.clear()
        
        if not self.camera_manager:
            return
        
        cameras = self.camera_manager.find_all_cameras()
        for camera_prim in cameras:
            item = QListWidgetItem(camera_prim.GetPath().pathString)
            item.setData(Qt.ItemDataRole.UserRole, camera_prim.GetPath().pathString)
            self.camera_list.addItem(item)
    
    def on_camera_selected(self):
        """Handle camera selection"""
        selected = self.camera_list.currentItem()
        if not selected or not self.camera_manager:
            return
        
        prim_path = selected.data(Qt.ItemDataRole.UserRole)
        if not prim_path:
            return
        
        camera_prim = self.camera_manager.stage.GetPrimAtPath(prim_path)
        if not camera_prim:
            return
        
        self.current_camera_prim = camera_prim
        self.camera_manager.set_current_camera(camera_prim)
        
        # Load camera properties
        camera_info = self.camera_manager.get_camera_info(camera_prim)
        if camera_info:
            self.camera_name_label.setText(camera_info['name'])
            self.focal_length_spin.setValue(camera_info['focal_length'])
            self.h_aperture_spin.setValue(camera_info['horizontal_aperture'])
            self.v_aperture_spin.setValue(camera_info['vertical_aperture'])
            self.near_clip_spin.setValue(camera_info['near_clip'])
            self.far_clip_spin.setValue(camera_info['far_clip'])
            projection_index = self.projection_combo.findText(camera_info['projection'])
            if projection_index >= 0:
                self.projection_combo.setCurrentIndex(projection_index)
        
        self.camera_selected.emit(prim_path)
    
    def on_camera_double_clicked(self, item: QListWidgetItem):
        """Handle camera double-click (switch to camera)"""
        self.on_camera_selected()
    
    def on_property_changed(self):
        """Handle property change"""
        if not self.current_camera_prim or not self.camera_manager:
            return
        
        # Update camera properties
        self.camera_manager.set_camera_property(
            self.current_camera_prim, 'focal_length', self.focal_length_spin.value()
        )
        self.camera_manager.set_camera_property(
            self.current_camera_prim, 'horizontal_aperture', self.h_aperture_spin.value()
        )
        self.camera_manager.set_camera_property(
            self.current_camera_prim, 'vertical_aperture', self.v_aperture_spin.value()
        )
        self.camera_manager.set_camera_property(
            self.current_camera_prim, 'near_clip', self.near_clip_spin.value()
        )
        self.camera_manager.set_camera_property(
            self.current_camera_prim, 'far_clip', self.far_clip_spin.value()
        )
        self.camera_manager.set_camera_property(
            self.current_camera_prim, 'projection', self.projection_combo.currentText()
        )
        
        self.camera_changed.emit(self.current_camera_prim.GetPath().pathString)
    
    def create_camera(self):
        """Create a new camera"""
        if not self.camera_manager:
            return
        
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Create Camera", "Camera name:")
        if ok and name:
            camera_prim = self.camera_manager.create_camera("/World", name)
            if camera_prim:
                self.refresh()
                # Select the new camera
                for i in range(self.camera_list.count()):
                    item = self.camera_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == camera_prim.GetPath().pathString:
                        self.camera_list.setCurrentItem(item)
                        break

