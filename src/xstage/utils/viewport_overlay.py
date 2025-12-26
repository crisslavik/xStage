"""
Viewport Overlay & HUD System
FPS counter, statistics, and information overlays
"""

from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QFont, QColor, QPen
import time

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class ViewportOverlay(QWidget):
    """Overlay widget for viewport HUD information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # Overlay settings
        self.show_fps = True
        self.show_stats = True
        self.show_memory = True
        self.show_selection = True
        self.show_camera = True
        self.show_grid = True
        
        # Data
        self.fps = 0.0
        self.frame_count = 0
        self.last_time = time.time()
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)  # Update every second
        
        # Statistics
        self.stats: Dict[str, any] = {}
        self.selected_prim: Optional[str] = None
        self.camera_info: Dict[str, any] = {}
        
        # Memory tracking
        self.memory_usage = 0.0
        self.update_memory()
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory)
        self.memory_timer.start(2000)  # Update every 2 seconds
    
    def update_fps(self):
        """Update FPS calculation"""
        current_time = time.time()
        elapsed = current_time - self.last_time
        if elapsed > 0:
            self.fps = self.frame_count / elapsed
        self.frame_count = 0
        self.last_time = current_time
        self.update()
    
    def record_frame(self):
        """Record a frame render"""
        self.frame_count += 1
    
    def update_memory(self):
        """Update memory usage"""
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                self.memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
            except:
                self.memory_usage = 0.0
        self.update()
    
    def set_stats(self, stats: Dict[str, any]):
        """Set scene statistics"""
        self.stats = stats
        self.update()
    
    def set_selected_prim(self, prim_path: Optional[str]):
        """Set selected prim path"""
        self.selected_prim = prim_path
        self.update()
    
    def set_camera_info(self, info: Dict[str, any]):
        """Set camera information"""
        self.camera_info = info
        self.update()
    
    def paintEvent(self, event):
        """Paint overlay information"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set font
        font = QFont("Monospace", 10)
        font.setBold(True)
        painter.setFont(font)
        
        # Background color (semi-transparent)
        bg_color = QColor(0, 0, 0, 180)
        text_color = QColor(255, 255, 255, 255)
        highlight_color = QColor(100, 150, 255, 255)
        
        y_offset = 10
        x_offset = 10
        line_height = 18
        padding = 5
        
        # Draw FPS
        if self.show_fps:
            fps_text = f"FPS: {self.fps:.1f}"
            text_rect = painter.fontMetrics().boundingRect(fps_text)
            bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
            bg_rect.moveTopLeft((x_offset, y_offset))
            
            painter.fillRect(bg_rect, bg_color)
            painter.setPen(QPen(text_color))
            painter.drawText(x_offset, y_offset + text_rect.height(), fps_text)
            y_offset += line_height + 5
        
        # Draw statistics
        if self.show_stats and self.stats:
            for key, value in list(self.stats.items())[:5]:  # Show first 5 stats
                stat_text = f"{key}: {value}"
                text_rect = painter.fontMetrics().boundingRect(stat_text)
                bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                bg_rect.moveTopLeft((x_offset, y_offset))
                
                painter.fillRect(bg_rect, bg_color)
                painter.setPen(QPen(text_color))
                painter.drawText(x_offset, y_offset + text_rect.height(), stat_text)
                y_offset += line_height
        
        # Draw memory usage
        if self.show_memory and self.memory_usage > 0:
            memory_text = f"Memory: {self.memory_usage:.1f} MB"
            text_rect = painter.fontMetrics().boundingRect(memory_text)
            bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
            bg_rect.moveTopLeft((x_offset, y_offset))
            
            painter.fillRect(bg_rect, bg_color)
            painter.setPen(QPen(text_color))
            painter.drawText(x_offset, y_offset + text_rect.height(), memory_text)
            y_offset += line_height + 5
        
        # Draw selection info
        if self.show_selection and self.selected_prim:
            selection_text = f"Selected: {self.selected_prim[:40]}"
            if len(self.selected_prim) > 40:
                selection_text += "..."
            text_rect = painter.fontMetrics().boundingRect(selection_text)
            bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
            bg_rect.moveTopLeft((x_offset, y_offset))
            
            painter.fillRect(bg_rect, bg_color)
            painter.setPen(QPen(highlight_color))
            painter.drawText(x_offset, y_offset + text_rect.height(), selection_text)
            y_offset += line_height + 5
        
        # Draw camera info
        if self.show_camera and self.camera_info:
            camera_text = f"Camera: {self.camera_info.get('name', 'N/A')}"
            if 'fov' in self.camera_info:
                camera_text += f" | FOV: {self.camera_info['fov']:.1f}°"
            text_rect = painter.fontMetrics().boundingRect(camera_text)
            bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
            bg_rect.moveTopLeft((x_offset, y_offset))
            
            painter.fillRect(bg_rect, bg_color)
            painter.setPen(QPen(text_color))
            painter.drawText(x_offset, y_offset + text_rect.height(), camera_text)
        
        # Draw bottom-right corner info (grid, axis)
        if self.show_grid:
            width = self.width()
            height = self.height()
            grid_text = "Grid: ON" if self.stats.get('grid_enabled', False) else "Grid: OFF"
            axis_text = "Axis: ON" if self.stats.get('axis_enabled', False) else "Axis: OFF"
            
            y_bottom = height - 40
            x_right = width - 150
            
            for i, text in enumerate([grid_text, axis_text]):
                text_rect = painter.fontMetrics().boundingRect(text)
                bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                bg_rect.moveTopLeft((x_right, y_bottom + i * line_height))
                
                painter.fillRect(bg_rect, bg_color)
                painter.setPen(QPen(text_color))
                painter.drawText(x_right, y_bottom + i * line_height + text_rect.height(), text)

