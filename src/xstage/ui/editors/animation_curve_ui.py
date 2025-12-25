"""
Animation Curve Editor UI
Graph widget for visualizing and editing time-sampled attributes
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QGroupBox,
    QSplitter, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor
from typing import Optional, List, Dict

from ...managers.animation_curves import AnimationCurveManager


class CurveGraphWidget(QWidget):
    """Widget for drawing animation curves"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.curve_data = None
        self.time_range = (0.0, 100.0)
        self.value_range = (0.0, 1.0)
        self.selected_keyframe = None
        self.setMinimumHeight(200)
    
    def set_curve_data(self, curve_data: Dict):
        """Set curve data to display"""
        self.curve_data = curve_data
        if curve_data:
            if 'time_range' in curve_data:
                self.time_range = curve_data['time_range']
            if 'value_range' in curve_data:
                self.value_range = curve_data['value_range']
        self.update()
    
    def paintEvent(self, event):
        """Draw the curve graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw background
        painter.fillRect(0, 0, width, height, QColor(40, 40, 40))
        
        if not self.curve_data or 'keyframes' not in self.curve_data:
            return
        
        # Calculate scale
        time_span = self.time_range[1] - self.time_range[0]
        value_span = self.value_range[1] - self.value_range[0]
        
        if time_span == 0 or value_span == 0:
            return
        
        # Draw grid
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        for i in range(5):
            x = int((i / 4.0) * width)
            painter.drawLine(x, 0, x, height)
            y = int((i / 4.0) * height)
            painter.drawLine(0, y, width, y)
        
        # Draw curve
        keyframes = self.curve_data['keyframes']
        if len(keyframes) < 2:
            return
        
        # Convert to screen coordinates
        points = []
        for kf in keyframes:
            time = kf['time']
            value = kf['value']
            
            # Handle different value types
            if isinstance(value, (int, float)):
                x = int(((time - self.time_range[0]) / time_span) * width)
                y = int(height - ((value - self.value_range[0]) / value_span) * height)
                points.append((x, y))
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                # Use first component for now
                x = int(((time - self.time_range[0]) / time_span) * width)
                y = int(height - ((value[0] - self.value_range[0]) / value_span) * height)
                points.append((x, y))
        
        # Draw curve line
        if len(points) > 1:
            painter.setPen(QPen(QColor(100, 150, 255), 2))
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Draw keyframes
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        for i, (x, y) in enumerate(points):
            if i == self.selected_keyframe:
                painter.setBrush(QColor(255, 200, 0))
            else:
                painter.setBrush(QColor(100, 150, 255))
            painter.drawEllipse(x - 4, y - 4, 8, 8)


class AnimationCurveEditorWidget(QWidget):
    """Main animation curve editor widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self.current_prim = None
        self.current_attr = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Animation Curve Editor</b>")
        layout.addWidget(title)
        
        # Splitter for tree and graph
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Attribute tree
        tree_widget = QWidget()
        tree_layout = QVBoxLayout()
        
        tree_label = QLabel("Animated Attributes:")
        tree_layout.addWidget(tree_label)
        
        self.attr_tree = QTreeWidget()
        self.attr_tree.setHeaderLabels(["Prim", "Attribute", "Keyframes"])
        self.attr_tree.itemSelectionChanged.connect(self.on_attribute_selected)
        tree_layout.addWidget(self.attr_tree)
        
        tree_widget.setLayout(tree_layout)
        splitter.addWidget(tree_widget)
        
        # Right: Curve graph
        graph_widget = QWidget()
        graph_layout = QVBoxLayout()
        
        self.curve_graph = CurveGraphWidget()
        graph_layout.addWidget(self.curve_graph)
        
        # Keyframe controls
        controls_group = QGroupBox("Keyframe Controls")
        controls_layout = QVBoxLayout()
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time:"))
        self.time_spinbox = QDoubleSpinBox()
        self.time_spinbox.setRange(-10000, 10000)
        self.time_spinbox.setDecimals(3)
        time_layout.addWidget(self.time_spinbox)
        controls_layout.addLayout(time_layout)
        
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setRange(-1000000, 1000000)
        self.value_spinbox.setDecimals(3)
        value_layout.addWidget(self.value_spinbox)
        controls_layout.addLayout(value_layout)
        
        button_layout = QHBoxLayout()
        self.add_keyframe_btn = QPushButton("Add Keyframe")
        self.add_keyframe_btn.clicked.connect(self.add_keyframe)
        button_layout.addWidget(self.add_keyframe_btn)
        
        self.remove_keyframe_btn = QPushButton("Remove Keyframe")
        self.remove_keyframe_btn.clicked.connect(self.remove_keyframe)
        button_layout.addWidget(self.remove_keyframe_btn)
        controls_layout.addLayout(button_layout)
        
        controls_group.setLayout(controls_layout)
        graph_layout.addWidget(controls_group)
        
        graph_widget.setLayout(graph_layout)
        splitter.addWidget(graph_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        self.stage = stage
        self.refresh()
    
    def refresh(self):
        """Refresh animated attributes"""
        self.attr_tree.clear()
        
        if not self.stage:
            return
        
        # Get all animated attributes
        all_animated = AnimationCurveManager.get_all_animated_attributes(self.stage)
        
        for prim_data in all_animated:
            prim_item = QTreeWidgetItem([prim_data['prim_path'], "", ""])
            self.attr_tree.addTopLevelItem(prim_item)
            
            for attr_info in prim_data['attributes']:
                attr_item = QTreeWidgetItem([
                    "",
                    attr_info['name'],
                    str(len(attr_info['time_samples']))
                ])
                attr_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'prim_path': prim_data['prim_path'],
                    'attr_name': attr_info['name'],
                })
                prim_item.addChild(attr_item)
        
        self.attr_tree.expandAll()
    
    def on_attribute_selected(self):
        """Handle attribute selection"""
        selected = self.attr_tree.currentItem()
        if not selected:
            return
        
        data = selected.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        # Get attribute
        prim = self.stage.GetPrimAtPath(data['prim_path'])
        if not prim:
            return
        
        attr = prim.GetAttribute(data['attr_name'])
        if not attr:
            return
        
        self.current_prim = prim
        self.current_attr = attr
        
        # Get curve data
        curve_data = AnimationCurveManager.get_curve_data(attr)
        self.curve_graph.set_curve_data(curve_data)
    
    def add_keyframe(self):
        """Add a keyframe"""
        if not self.current_attr:
            return
        
        time = self.time_spinbox.value()
        value = self.value_spinbox.value()
        
        AnimationCurveManager.set_keyframe(self.current_attr, time, value)
        self.on_attribute_selected()  # Refresh
    
    def remove_keyframe(self):
        """Remove a keyframe"""
        if not self.current_attr:
            return
        
        time = self.time_spinbox.value()
        AnimationCurveManager.remove_keyframe(self.current_attr, time)
        self.on_attribute_selected()  # Refresh

