"""
OpenGL Viewport Widget
Basic OpenGL rendering for USD geometry
"""

from typing import Optional
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

from ..core.stage_manager import USDStageManager


class ViewerSettings:
    """Viewport display settings"""
    def __init__(self):
        self.background_color = (0.2, 0.2, 0.2, 1.0)
        self.grid_enabled = True
        self.axis_enabled = True
        self.wireframe_mode = False
        self.camera_fov = 60.0
        self.near_clip = 0.1
        self.far_clip = 10000.0
        self.auto_frame = True


class OpenGLViewport(QOpenGLWidget):
    """OpenGL viewport for USD rendering"""
    
    def __init__(self, parent=None):
        # Configure OpenGL format for compatibility profile
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)  # OpenGL 2.1 for compatibility
        fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
        fmt.setDepthBufferSize(24)
        fmt.setSamples(4)  # 4x MSAA
        QSurfaceFormat.setDefaultFormat(fmt)
        
        super().__init__(parent)
        self.stage_manager: Optional[USDStageManager] = None
        self.geometry_data = {}
        self.settings = ViewerSettings()
        
        # Camera controls
        self.camera_distance = 10.0
        self.camera_rotation_x = 30.0
        self.camera_rotation_y = 45.0
        self.camera_target = np.array([0.0, 0.0, 0.0])
        
        # View mode (Perspective, Top, Front, Left, Back, Right)
        self.view_mode = "Perspective"
        self.current_usd_camera = None
        
        # Store initial camera state (home position)
        self.home_camera_distance = 10.0
        self.home_camera_rotation_x = 30.0
        self.home_camera_rotation_y = 45.0
        self.home_camera_target = np.array([0.0, 0.0, 0.0])
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.is_rotating = False
        self.is_panning = False
        
        # Enable keyboard focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def set_stage_manager(self, manager: USDStageManager):
        """Set the USD stage manager"""
        self.stage_manager = manager
        
    def update_geometry(self, time_code: float):
        """Update geometry for current time"""
        if not self.stage_manager:
            return
            
        try:
            self.geometry_data = self.stage_manager.get_geometry_data(time_code)
            
            # Auto-frame on first load
            if self.settings.auto_frame and 'bounds' in self.geometry_data and self.geometry_data['bounds']:
                bounds = self.geometry_data['bounds']
                self.frame_bounds(bounds)
                self.settings.auto_frame = False
                
            # Schedule update
            QTimer.singleShot(0, self.update)
        except Exception as e:
            print(f"ERROR in update_geometry: {e}")
            import traceback
            traceback.print_exc()
    
    def frame_bounds(self, bounds: dict):
        """Frame camera to bounds"""
        if not bounds:
            return
        
        center = np.array(bounds['center'])
        size = np.array(bounds['size'])
        max_size = np.max(size)
        
        # Set camera to view entire bounds
        self.camera_target = center
        self.camera_distance = max_size * 1.5
        
        print(f"DEBUG: Framed camera. Target: {self.camera_target}, Distance: {self.camera_distance}, Size: {max_size}")
    
    def go_home(self):
        """Reset camera to home position"""
        self.camera_distance = self.home_camera_distance
        self.camera_rotation_x = self.home_camera_rotation_x
        self.camera_rotation_y = self.home_camera_rotation_y
        self.camera_target = self.home_camera_target.copy()
        self.update()
        
    def initializeGL(self):
        """Initialize OpenGL settings"""
        print("DEBUG: Initializing OpenGL viewport...")
        
        try:
            gl_version = glGetString(GL_VERSION)
            gl_renderer = glGetString(GL_RENDERER)
            print(f"DEBUG: OpenGL Version: {gl_version}")
            print(f"DEBUG: OpenGL Renderer: {gl_renderer}")
        except:
            print("WARNING: Could not get OpenGL info")
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])
        
        print("DEBUG: OpenGL viewport initialized successfully")
        
    def resizeGL(self, w, h):
        """Handle viewport resize"""
        glViewport(0, 0, w, h)
        
    def paintGL(self):
        """Render the scene"""
        try:
            # Clear buffers
            bg = self.settings.background_color
            glClearColor(*bg)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Set up projection
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            aspect = self.width() / max(self.height(), 1)
            
            if self.view_mode == "Perspective":
                gluPerspective(self.settings.camera_fov, aspect, 
                              self.settings.near_clip, self.settings.far_clip)
            else:
                ortho_size = self.camera_distance * 0.5
                glOrtho(-ortho_size * aspect, ortho_size * aspect,
                       -ortho_size, ortho_size,
                       self.settings.near_clip, self.settings.far_clip)
            
            # Set up camera
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            # Calculate camera position based on view mode
            camera_pos, up_vector = self._calculate_camera_transform()
            
            gluLookAt(
                camera_pos[0], camera_pos[1], camera_pos[2],
                self.camera_target[0], self.camera_target[1], self.camera_target[2],
                up_vector[0], up_vector[1], up_vector[2]
            )
            
            # Draw scene
            if self.settings.grid_enabled:
                self.draw_grid()
            
            if self.settings.axis_enabled:
                self.draw_axis()
            
            self.draw_geometry()
            
        except Exception as e:
            print(f"ERROR in paintGL: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_camera_transform(self):
        """Calculate camera position and up vector based on view mode"""
        if self.view_mode == "Perspective":
            cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
            cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            camera_pos = self.camera_target + np.array([cam_x, cam_y, cam_z])
            up_vector = np.array([0, 1, 0])
        elif self.view_mode == "Top":
            camera_pos = self.camera_target + np.array([0, self.camera_distance, 0])
            up_vector = np.array([0, 0, -1])
        elif self.view_mode == "Front":
            camera_pos = self.camera_target + np.array([0, 0, self.camera_distance])
            up_vector = np.array([0, 1, 0])
        elif self.view_mode == "Left":
            camera_pos = self.camera_target + np.array([-self.camera_distance, 0, 0])
            up_vector = np.array([0, 1, 0])
        elif self.view_mode == "Back":
            camera_pos = self.camera_target + np.array([0, 0, -self.camera_distance])
            up_vector = np.array([0, 1, 0])
        elif self.view_mode == "Right":
            camera_pos = self.camera_target + np.array([self.camera_distance, 0, 0])
            up_vector = np.array([0, 1, 0])
        else:
            cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
            cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            camera_pos = self.camera_target + np.array([cam_x, cam_y, cam_z])
            up_vector = np.array([0, 1, 0])
        
        return camera_pos, up_vector
    
    def draw_grid(self):
        """Draw grid"""
        glDisable(GL_LIGHTING)
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        
        grid_size = 50
        grid_spacing = 1.0
        
        for i in range(-grid_size, grid_size + 1):
            x = i * grid_spacing
            glVertex3f(x, 0, -grid_size * grid_spacing)
            glVertex3f(x, 0, grid_size * grid_spacing)
            
            z = i * grid_spacing
            glVertex3f(-grid_size * grid_spacing, 0, z)
            glVertex3f(grid_size * grid_spacing, 0, z)
        
        glEnd()
        glEnable(GL_LIGHTING)
    
    def draw_axis(self):
        """Draw coordinate axis"""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        
        # X axis (red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(5, 0, 0)
        
        # Y axis (green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 5, 0)
        
        # Z axis (blue)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 5)
        
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
    
    def draw_geometry(self):
        """Draw USD geometry"""
        if not self.geometry_data or 'meshes' not in self.geometry_data:
            return
        
        if not self.geometry_data['meshes']:
            return
        
        try:
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LEQUAL)
            glEnable(GL_NORMALIZE)
            
            # Material properties
            glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.9, 0.9, 0.9, 1.0])
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64.0)
            
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glColor3f(0.8, 0.8, 0.8)
            
            mesh_count = 0
            for mesh in self.geometry_data['meshes']:
                if mesh and 'points' in mesh and len(mesh['points']) > 0:
                    self.draw_mesh(mesh)
                    mesh_count += 1
            
            # Log occasionally
            import time
            current_time = int(time.time() * 1000)
            if not hasattr(self, '_last_mesh_count_print') or current_time - self._last_mesh_count_print > 2000:
                print(f"DEBUG: Drew {mesh_count} meshes")
                self._last_mesh_count_print = current_time
            
            glDisable(GL_COLOR_MATERIAL)
            
        except Exception as e:
            print(f"ERROR in draw_geometry: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_mesh(self, mesh: dict):
        """Draw a single mesh"""
        try:
            points = mesh.get('points', [])
            face_vertex_counts = mesh.get('face_vertex_counts', [])
            face_vertex_indices = mesh.get('face_vertex_indices', [])
            normals = mesh.get('normals', None)
            
            if not points or not face_vertex_counts or not face_vertex_indices:
                return
            
            # Apply transform
            transform = mesh.get('transform', None)
            if transform:
                glPushMatrix()
                # Convert to column-major for OpenGL
                transform_flat = []
                for row in transform:
                    transform_flat.extend(row)
                glMultMatrixd(transform_flat)
            
            # Draw faces
            idx = 0
            for face_count in face_vertex_counts:
                if face_count == 3:
                    glBegin(GL_TRIANGLES)
                elif face_count == 4:
                    glBegin(GL_QUADS)
                else:
                    glBegin(GL_POLYGON)
                
                for i in range(face_count):
                    vertex_idx = face_vertex_indices[idx + i]
                    if vertex_idx < len(points):
                        if normals and vertex_idx < len(normals):
                            glNormal3f(*normals[vertex_idx])
                        else:
                            glNormal3f(0, 1, 0)
                        glVertex3f(*points[vertex_idx])
                
                glEnd()
                idx += face_count
            
            if transform:
                glPopMatrix()
                
        except Exception as e:
            print(f"ERROR drawing mesh: {e}")
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        self.last_mouse_pos = event.pos()
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_rotating = True
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_rotating = False
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
        self.last_mouse_pos = None
    
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        if not self.last_mouse_pos:
            return
        
        dx = event.pos().x() - self.last_mouse_pos.x()
        dy = event.pos().y() - self.last_mouse_pos.y()
        
        if self.is_rotating:
            self.camera_rotation_y += dx * 0.5
            self.camera_rotation_x += dy * 0.5
            self.camera_rotation_x = np.clip(self.camera_rotation_x, -89, 89)
            QTimer.singleShot(0, self.update)
        
        elif self.is_panning:
            pan_speed = self.camera_distance * 0.001
            right = np.array([np.cos(np.radians(self.camera_rotation_y)), 0, 
                            np.sin(np.radians(self.camera_rotation_y))])
            up = np.array([0, 1, 0])
            self.camera_target -= right * dx * pan_speed
            self.camera_target += up * dy * pan_speed
            QTimer.singleShot(0, self.update)
        
        self.last_mouse_pos = event.pos()
    
    def wheelEvent(self, event):
        """Handle mouse wheel"""
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        self.camera_distance *= zoom_factor
        self.camera_distance = np.clip(self.camera_distance, 0.1, 10000)
        QTimer.singleShot(0, self.update)
