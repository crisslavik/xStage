"""
Texture Preview Widget
Preview textures and materials
"""

from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QSizePolicy, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class TexturePreviewWidget(QWidget):
    """Widget for previewing textures"""
    
    texture_selected = Signal(str)  # Emits texture path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_texture_path: Optional[str] = None
        self.zoom_level = 1.0
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Texture Preview</b>")
        layout.addWidget(title)
        
        # Preview area
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(256, 256)
        self.preview_label.setMaximumSize(512, 512)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        self.preview_label.setText("No texture loaded")
        layout.addWidget(self.preview_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load Texture...")
        load_btn.clicked.connect(self.load_texture)
        controls_layout.addWidget(load_btn)
        
        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(self.zoom_in)
        controls_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(self.zoom_out)
        controls_layout.addWidget(zoom_out_btn)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_zoom)
        controls_layout.addWidget(reset_btn)
        
        layout.addLayout(controls_layout)
        
        # Info
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_texture(self, filepath: Optional[str] = None):
        """Load a texture file"""
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Load Texture", "",
                "Image Files (*.png *.jpg *.jpeg *.tif *.tiff *.exr *.hdr);;All Files (*)"
            )
        
        if not filepath or not Path(filepath).exists():
            return
        
        self.current_texture_path = filepath
        self.display_texture(filepath)
        self.texture_selected.emit(filepath)
    
    def display_texture(self, filepath: str):
        """Display texture in preview"""
        try:
            if PIL_AVAILABLE:
                img = Image.open(filepath)
                # Convert to QImage
                if img.mode == 'RGBA':
                    qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888)
                elif img.mode == 'RGB':
                    qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGB888)
                else:
                    img = img.convert('RGB')
                    qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGB888)
            else:
                # Fallback: try QImage directly
                qimage = QImage(filepath)
                if qimage.isNull():
                    self.preview_label.setText(f"Failed to load: {filepath}")
                    return
            
            # Scale image for preview
            scaled_size = QSize(256, 256)
            scaled_size.scale(qimage.size(), Qt.AspectRatioMode.KeepAspectRatio)
            scaled_pixmap = QPixmap.fromImage(qimage).scaled(
                scaled_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
            
            # Update info
            info_text = f"File: {Path(filepath).name}\n"
            info_text += f"Size: {qimage.width()}x{qimage.height()}\n"
            info_text += f"Format: {qimage.format()}"
            self.info_label.setText(info_text)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load texture:\n{e}")
            self.preview_label.setText("Error loading texture")
    
    def zoom_in(self):
        """Zoom in on texture"""
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self.update_preview()
    
    def zoom_out(self):
        """Zoom out on texture"""
        self.zoom_level = max(self.zoom_level / 1.2, 0.1)
        self.update_preview()
    
    def reset_zoom(self):
        """Reset zoom level"""
        self.zoom_level = 1.0
        self.update_preview()
    
    def update_preview(self):
        """Update preview with current zoom"""
        if self.current_texture_path:
            self.display_texture(self.current_texture_path)

