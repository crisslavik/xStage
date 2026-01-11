"""
Viewport Overlay & HUD System
FPS counter, statistics, and information overlays
"""

from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint
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
        self.color_space_info: Dict[str, any] = {}
        self.scene_metrics: Dict[str, any] = {}
        
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
    
    def set_color_space_info(self, info: Dict[str, any]):
        """Set color space information"""
        self.color_space_info = info
        self.update()
    
    def set_scene_metrics(self, metrics: Dict[str, any]):
        """Set scene performance metrics"""
        self.scene_metrics = metrics
        self.update()
    
    def paintEvent(self, event):
        """Paint overlay information in a box like Blender"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Set font
            font = QFont("Monospace", 10)
            font.setBold(True)
            painter.setFont(font)
            
            # Background color (semi-transparent dark box)
            bg_color = QColor(0, 0, 0, 200)
            text_color = QColor(255, 255, 255, 255)
            highlight_color = QColor(100, 150, 255, 255)
            border_color = QColor(100, 100, 100, 255)
            
            # Calculate content size first
            content_lines = []
            if self.show_fps:
                content_lines.append(f"FPS: {self.fps:.1f}")
            if self.show_stats and self.stats:
                for key, value in list(self.stats.items())[:5]:
                    content_lines.append(f"{key}: {value}")
            if self.show_memory and self.memory_usage > 0:
                content_lines.append(f"Memory: {self.memory_usage:.1f} MB")
            if self.show_selection and self.selected_prim:
                sel_text = f"Selected: {self.selected_prim[:40]}"
                if len(self.selected_prim) > 40:
                    sel_text += "..."
                content_lines.append(sel_text)
            if self.show_camera and self.camera_info:
                cam_text = f"Camera: {self.camera_info.get('name', 'N/A')}"
                if 'fov' in self.camera_info:
                    cam_text += f" | FOV: {self.camera_info['fov']:.1f}°"
                content_lines.append(cam_text)
            if self.color_space_info and self.color_space_info.get('ocio_available', False):
                asset_cs = self.color_space_info.get('asset_color_space', 'Unknown')
                display_cs = self.color_space_info.get('display_color_space', 'Unknown')
                content_lines.append(f"Color Space: {asset_cs} → {display_cs}")
            
            if not content_lines:
                return  # Nothing to draw
            
            # Calculate box dimensions
            line_height = 18
            padding = 10
            spacing = 4
            max_width = 0
            for line in content_lines:
                text_rect = painter.fontMetrics().boundingRect(line)
                max_width = max(max_width, text_rect.width())
            
            box_width = max_width + padding * 2
            box_height = len(content_lines) * (line_height + spacing) + padding * 2 - spacing
            
            # Position in top-left corner
            x_offset = 10
            y_offset = 10
            
            # Draw background box with border
            box_rect = QRect(x_offset, y_offset, box_width, box_height)
            painter.fillRect(box_rect, bg_color)
            painter.setPen(QPen(border_color, 1))
            painter.drawRect(box_rect)
            
            # Draw text inside box
            y_pos = y_offset + padding + line_height
            
            # Draw all content lines
            for i, line in enumerate(content_lines):
                # Use highlight color for selection and color space
                use_highlight = (self.show_selection and self.selected_prim and line.startswith("Selected:")) or \
                               (self.color_space_info and line.startswith("Color Space:"))
                pen_color = highlight_color if use_highlight else text_color
                
                painter.setPen(QPen(pen_color))
                painter.drawText(x_offset + padding, y_pos, line)
                y_pos += line_height + spacing
            
            # Draw scene metrics (performance stats)
            if self.scene_metrics:
                y_offset += 5  # Spacing
                
                # Polygon count
                polygon_counts = self.scene_metrics.get('polygon_counts', {})
                if polygon_counts:
                    total_polys = polygon_counts.get('total_polygons', 0)
                    total_objs = polygon_counts.get('total_objects', 0)
                    poly_text = f"Polygons: {total_polys:,} ({total_objs} objects)"
                    
                    text_rect = painter.fontMetrics().boundingRect(poly_text)
                    bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                    bg_rect.moveTopLeft(QPoint(x_offset, y_offset))
                    
                    painter.fillRect(bg_rect, bg_color)
                    painter.setPen(QPen(text_color))
                    painter.drawText(x_offset, y_offset + text_rect.height(), poly_text)
                    y_offset += line_height
                
                # Texture memory
                texture_memory = self.scene_metrics.get('texture_memory', {})
                if texture_memory:
                    tex_mem = texture_memory.get('total_memory_mb', 0.0)
                    tex_count = texture_memory.get('texture_count', 0)
                    tex_text = f"Textures: {tex_mem:.1f} MB ({tex_count} textures)"
                    
                    text_rect = painter.fontMetrics().boundingRect(tex_text)
                    bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                    bg_rect.moveTopLeft(QPoint(x_offset, y_offset))
                    
                    painter.fillRect(bg_rect, bg_color)
                    painter.setPen(QPen(text_color))
                    painter.drawText(x_offset, y_offset + text_rect.height(), tex_text)
                    y_offset += line_height
                
                # Draw calls
                draw_calls = self.scene_metrics.get('draw_calls', {})
                if draw_calls:
                    est_draws = draw_calls.get('estimated_draw_calls', 0)
                    draw_text = f"Draw Calls: ~{est_draws}"
                    
                    text_rect = painter.fontMetrics().boundingRect(draw_text)
                    bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                    bg_rect.moveTopLeft(QPoint(x_offset, y_offset))
                    
                    painter.fillRect(bg_rect, bg_color)
                    painter.setPen(QPen(text_color))
                    painter.drawText(x_offset, y_offset + text_rect.height(), draw_text)
                    y_offset += line_height
                
                # File size
                file_size = self.scene_metrics.get('file_size', {})
                if file_size and file_size.get('total_size_mb', 0) > 0:
                    file_mb = file_size.get('total_size_mb', 0.0)
                    size_text = f"File Size: {file_mb:.2f} MB"
                    
                    text_rect = painter.fontMetrics().boundingRect(size_text)
                    bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                    bg_rect.moveTopLeft(QPoint(x_offset, y_offset))
                    
                    painter.fillRect(bg_rect, bg_color)
                    painter.setPen(QPen(text_color))
                    painter.drawText(x_offset, y_offset + text_rect.height(), size_text)
                    y_offset += line_height
                
                # Complexity score
                complexity = self.scene_metrics.get('complexity', {})
                if complexity:
                    score = complexity.get('score', 0.0)
                    level = complexity.get('level', 'Unknown')
                    color_name = complexity.get('color', 'white')
                    
                    # Map color name to QColor
                    color_map = {
                        'green': QColor(100, 255, 100, 255),
                        'yellow': QColor(255, 255, 100, 255),
                        'orange': QColor(255, 165, 0, 255),
                        'red': QColor(255, 100, 100, 255),
                        'white': text_color
                    }
                    complexity_color = color_map.get(color_name, text_color)
                    
                    complexity_text = f"Complexity: {score:.1f}/100 ({level})"
                    
                    text_rect = painter.fontMetrics().boundingRect(complexity_text)
                    bg_rect = text_rect.adjusted(-padding, -padding, padding, padding)
                    bg_rect.moveTopLeft(QPoint(x_offset, y_offset))
                    
                    painter.fillRect(bg_rect, bg_color)
                    painter.setPen(QPen(complexity_color))
                    painter.drawText(x_offset, y_offset + text_rect.height(), complexity_text)
            
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
                    bg_rect.moveTopLeft(QPoint(x_right, y_bottom + i * line_height))
                    
                    painter.fillRect(bg_rect, bg_color)
                    painter.setPen(QPen(text_color))
                    painter.drawText(x_right, y_bottom + i * line_height + text_rect.height(), text)
        finally:
            painter.end()

