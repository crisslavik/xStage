"""
Timeline Widget
Playback controls and timeline slider for USD animation
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSlider, QLabel, QSpinBox
)
from PySide6.QtCore import Qt, Signal


class TimelineWidget(QWidget):
    """Timeline widget with playback controls"""
    
    # Signals
    frame_changed = Signal(int)
    play_toggled = Signal(bool)
    fps_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = False
        self.setup_ui()
        
    def setup_ui(self):
        """Setup timeline UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Button style
        button_style = """
            QPushButton {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """
        
        # First frame button
        first_frame_btn = QPushButton("⏮")
        first_frame_btn.setToolTip("First Frame")
        first_frame_btn.setFixedSize(32, 32)
        first_frame_btn.clicked.connect(self.goto_first_frame)
        first_frame_btn.setStyleSheet(button_style + "QPushButton { font-size: 14pt; }")
        layout.addWidget(first_frame_btn)
        
        # Previous frame button
        prev_frame_btn = QPushButton("◀")
        prev_frame_btn.setToolTip("Previous Frame")
        prev_frame_btn.setFixedSize(32, 32)
        prev_frame_btn.clicked.connect(self.prev_frame)
        prev_frame_btn.setStyleSheet(button_style + "QPushButton { font-size: 14pt; }")
        layout.addWidget(prev_frame_btn)
        
        # Play/Pause button
        self.play_button = QPushButton("▶")
        self.play_button.setToolTip("Play/Pause")
        self.play_button.setFixedSize(40, 32)
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setStyleSheet(button_style + "QPushButton { font-size: 16pt; font-weight: bold; }")
        layout.addWidget(self.play_button)
        
        # Next frame button
        next_frame_btn = QPushButton("▶")
        next_frame_btn.setToolTip("Next Frame")
        next_frame_btn.setFixedSize(32, 32)
        next_frame_btn.clicked.connect(self.next_frame)
        next_frame_btn.setStyleSheet(button_style + "QPushButton { font-size: 14pt; }")
        layout.addWidget(next_frame_btn)
        
        # Last frame button
        last_frame_btn = QPushButton("⏭")
        last_frame_btn.setToolTip("Last Frame")
        last_frame_btn.setFixedSize(32, 32)
        last_frame_btn.clicked.connect(self.goto_last_frame)
        last_frame_btn.setStyleSheet(button_style + "QPushButton { font-size: 14pt; }")
        layout.addWidget(last_frame_btn)
        
        layout.addSpacing(20)
        
        # Timeline slider
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.valueChanged.connect(self.on_slider_changed)
        self.timeline_slider.setMinimumWidth(200)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 6px;
                background: #333;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2a82da;
                border: 1px solid #1a5a9a;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #3a92ea;
            }
        """)
        layout.addWidget(self.timeline_slider, 1)
        
        layout.addSpacing(10)
        
        # Frame and time display
        self.frame_label = QLabel("Frame: 0")
        self.frame_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 4px; color: palette(window-text);")
        layout.addWidget(self.frame_label)
        
        self.time_label = QLabel("Time: 0.00s")
        self.time_label.setStyleSheet("font-weight: bold; font-size: 10pt; padding: 4px; color: palette(window-text);")
        layout.addWidget(self.time_label)
        
        layout.addSpacing(20)
        
        # FPS control
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet("color: #888; font-size: 10pt;")
        layout.addWidget(fps_label)
        
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 120)
        self.fps_spinbox.setValue(24)
        self.fps_spinbox.setFixedWidth(60)
        self.fps_spinbox.valueChanged.connect(self.on_fps_changed)
        layout.addWidget(self.fps_spinbox)
        
        self.setLayout(layout)
    
    def set_time_range(self, start: int, end: int):
        """Set timeline range"""
        self.timeline_slider.setRange(start, end)
        self.timeline_slider.setValue(start)
    
    def set_current_frame(self, frame: int):
        """Set current frame"""
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(frame)
        self.timeline_slider.blockSignals(False)
        self.frame_label.setText(f"Frame: {frame}")
    
    def set_current_time(self, time: float):
        """Set current time display"""
        self.time_label.setText(f"Time: {time:.2f}s")
    
    def set_fps(self, fps: int):
        """Set FPS"""
        self.fps_spinbox.blockSignals(True)
        self.fps_spinbox.setValue(fps)
        self.fps_spinbox.blockSignals(False)
    
    def toggle_playback(self):
        """Toggle play/pause"""
        self.is_playing = not self.is_playing
        self.play_button.setText("⏸" if self.is_playing else "▶")
        self.play_toggled.emit(self.is_playing)
    
    def stop_playback(self):
        """Stop playback"""
        self.is_playing = False
        self.play_button.setText("▶")
    
    def goto_first_frame(self):
        """Go to first frame"""
        self.timeline_slider.setValue(self.timeline_slider.minimum())
    
    def goto_last_frame(self):
        """Go to last frame"""
        self.timeline_slider.setValue(self.timeline_slider.maximum())
    
    def prev_frame(self):
        """Go to previous frame"""
        current = self.timeline_slider.value()
        self.timeline_slider.setValue(max(current - 1, self.timeline_slider.minimum()))
    
    def next_frame(self):
        """Go to next frame"""
        current = self.timeline_slider.value()
        self.timeline_slider.setValue(min(current + 1, self.timeline_slider.maximum()))
    
    def on_slider_changed(self, value: int):
        """Handle slider change"""
        self.frame_changed.emit(value)
    
    def on_fps_changed(self, value: int):
        """Handle FPS change"""
        self.fps_changed.emit(value)
