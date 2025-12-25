"""
Annotations UI
Drawing tools and arrow options for scene annotations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QColorDialog, QSpinBox,
    QDoubleSpinBox, QGroupBox, QFormLayout, QTextEdit, QComboBox,
    QCheckBox, QFileDialog, QMessageBox, QToolButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QColor, QPen, QPainter, QPainterPath
from typing import Optional, List, Tuple

from ...utils.annotations import AnnotationManager, Annotation, AnnotationType


class AnnotationCanvas(QWidget):
    """Canvas for drawing annotations"""
    
    annotation_drawn = Signal(list)  # Emits list of points
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = False
        self.current_points = []
        self.current_color = QColor(0, 255, 0)
        self.current_size = 2.0
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
    
    def set_drawing_color(self, color: QColor):
        """Set drawing color"""
        self.current_color = color
    
    def set_drawing_size(self, size: float):
        """Set drawing size"""
        self.current_size = size
    
    def mousePressEvent(self, event):
        """Start drawing"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.current_points = [event.position().toPoint()]
            self.update()
    
    def mouseMoveEvent(self, event):
        """Continue drawing"""
        if self.drawing:
            self.current_points.append(event.position().toPoint())
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Finish drawing"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if len(self.current_points) > 1:
                # Convert to list of tuples
                points = [(p.x(), p.y()) for p in self.current_points]
                self.annotation_drawn.emit(points)
            self.current_points = []
            self.update()
    
    def paintEvent(self, event):
        """Paint the canvas"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(50, 50, 50))
        
        # Draw current drawing
        if self.current_points:
            pen = QPen(self.current_color, self.current_size)
            painter.setPen(pen)
            
            path = QPainterPath()
            path.moveTo(self.current_points[0])
            for point in self.current_points[1:]:
                path.lineTo(point)
            
            painter.drawPath(path)
    
    def clear(self):
        """Clear the canvas"""
        self.current_points = []
        self.update()


class AnnotationsWidget(QWidget):
    """Widget for managing annotations"""
    
    annotation_added = Signal(str)  # Emits annotation ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.annotation_manager = AnnotationManager()
        self.current_annotation_type = AnnotationType.TEXT
        self.current_color = QColor(255, 255, 0)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Scene Annotations</b>")
        layout.addWidget(title)
        
        # Annotation type selector
        type_group = QGroupBox("Annotation Type")
        type_layout = QHBoxLayout()
        
        self.type_button_group = QButtonGroup()
        
        text_btn = QToolButton()
        text_btn.setText("Text")
        text_btn.setCheckable(True)
        text_btn.setChecked(True)
        text_btn.clicked.connect(lambda: self.set_annotation_type(AnnotationType.TEXT))
        self.type_button_group.addButton(text_btn, 0)
        type_layout.addWidget(text_btn)
        
        arrow_btn = QToolButton()
        arrow_btn.setText("Arrow")
        arrow_btn.setCheckable(True)
        arrow_btn.clicked.connect(lambda: self.set_annotation_type(AnnotationType.ARROW))
        self.type_button_group.addButton(arrow_btn, 1)
        type_layout.addWidget(arrow_btn)
        
        draw_btn = QToolButton()
        draw_btn.setText("Draw")
        draw_btn.setCheckable(True)
        draw_btn.clicked.connect(lambda: self.set_annotation_type(AnnotationType.DRAWING))
        self.type_button_group.addButton(draw_btn, 2)
        type_layout.addWidget(draw_btn)
        
        rect_btn = QToolButton()
        rect_btn.setText("Rect")
        rect_btn.setCheckable(True)
        rect_btn.clicked.connect(lambda: self.set_annotation_type(AnnotationType.RECTANGLE))
        self.type_button_group.addButton(rect_btn, 3)
        type_layout.addWidget(rect_btn)
        
        circle_btn = QToolButton()
        circle_btn.setText("Circle")
        circle_btn.setCheckable(True)
        circle_btn.clicked.connect(lambda: self.set_annotation_type(AnnotationType.CIRCLE))
        self.type_button_group.addButton(circle_btn, 4)
        type_layout.addWidget(circle_btn)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Drawing canvas (for freehand drawing)
        self.canvas = AnnotationCanvas()
        self.canvas.annotation_drawn.connect(self.on_drawing_complete)
        self.canvas.set_drawing_color(self.current_color)
        layout.addWidget(self.canvas)
        
        # Annotation properties
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout()
        
        # Color picker
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.update_color_button()
        props_layout.addRow("Color:", self.color_btn)
        
        # Size
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(0.1, 10.0)
        self.size_spin.setValue(1.0)
        self.size_spin.setDecimals(1)
        props_layout.addRow("Size:", self.size_spin)
        
        # Arrow head size
        self.arrow_head_spin = QDoubleSpinBox()
        self.arrow_head_spin.setRange(0.1, 5.0)
        self.arrow_head_spin.setValue(0.5)
        self.arrow_head_spin.setDecimals(2)
        props_layout.addRow("Arrow Head Size:", self.arrow_head_spin)
        
        # Text input
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(60)
        self.text_edit.setPlaceholderText("Enter annotation text...")
        props_layout.addRow("Text:", self.text_edit)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        # Annotations list
        list_group = QGroupBox("Annotations")
        list_layout = QVBoxLayout()
        
        self.annotations_list = QListWidget()
        self.annotations_list.itemSelectionChanged.connect(self.on_annotation_selected)
        list_layout.addWidget(self.annotations_list)
        
        list_buttons = QHBoxLayout()
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_selected)
        list_buttons.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        list_buttons.addWidget(clear_btn)
        
        list_layout.addLayout(list_buttons)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Export/Import
        io_group = QGroupBox("Export/Import")
        io_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self.export_annotations)
        io_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Import...")
        import_btn.clicked.connect(self.import_annotations)
        io_layout.addWidget(import_btn)
        
        io_group.setLayout(io_layout)
        layout.addWidget(io_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_annotation_type(self, ann_type: AnnotationType):
        """Set current annotation type"""
        self.current_annotation_type = ann_type
        self.canvas.setVisible(ann_type == AnnotationType.DRAWING)
    
    def choose_color(self):
        """Choose annotation color"""
        color = QColorDialog.getColor(self.current_color, self, "Choose Color")
        if color.isValid():
            self.current_color = color
            self.canvas.set_drawing_color(color)
            self.update_color_button()
    
    def update_color_button(self):
        """Update color button appearance"""
        self.color_btn.setStyleSheet(
            f"background-color: {self.current_color.name()};"
            f"color: {'white' if self.current_color.lightness() < 128 else 'black'};"
        )
    
    def on_drawing_complete(self, points: List[Tuple[float, float]]):
        """Handle drawing completion"""
        if self.current_annotation_type == AnnotationType.DRAWING:
            viewport_pos = (0, 0)  # Would be actual viewport position
            color = (
                self.current_color.redF(),
                self.current_color.greenF(),
                self.current_color.blueF(),
                self.current_color.alphaF()
            )
            ann_id = self.annotation_manager.add_drawing_annotation(
                points, viewport_pos, color, self.size_spin.value()
            )
            self.annotation_added.emit(ann_id)
            self.refresh_list()
            self.canvas.clear()
    
    def add_text_annotation(self, position: Tuple[float, float, float], prim_path: Optional[str] = None):
        """Add a text annotation"""
        text = self.text_edit.toPlainText()
        if not text:
            return
        
        color = (
            self.current_color.redF(),
            self.current_color.greenF(),
            self.current_color.blueF(),
            self.current_color.alphaF()
        )
        
        ann_id = self.annotation_manager.add_text_annotation(
            text, position, prim_path, color
        )
        self.annotation_added.emit(ann_id)
        self.refresh_list()
        self.text_edit.clear()
    
    def add_arrow_annotation(self, start: Tuple[float, float, float], end: Tuple[float, float, float]):
        """Add an arrow annotation"""
        text = self.text_edit.toPlainText()
        color = (
            self.current_color.redF(),
            self.current_color.greenF(),
            self.current_color.blueF(),
            self.current_color.alphaF()
        )
        
        ann_id = self.annotation_manager.add_arrow_annotation(
            start, end, text, color, self.arrow_head_spin.value()
        )
        self.annotation_added.emit(ann_id)
        self.refresh_list()
        self.text_edit.clear()
    
    def remove_selected(self):
        """Remove selected annotation"""
        selected = self.annotations_list.currentItem()
        if selected:
            ann_id = selected.data(Qt.ItemDataRole.UserRole)
            if self.annotation_manager.remove_annotation(ann_id):
                self.refresh_list()
    
    def clear_all(self):
        """Clear all annotations"""
        reply = QMessageBox.question(
            self, "Clear All", "Remove all annotations?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.annotation_manager.annotations.clear()
            self.refresh_list()
    
    def refresh_list(self):
        """Refresh annotations list"""
        self.annotations_list.clear()
        for ann in self.annotation_manager.get_visible_annotations():
            item_text = f"{ann.type.value}: {ann.text[:30] if ann.text else 'No text'}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, ann.id)
            self.annotations_list.addItem(item)
    
    def export_annotations(self):
        """Export annotations to file"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Annotations", "", "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            if self.annotation_manager.export_annotations(filepath):
                QMessageBox.information(self, "Success", "Annotations exported successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to export annotations")
    
    def import_annotations(self):
        """Import annotations from file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Annotations", "", "JSON Files (*.json);;All Files (*)"
        )
        if filepath:
            if self.annotation_manager.import_annotations(filepath):
                self.refresh_list()
                QMessageBox.information(self, "Success", "Annotations imported successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to import annotations")
    
    def set_stage(self, stage):
        """Set the USD stage"""
        self.annotation_manager.stage = stage

