"""
Help System & Tooltips
Context-sensitive help and tooltips for easy use
"""

from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QDialog, QToolTip
from PySide6.QtCore import Qt


class HelpSystem:
    """Manages help system and tooltips"""
    
    def __init__(self):
        self.help_database: Dict[str, str] = {
            # Viewer features
            'viewport': "3D viewport for viewing USD scenes. Left-click to rotate, middle-click to pan, scroll to zoom.",
            'hierarchy': "Scene hierarchy tree showing all prims in the stage. Double-click variant sets to change selection.",
            'timeline': "Animation timeline. Drag to scrub, use buttons to play/pause and navigate frames.",
            'stage_info': "Stage information panel showing metadata, statistics, and validation results.",
            
            # Tools
            'layer_composition': "View and manage layer composition including subLayers, references, and payloads.",
            'animation_editor': "Edit animation curves for time-sampled attributes. Add/remove keyframes and adjust values.",
            'material_editor': "Edit material properties including colors, textures, and shader networks.",
            'scene_search': "Search and filter prims by name, type, path, or metadata. Double-click results to select.",
            'camera_manager': "Manage cameras: create, switch between, and edit camera properties.",
            'prim_properties': "Edit selected prim properties including transforms and attributes.",
            'collection_editor': "Edit collection membership and properties for material binding and organization.",
            'primvar_editor': "Edit primvar values and interpolation modes for custom attributes.",
            'render_settings': "Configure render settings including resolution, camera, and render products.",
            'stage_variables': "Manage stage variables for dynamic asset paths and configuration.",
            
            # Conversion
            'converter': "Convert 3D files (FBX, OBJ, Alembic, glTF, etc.) to USD format with options for scale and axis.",
            
            # Viewport
            'hydra_rendering': "Use Hydra 2.0 for GPU-accelerated rendering with proper material support.",
            'grid': "Toggle reference grid display for scene navigation.",
            'axis': "Toggle coordinate axis display.",
            'frame_all': "Frame camera to fit all geometry in the scene.",
            
            # Payloads
            'load_payloads': "Load all payloads in the stage for full scene access.",
            'unload_payloads': "Unload all payloads to improve performance on large scenes.",
        }
    
    def get_tooltip(self, widget_name: str) -> str:
        """Get tooltip text for a widget"""
        return self.help_database.get(widget_name, f"Help for {widget_name}")
    
    def set_tooltip(self, widget: QWidget, widget_name: str):
        """Set tooltip for a widget"""
        tooltip_text = self.get_tooltip(widget_name)
        widget.setToolTip(tooltip_text)
    
    def get_help_text(self, topic: str) -> str:
        """Get detailed help text for a topic"""
        return self.help_database.get(topic, f"No help available for {topic}")


class HelpDialog(QDialog):
    """Help dialog widget"""
    
    def __init__(self, parent=None):
        from PySide6.QtWidgets import QVBoxLayout, QTextEdit, QPushButton
        
        super().__init__(parent)
        self.setWindowTitle("xStage Help")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml(self._generate_help_html())
        layout.addWidget(help_text)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def _generate_help_html(self) -> str:
        """Generate help HTML"""
        html = """
        <h1>xStage USD Viewer Help</h1>
        
        <h2>Basic Usage</h2>
        <p><b>Opening Files:</b> File → Open USD or drag and drop USD files</p>
        <p><b>Converting Files:</b> File → Import and Convert to convert FBX, OBJ, Alembic, etc. to USD</p>
        
        <h2>Viewport Controls</h2>
        <ul>
        <li><b>Left Click + Drag:</b> Rotate camera</li>
        <li><b>Middle Click + Drag:</b> Pan camera</li>
        <li><b>Scroll Wheel:</b> Zoom in/out</li>
        <li><b>F Key:</b> Frame all geometry</li>
        </ul>
        
        <h2>Tools</h2>
        <ul>
        <li><b>Layer Composition:</b> View and manage USD layer stack</li>
        <li><b>Animation Editor:</b> Edit animation curves</li>
        <li><b>Material Editor:</b> Edit material properties</li>
        <li><b>Scene Search:</b> Search and filter prims</li>
        <li><b>Camera Management:</b> Manage cameras</li>
        <li><b>Prim Properties:</b> Edit selected prim properties</li>
        </ul>
        
        <h2>Keyboard Shortcuts</h2>
        <ul>
        <li><b>Ctrl+O:</b> Open USD file</li>
        <li><b>Ctrl+I:</b> Import and convert</li>
        <li><b>F:</b> Frame all</li>
        </ul>
        
        <h2>Pipeline Integration</h2>
        <p>xStage is designed for VFX pipeline integration. Use Tools menu for advanced features.</p>
        """
        return html

