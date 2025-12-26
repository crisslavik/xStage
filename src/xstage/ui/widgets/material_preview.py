"""
Material Preview Widget
Preview materials with sphere rendering
"""

from typing import Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *

try:
    from pxr import Usd, UsdShade, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class MaterialPreviewWidget(QOpenGLWidget):
    """Widget for previewing materials on a sphere"""
    
    material_changed = Signal(str)  # Emits material path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.material_path: Optional[str] = None
        self.material_data: Optional[Dict] = None
        self.preview_mode = "sphere"  # sphere, plane, cube
        self.light_direction = [0.5, 0.5, 1.0]
        self.background_color = QColor(50, 50, 50)
    
    def set_material(self, material_path: str, material_data: Optional[Dict] = None):
        """Set material to preview"""
        self.material_path = material_path
        self.material_data = material_data
        self.update()
        self.material_changed.emit(material_path)
    
    def set_preview_mode(self, mode: str):
        """Set preview mode (sphere, plane, cube)"""
        self.preview_mode = mode
        self.update()
    
    def initializeGL(self):
        """Initialize OpenGL"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.5, 0.5, 1.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
    
    def resizeGL(self, w, h):
        """Handle resize"""
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = w / max(h, 1)
        gluPerspective(45.0, aspect, 0.1, 100.0)
    
    def paintGL(self):
        """Render material preview"""
        bg = self.background_color
        glClearColor(bg.redF(), bg.greenF(), bg.blueF(), 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)
        
        # Set material properties
        if self.material_data:
            self._apply_material_properties()
        else:
            # Default material
            glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)
        
        # Draw preview geometry
        if self.preview_mode == "sphere":
            self._draw_sphere()
        elif self.preview_mode == "plane":
            self._draw_plane()
        elif self.preview_mode == "cube":
            self._draw_cube()
    
    def _apply_material_properties(self):
        """Apply material properties from material_data"""
        if not self.material_data:
            return
        
        # Get base color
        base_color = [0.7, 0.7, 0.7, 1.0]
        if 'inputs' in self.material_data:
            if 'baseColor' in self.material_data['inputs']:
                color_value = self.material_data['inputs']['baseColor'].get('value', base_color)
                if isinstance(color_value, (list, tuple)) and len(color_value) >= 3:
                    base_color = list(color_value[:3]) + [1.0]
            elif 'diffuseColor' in self.material_data['inputs']:
                color_value = self.material_data['inputs']['diffuseColor'].get('value', base_color)
                if isinstance(color_value, (list, tuple)) and len(color_value) >= 3:
                    base_color = list(color_value[:3]) + [1.0]
        
        # Get metallic/roughness
        metallic = 0.0
        roughness = 0.5
        if 'inputs' in self.material_data:
            if 'metallic' in self.material_data['inputs']:
                metallic = float(self.material_data['inputs']['metallic'].get('value', 0.0))
            if 'roughness' in self.material_data['inputs']:
                roughness = float(self.material_data['inputs']['roughness'].get('value', 0.5))
        
        # Apply material
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [base_color[0] * 0.2, base_color[1] * 0.2, base_color[2] * 0.2, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, base_color)
        
        # Adjust specular based on metallic
        specular = [base_color[0] * metallic, base_color[1] * metallic, base_color[2] * metallic, 1.0]
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, (1.0 - roughness) * 128.0)
    
    def _draw_sphere(self):
        """Draw sphere for material preview"""
        from OpenGL.GLU import gluSphere
        import math
        
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluSphere(quad, 1.0, 32, 32)
        gluDeleteQuadric(quad)
    
    def _draw_plane(self):
        """Draw plane for material preview"""
        glBegin(GL_QUADS)
        glNormal3f(0, 0, 1)
        glVertex3f(-1, -1, 0)
        glVertex3f(1, -1, 0)
        glVertex3f(1, 1, 0)
        glVertex3f(-1, 1, 0)
        glEnd()
    
    def _draw_cube(self):
        """Draw cube for material preview"""
        # Front face
        glBegin(GL_QUADS)
        glNormal3f(0, 0, 1)
        glVertex3f(-1, -1, 1)
        glVertex3f(1, -1, 1)
        glVertex3f(1, 1, 1)
        glVertex3f(-1, 1, 1)
        glEnd()
        
        # Back face
        glBegin(GL_QUADS)
        glNormal3f(0, 0, -1)
        glVertex3f(-1, -1, -1)
        glVertex3f(-1, 1, -1)
        glVertex3f(1, 1, -1)
        glVertex3f(1, -1, -1)
        glEnd()
        
        # Top face
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-1, 1, -1)
        glVertex3f(-1, 1, 1)
        glVertex3f(1, 1, 1)
        glVertex3f(1, 1, -1)
        glEnd()
        
        # Bottom face
        glBegin(GL_QUADS)
        glNormal3f(0, -1, 0)
        glVertex3f(-1, -1, -1)
        glVertex3f(1, -1, -1)
        glVertex3f(1, -1, 1)
        glVertex3f(-1, -1, 1)
        glEnd()
        
        # Right face
        glBegin(GL_QUADS)
        glNormal3f(1, 0, 0)
        glVertex3f(1, -1, -1)
        glVertex3f(1, 1, -1)
        glVertex3f(1, 1, 1)
        glVertex3f(1, -1, 1)
        glEnd()
        
        # Left face
        glBegin(GL_QUADS)
        glNormal3f(-1, 0, 0)
        glVertex3f(-1, -1, -1)
        glVertex3f(-1, -1, 1)
        glVertex3f(-1, 1, 1)
        glVertex3f(-1, 1, -1)
        glEnd()

