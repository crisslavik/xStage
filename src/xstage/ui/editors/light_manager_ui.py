"""
Light Management UI
Light list, properties, and look-through functionality
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QGroupBox, QFormLayout, QDoubleSpinBox,
    QComboBox, QColorDialog, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Optional

try:
    from pxr import Usd, UsdLux
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class LightManagerWidget(QWidget):
    """Widget for managing lights"""
    
    light_selected = Signal(str)  # Emits light path when selected
    light_changed = Signal(str)  # Emits light path when properties change
    look_through_light = Signal(str)  # Emits light path for look-through
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.current_light_prim = None
        self.light_linking_widget = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Light Management</b>")
        layout.addWidget(title)
        
        # Light list
        list_label = QLabel("Lights:")
        layout.addWidget(list_label)
        
        self.light_list = QListWidget()
        self.light_list.itemSelectionChanged.connect(self.on_light_selected)
        self.light_list.itemDoubleClicked.connect(self.on_light_double_clicked)
        layout.addWidget(self.light_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(refresh_btn)
        
        look_through_btn = QPushButton("Look Through")
        look_through_btn.clicked.connect(self.on_look_through_clicked)
        button_layout.addWidget(look_through_btn)
        
        light_linking_btn = QPushButton("Light Linking...")
        light_linking_btn.clicked.connect(self.show_light_linking)
        button_layout.addWidget(light_linking_btn)
        
        layout.addLayout(button_layout)
        
        # Light properties
        props_group = QGroupBox("Light Properties")
        props_layout = QFormLayout()
        
        self.light_name_label = QLabel("No light selected")
        props_layout.addRow("Light:", self.light_name_label)
        
        self.light_type_label = QLabel("-")
        props_layout.addRow("Type:", self.light_type_label)
        
        self.intensity_spin = QDoubleSpinBox()
        self.intensity_spin.setRange(0.0, 1000.0)
        self.intensity_spin.setDecimals(2)
        self.intensity_spin.valueChanged.connect(self.on_property_changed)
        props_layout.addRow("Intensity:", self.intensity_spin)
        
        self.exposure_spin = QDoubleSpinBox()
        self.exposure_spin.setRange(-10.0, 10.0)
        self.exposure_spin.setDecimals(2)
        self.exposure_spin.valueChanged.connect(self.on_property_changed)
        props_layout.addRow("Exposure:", self.exposure_spin)
        
        self.color_btn = QPushButton("Color")
        self.color_btn.clicked.connect(self.on_color_clicked)
        self.color_btn.setStyleSheet("background-color: white;")
        props_layout.addRow("Color:", self.color_btn)
        
        self.current_color = QColor(255, 255, 255)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        self.stage = stage
        self.refresh()
    
    def refresh(self):
        """Refresh light list"""
        self.light_list.clear()
        
        if not USD_AVAILABLE or not self.stage:
            return
        
        try:
            from ..utils.usd_lux_support import UsdLuxExtractor
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
        if not selected or not USD_AVAILABLE or not self.stage:
            return
        
        prim_path = selected.data(Qt.ItemDataRole.UserRole)
        if not prim_path:
            return
        
        light_prim = self.stage.GetPrimAtPath(prim_path)
        if not light_prim:
            return
        
        self.current_light_prim = light_prim
        
        # Load light properties
        try:
            from ..utils.usd_lux_support import UsdLuxExtractor
            light_data = UsdLuxExtractor.extract_light(light_prim, 0.0)
            
            if light_data:
                self.light_name_label.setText(light_prim.GetName())
                self.light_type_label.setText(light_data.get('type', 'Unknown'))
                self.intensity_spin.setValue(light_data.get('intensity', 1.0))
                self.exposure_spin.setValue(light_data.get('exposure', 0.0))
                
                color = light_data.get('color', (1.0, 1.0, 1.0))
                self.current_color = QColor(
                    int(color[0] * 255),
                    int(color[1] * 255),
                    int(color[2] * 255)
                )
                self.color_btn.setStyleSheet(
                    f"background-color: rgb({self.current_color.red()}, "
                    f"{self.current_color.green()}, {self.current_color.blue()});"
                )
        except Exception as e:
            print(f"Error loading light properties: {e}")
        
        self.light_selected.emit(prim_path)
    
    def on_light_double_clicked(self, item: QListWidgetItem):
        """Handle light double-click (look through)"""
        self.on_look_through_clicked()
    
    def on_look_through_clicked(self):
        """Handle look-through button click"""
        if not self.current_light_prim:
            return
        
        prim_path = str(self.current_light_prim.GetPath())
        self.look_through_light.emit(prim_path)
    
    def on_color_clicked(self):
        """Handle color button click"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.color_btn.setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
            )
            self.on_property_changed()
    
    def show_light_linking(self):
        """Show light linking dialog"""
        if not self.stage:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "No Stage",
                "No USD stage loaded."
            )
            return
        
        if not self.light_linking_widget:
            from PySide6.QtWidgets import QDialog, QVBoxLayout
            from ..editors.light_linking_ui import LightLinkingWidget
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Light Linking")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            self.light_linking_widget = LightLinkingWidget()
            self.light_linking_widget.set_stage(self.stage)
            self.light_linking_widget.linking_changed.connect(self.on_linking_changed)
            layout.addWidget(self.light_linking_widget)
            
            # If a light is selected, select it in the light linking widget
            if self.current_light_prim:
                light_path = str(self.current_light_prim.GetPath())
                for i in range(self.light_linking_widget.light_list.count()):
                    item = self.light_linking_widget.light_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == light_path:
                        self.light_linking_widget.light_list.setCurrentItem(item)
                        break
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec()
        else:
            # Show existing dialog
            self.light_linking_widget.set_stage(self.stage)
            # Find parent dialog and show it
            parent = self.light_linking_widget.parent()
            if parent and isinstance(parent, QDialog):
                parent.show()
                parent.raise_()
    
    def on_linking_changed(self):
        """Handle light linking change"""
        # Emit signal to update viewport if needed
        pass
    
    def on_property_changed(self):
        """Handle property change"""
        if not self.current_light_prim or not USD_AVAILABLE:
            return
        
        try:
            from pxr import UsdLux
            
            light_api = UsdLux.LightAPI(self.current_light_prim)
            if light_api:
                # Update intensity
                intensity_attr = light_api.GetIntensityAttr()
                if intensity_attr:
                    intensity_attr.Set(self.intensity_spin.value())
                
                # Update exposure
                exposure_attr = light_api.GetExposureAttr()
                if exposure_attr:
                    exposure_attr.Set(self.exposure_spin.value())
                
                # Update color
                color_attr = light_api.GetColorAttr()
                if color_attr:
                    color = (
                        self.current_color.red() / 255.0,
                        self.current_color.green() / 255.0,
                        self.current_color.blue() / 255.0
                    )
                    color_attr.Set(color)
            
            self.light_changed.emit(str(self.current_light_prim.GetPath()))
        except Exception as e:
            print(f"Error updating light properties: {e}")

