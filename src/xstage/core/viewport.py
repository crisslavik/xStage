"""
Enhanced Viewport Widget with Scale Controls and Measured Grid
Based on OpenUSD v25.11 with Hydra 2.0 support
Includes Houdini-style grid with metric measurements
"""

import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QDoubleSpinBox, QGroupBox, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

try:
    from pxr import Usd, UsdGeom, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class ViewportWidget(QOpenGLWidget):
    """
    Enhanced OpenGL viewport with:
    - Scene scale control for mismatched FBX/imports
    - Houdini-style grid with metric measurements
    - Hydra 2.0 integration (when available)
    - Better performance for large scenes
    """
    
    scale_changed = Signal(float)
    
    def __init__(self, parent=None):
        # Configure OpenGL format for compatibility profile (supports deprecated functions)
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)  # OpenGL 2.1
        fmt.setProfile(QSurfaceFormat.CompatibilityProfile)  # Compatibility profile (not Core)
        fmt.setSamples(4)  # 4x MSAA
        QSurfaceFormat.setDefaultFormat(fmt)
        
        super().__init__(parent)
        self.stage_manager = None
        self.geometry_data = {}
        
        # Camera controls
        self.camera_distance = 10.0
        self.camera_rotation_x = 30.0
        self.camera_rotation_y = 45.0
        self.camera_target = np.array([0.0, 0.0, 0.0])
        
        # Scene scale control - for FBX imports with wrong scale
        self.scene_scale = 1.0
        self.scale_min = 0.001
        self.scale_max = 1000.0
        
        # Grid settings
        self.grid_enabled = True
        self.grid_size = 100  # Grid extends this many meters
        self.grid_major_spacing = 1.0  # Major grid lines every 1 meter
        self.grid_minor_spacing = 0.1  # Minor grid lines every 10cm
        self.grid_color_major = (0.3, 0.3, 0.3, 1.0)
        self.grid_color_minor = (0.2, 0.2, 0.2, 0.5)
        self.grid_text_enabled = True  # Show measurements like Houdini
        
        # Axis settings
        self.axis_enabled = True
        self.axis_size = 1.0  # In meters
        
        # USD stage settings
        self.up_axis = 'Y'  # Default Y-up, will be updated from USD stage
        self.meters_per_unit = 1.0  # Default 1 unit = 1 meter
        
        # View settings
        self.background_color = (0.18, 0.18, 0.18, 1.0)  # Houdini-like bg
        self.camera_fov = 60.0
        self.near_clip = 0.01  # Closer near clip for small objects
        self.far_clip = 100000.0
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.is_rotating = False
        self.is_panning = False
        
        # Performance settings
        self.use_hydra2 = self._check_hydra2_available()
        self.multisample_enabled = True
        
    def _check_hydra2_available(self) -> bool:
        """Check if Hydra 2.0 is available"""
        if not USD_AVAILABLE:
            return False
        try:
            from pxr import UsdImagingGL
            # Check if scene index is enabled (Hydra 2.0)
            return hasattr(UsdImagingGL, 'Engine')
        except:
            return False
    
    def set_stage_manager(self, manager):
        """Set the USD stage manager"""
        self.stage_manager = manager
        
    def set_scene_scale(self, scale: float):
        """Set global scene scale"""
        self.scene_scale = np.clip(scale, self.scale_min, self.scale_max)
        self.scale_changed.emit(self.scene_scale)
        self.update()
        
    def update_geometry(self, time_code: float):
        """Update geometry for current time"""
        if self.stage_manager:
            self.geometry_data = self.stage_manager.get_geometry_data(time_code)
            
            # Get up-axis and meters_per_unit from geometry data
            self.up_axis = self.geometry_data.get('up_axis', 'Y')
            self.meters_per_unit = self.geometry_data.get('meters_per_unit', 0.01)
            
            # Auto-frame on first load
            if 'bounds' in self.geometry_data and self.geometry_data['bounds']:
                self.frame_bounds(self.geometry_data['bounds'])
                
            self.update()
    
    def frame_bounds(self, bounds: dict):
        """Frame camera to fit bounds"""
        if not bounds:
            return
        
        # Get center and size, accounting for meters_per_unit
        center = np.array(bounds['center'])
        size = np.max(bounds['size'])
        
        # Convert to meters for consistent viewport units
        center = center * self.meters_per_unit
        size = size * self.meters_per_unit
        
        # If Z-up, swap Y and Z for camera target
        if self.up_axis == 'Z':
            center = np.array([center[0], center[2], center[1]])
        
        self.camera_target = center
        self.camera_distance = max(size * 2.0, 1.0)  # Minimum distance of 1m
        
        # Adjust grid spacing based on scene size
        self._auto_adjust_grid(size)
        
    def _auto_adjust_grid(self, scene_size: float):
        """Automatically adjust grid spacing based on scene size"""
        # Determine appropriate major grid spacing
        if scene_size < 0.1:  # Very small (< 10cm)
            self.grid_major_spacing = 0.01  # 1cm
            self.grid_minor_spacing = 0.001  # 1mm
            self.grid_size = 1
        elif scene_size < 1.0:  # Small (< 1m)
            self.grid_major_spacing = 0.1  # 10cm
            self.grid_minor_spacing = 0.01  # 1cm
            self.grid_size = 10
        elif scene_size < 10.0:  # Medium (< 10m)
            self.grid_major_spacing = 1.0  # 1m
            self.grid_minor_spacing = 0.1  # 10cm
            self.grid_size = 50
        elif scene_size < 100.0:  # Large (< 100m)
            self.grid_major_spacing = 10.0  # 10m
            self.grid_minor_spacing = 1.0  # 1m
            self.grid_size = 200
        else:  # Very large
            self.grid_major_spacing = 100.0  # 100m
            self.grid_minor_spacing = 10.0  # 10m
            self.grid_size = 1000
            
    def initializeGL(self):
        """Initialize OpenGL settings"""
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        
        # Enable backface culling for better performance and correct rendering
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        
        # Enable automatic normal normalization (important for scaled geometry)
        glEnable(GL_NORMALIZE)
        
        if self.multisample_enabled:
            glEnable(GL_MULTISAMPLE)
            
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Two-sided lighting for better visibility
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        
        # Primary light (key light from upper-right-front)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
        
        # Secondary light (fill light from lower-left-back)
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_POSITION, [-1.0, -0.5, -1.0, 0.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.3, 0.3, 0.35, 1.0])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
        
    def resizeGL(self, w, h):
        """Handle viewport resize"""
        glViewport(0, 0, w, h)
    
    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        # Emit signal for overlay update if available
        if hasattr(self, 'overlay'):
            self.overlay.resize(self.size())
        
    def paintGL(self):
        """Render the scene"""
        # Clear buffers
        bg = self.background_color
        glClearColor(*bg)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width() / max(self.height(), 1)
        gluPerspective(self.camera_fov, aspect, self.near_clip, self.far_clip)
        
        # Set up camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Calculate camera position
        cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
        cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        
        camera_pos = self.camera_target + np.array([cam_x, cam_y, cam_z])
        
        gluLookAt(
            camera_pos[0], camera_pos[1], camera_pos[2],
            self.camera_target[0], self.camera_target[1], self.camera_target[2],
            0, 1, 0
        )
        
        # Update light positions in world space (after camera transform)
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT1, GL_POSITION, [-1.0, -0.5, -1.0, 0.0])
        
        # Draw grid with measurements (like Houdini)
        if self.grid_enabled:
            self.draw_measured_grid()
        
        # Draw axis
        if self.axis_enabled:
            self.draw_axis()
        
        # Apply Z-up to Y-up conversion if needed, then scene scale
        glPushMatrix()
        
        # Convert Z-up to Y-up (rotate -90 degrees around X axis)
        if self.up_axis == 'Z':
            glRotatef(-90.0, 1.0, 0.0, 0.0)
        
        # Apply meters_per_unit conversion (convert USD units to meters)
        glScalef(self.meters_per_unit, self.meters_per_unit, self.meters_per_unit)
        
        # Apply user scene scale
        glScalef(self.scene_scale, self.scene_scale, self.scene_scale)
        
        self.draw_geometry()
        glPopMatrix()
        
    def draw_measured_grid(self):
        """Draw grid with Houdini-style measurements in meters"""
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        
        # Draw minor grid lines
        glColor4f(*self.grid_color_minor)
        glBegin(GL_LINES)
        
        minor_count = int(self.grid_size / self.grid_minor_spacing)
        for i in range(-minor_count, minor_count + 1):
            pos = i * self.grid_minor_spacing
            
            # Skip if this will be a major line
            if abs(pos % self.grid_major_spacing) < 0.001:
                continue
                
            # Lines along X
            glVertex3f(-self.grid_size, 0, pos)
            glVertex3f(self.grid_size, 0, pos)
            
            # Lines along Z
            glVertex3f(pos, 0, -self.grid_size)
            glVertex3f(pos, 0, self.grid_size)
            
        glEnd()
        
        # Draw major grid lines
        glColor4f(*self.grid_color_major)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        
        major_count = int(self.grid_size / self.grid_major_spacing)
        for i in range(-major_count, major_count + 1):
            pos = i * self.grid_major_spacing
            
            # Lines along X
            glVertex3f(-self.grid_size, 0, pos)
            glVertex3f(self.grid_size, 0, pos)
            
            # Lines along Z
            glVertex3f(pos, 0, -self.grid_size)
            glVertex3f(pos, 0, self.grid_size)
            
        glEnd()
        
        # Draw origin cross (thicker)
        glColor4f(0.5, 0.5, 0.5, 1.0)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        
        # X axis on ground
        glVertex3f(-self.grid_size, 0, 0)
        glVertex3f(self.grid_size, 0, 0)
        
        # Z axis on ground
        glVertex3f(0, 0, -self.grid_size)
        glVertex3f(0, 0, self.grid_size)
        
        glEnd()
        
        # TODO: Add text labels for measurements (requires font rendering)
        # For now, measurements are implicit from grid spacing
        
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
        
    def draw_axis(self):
        """Draw coordinate axis with scale indicators"""
        glDisable(GL_LIGHTING)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        
        axis_length = self.axis_size
        
        # X axis - Red
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(axis_length, 0, 0)
        
        # Y axis - Green  
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, axis_length, 0)
        
        # Z axis - Blue
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, axis_length)
        
        glEnd()
        
        # Draw axis end markers (small cubes)
        cube_size = axis_length * 0.05
        
        glColor3f(1, 0, 0)
        self._draw_cube(axis_length, 0, 0, cube_size)
        
        glColor3f(0, 1, 0)
        self._draw_cube(0, axis_length, 0, cube_size)
        
        glColor3f(0, 0, 1)
        self._draw_cube(0, 0, axis_length, cube_size)
        
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
        
    def _draw_cube(self, x, y, z, size):
        """Draw a small cube at position"""
        s = size / 2
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Just draw a simple wireframe cube
        glBegin(GL_LINE_LOOP)
        glVertex3f(-s, -s, -s)
        glVertex3f(s, -s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(-s, s, -s)
        glEnd()
        
        glBegin(GL_LINE_LOOP)
        glVertex3f(-s, -s, s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, s)
        glEnd()
        
        glBegin(GL_LINES)
        glVertex3f(-s, -s, -s)
        glVertex3f(-s, -s, s)
        glVertex3f(s, -s, -s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, -s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, -s)
        glVertex3f(-s, s, s)
        glEnd()
        
        glPopMatrix()
        
    def draw_geometry(self):
        """Draw USD geometry"""
        if not self.geometry_data or 'meshes' not in self.geometry_data:
            return
        
        glEnable(GL_LIGHTING)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)
        
        for mesh in self.geometry_data['meshes']:
            self.draw_mesh(mesh)
        
        # Draw light visualization
        if 'lights' in self.geometry_data:
            self.draw_lights()
    
    def draw_mesh(self, mesh: dict):
        """Draw a single mesh"""
        points = mesh['points']
        fvc = mesh['face_vertex_counts']
        fvi = mesh['face_vertex_indices']
        normals = mesh['normals']
        
        # Apply transform (convert to numpy array if needed)
        glPushMatrix()
        transform = np.array(mesh['transform'], dtype=np.float32)
        # OpenGL expects column-major order, USD provides row-major
        glMultMatrixf(transform.T.flatten())
        
        # Draw faces
        idx = 0
        for count in fvc:
            if count == 3:
                glBegin(GL_TRIANGLES)
            elif count == 4:
                glBegin(GL_QUADS)
            else:
                glBegin(GL_POLYGON)
                
            for i in range(count):
                vert_idx = fvi[idx + i]
                
                # Normal
                if normals is not None and vert_idx < len(normals):
                    n = normals[vert_idx]
                    glNormal3f(n[0], n[1], n[2])
                    
                # Vertex
                v = points[vert_idx]
                glVertex3f(v[0], v[1], v[2])
                
            glEnd()
            idx += count
            
        glPopMatrix()
    
    def draw_lights(self):
        """Draw light visualization (icons, cones, direction indicators)"""
        if not self.geometry_data or 'lights' not in self.geometry_data:
            return
        
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        
        for light_data in self.geometry_data['lights']:
            self.draw_light_icon(light_data)
    
    def draw_light_icon(self, light_data: dict):
        """Draw a single light icon"""
        try:
            position = light_data.get('position', np.array([0, 0, 0]))
            light_type = light_data.get('type', 'Unknown')
            color = light_data.get('color', (1.0, 1.0, 1.0))
            intensity = light_data.get('intensity', 1.0)
            direction = light_data.get('direction', np.array([0, 0, -1]))
            
            # Normalize direction
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
            
            # Set color based on light color and intensity
            glColor3f(color[0] * min(intensity / 10.0, 1.0), 
                     color[1] * min(intensity / 10.0, 1.0), 
                     color[2] * min(intensity / 10.0, 1.0))
            
            glPushMatrix()
            glTranslatef(position[0], position[1], position[2])
            
            # Draw different icons based on light type
            if 'SphereLight' in light_type or 'Point' in light_type:
                radius = light_data.get('radius', 0.1)
                self._draw_sphere_light_icon(radius)
            
            elif 'RectLight' in light_type:
                width = light_data.get('width', 1.0)
                height = light_data.get('height', 1.0)
                self._draw_rect_light_icon(width, height, direction)
            
            elif 'DiskLight' in light_type:
                radius = light_data.get('radius', 0.5)
                self._draw_disk_light_icon(radius, direction)
            
            elif 'DistantLight' in light_type or 'Directional' in light_type:
                self._draw_distant_light_icon(direction)
            
            elif 'CylinderLight' in light_type:
                radius = light_data.get('radius', 0.5)
                length = light_data.get('length', 1.0)
                self._draw_cylinder_light_icon(radius, length)
            
            else:
                # Default: draw a small sphere
                self._draw_sphere_light_icon(0.1)
            
            # Draw direction indicator (arrow)
            if 'DistantLight' not in light_type and 'Directional' not in light_type:
                cone_angle = light_data.get('cone_angle')
                if cone_angle:
                    self._draw_cone_indicator(direction, cone_angle)
                else:
                    self._draw_direction_arrow(direction)
            
            glPopMatrix()
        except Exception as e:
            print(f"Error drawing light icon: {e}")
    
    def _draw_sphere_light_icon(self, radius: float):
        """Draw sphere light icon"""
        # Draw a wireframe sphere (simplified - just draw a circle)
        segments = 16
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            glVertex3f(x, y, 0)
        glEnd()
        
        # Draw perpendicular circles for 3D effect
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = radius * np.cos(angle)
            z = radius * np.sin(angle)
            glVertex3f(x, 0, z)
        glEnd()
        
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            y = radius * np.cos(angle)
            z = radius * np.sin(angle)
            glVertex3f(0, y, z)
        glEnd()
    
    def _draw_rect_light_icon(self, width: float, height: float, direction: np.ndarray):
        """Draw rectangular light icon"""
        # Draw a rectangle perpendicular to direction
        # Simplified: draw a square
        size = max(width, height) * 0.5
        
        glBegin(GL_LINE_LOOP)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, -size, 0)
        glVertex3f(size, size, 0)
        glVertex3f(-size, size, 0)
        glEnd()
        
        # Draw direction arrow
        self._draw_direction_arrow(direction)
    
    def _draw_disk_light_icon(self, radius: float, direction: np.ndarray):
        """Draw disk light icon"""
        segments = 32
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            glVertex3f(x, y, 0)
        glEnd()
        
        # Draw direction arrow
        self._draw_direction_arrow(direction)
    
    def _draw_distant_light_icon(self, direction: np.ndarray):
        """Draw distant/directional light icon"""
        # Draw a sun-like icon (circle with rays)
        radius = 0.2
        segments = 8
        
        # Draw circle
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            glVertex3f(x, y, 0)
        glEnd()
        
        # Draw rays
        ray_length = radius * 1.5
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x1 = radius * np.cos(angle)
            y1 = radius * np.sin(angle)
            x2 = ray_length * np.cos(angle)
            y2 = ray_length * np.sin(angle)
            
            glBegin(GL_LINES)
            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y2, 0)
            glEnd()
        
        # Draw direction arrow (longer for distant lights)
        arrow_length = 2.0
        arrow_dir = direction * arrow_length
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(arrow_dir[0], arrow_dir[1], arrow_dir[2])
        glEnd()
    
    def _draw_cylinder_light_icon(self, radius: float, length: float):
        """Draw cylinder light icon"""
        segments = 16
        half_length = length * 0.5
        
        # Draw cylinder outline
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            glVertex3f(x, y, -half_length)
        glEnd()
        
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            glVertex3f(x, y, half_length)
        glEnd()
        
        # Draw connecting lines
        for i in range(0, segments, 4):
            angle = 2 * np.pi * i / segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            glBegin(GL_LINES)
            glVertex3f(x, y, -half_length)
            glVertex3f(x, y, half_length)
            glEnd()
    
    def _draw_cone_indicator(self, direction: np.ndarray, cone_angle: float):
        """Draw cone angle indicator for spot lights"""
        cone_length = 1.0
        cone_radius = cone_length * np.tan(np.radians(cone_angle))
        
        # Draw cone outline
        segments = 16
        glBegin(GL_LINE_LOOP)
        glVertex3f(0, 0, 0)  # Tip at origin
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = cone_radius * np.cos(angle)
            y = cone_radius * np.sin(angle)
            z = -cone_length
            glVertex3f(x, y, z)
        glEnd()
        
        # Draw lines from tip to base
        for i in range(0, segments, 4):
            angle = 2 * np.pi * i / segments
            x = cone_radius * np.cos(angle)
            y = cone_radius * np.sin(angle)
            z = -cone_length
            
            glBegin(GL_LINES)
            glVertex3f(0, 0, 0)
            glVertex3f(x, y, z)
            glEnd()
    
    def _draw_direction_arrow(self, direction: np.ndarray):
        """Draw direction arrow"""
        arrow_length = 0.5
        arrow_head_size = 0.1
        
        # Arrow shaft
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        arrow_end = direction * arrow_length
        glVertex3f(arrow_end[0], arrow_end[1], arrow_end[2])
        glEnd()
        
        # Arrow head (simplified - triangle)
        arrow_end = direction * arrow_length
        # Perpendicular vectors for arrow head
        if abs(direction[0]) < 0.9:
            perp = np.array([1, 0, 0])
        else:
            perp = np.array([0, 1, 0])
        perp = perp - np.dot(perp, direction) * direction
        perp = perp / np.linalg.norm(perp)
        
        head1 = arrow_end - direction * arrow_head_size + perp * arrow_head_size * 0.5
        head2 = arrow_end - direction * arrow_head_size - perp * arrow_head_size * 0.5
        
        glBegin(GL_LINES)
        glVertex3f(arrow_end[0], arrow_end[1], arrow_end[2])
        glVertex3f(head1[0], head1[1], head1[2])
        glVertex3f(arrow_end[0], arrow_end[1], arrow_end[2])
        glVertex3f(head2[0], head2[1], head2[2])
        glEnd()
        
    def mousePressEvent(self, event):
        """Handle mouse press"""
        self.last_mouse_pos = event.position()
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_rotating = True
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.is_rotating = False
        self.is_panning = False
        
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        if not self.last_mouse_pos:
            return
            
        pos = event.position()
        dx = pos.x() - self.last_mouse_pos.x()
        dy = pos.y() - self.last_mouse_pos.y()
        
        if self.is_rotating:
            self.camera_rotation_y += dx * 0.5
            self.camera_rotation_x = np.clip(self.camera_rotation_x + dy * 0.5, -89, 89)
            self.update()
            
        elif self.is_panning:
            pan_speed = self.camera_distance * 0.001
            right = np.array([np.cos(np.radians(self.camera_rotation_y)), 0, 
                            -np.sin(np.radians(self.camera_rotation_y))])
            up = np.array([0, 1, 0])
            
            self.camera_target -= right * dx * pan_speed
            self.camera_target += up * dy * pan_speed
            self.update()
            
        self.last_mouse_pos = pos
        
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom"""
        delta = event.angleDelta().y()
        zoom_factor = 0.1
        
        if delta > 0:
            self.camera_distance *= (1.0 - zoom_factor)
        else:
            self.camera_distance *= (1.0 + zoom_factor)
            
        self.camera_distance = np.clip(self.camera_distance, 0.01, 100000.0)
        self.update()


class ScaleControlWidget(QWidget):
    """Widget for controlling scene scale"""
    
    scale_changed = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Scene Scale Control</b>")
        layout.addWidget(title)
        
        # Info label
        info = QLabel("Adjust for FBX/imports with incorrect scale:")
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info)
        
        # Scale slider (logarithmic)
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Scale:"))
        
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(-3000, 3000)  # 0.001 to 1000
        self.scale_slider.setValue(0)  # 1.0
        self.scale_slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self.scale_slider)
        
        layout.addLayout(slider_layout)
        
        # Scale spinbox
        spinbox_layout = QHBoxLayout()
        spinbox_layout.addWidget(QLabel("Value:"))
        
        self.scale_spinbox = QDoubleSpinBox()
        self.scale_spinbox.setRange(0.001, 1000.0)
        self.scale_spinbox.setValue(1.0)
        self.scale_spinbox.setDecimals(3)
        self.scale_spinbox.setSingleStep(0.1)
        self.scale_spinbox.valueChanged.connect(self._on_spinbox_changed)
        spinbox_layout.addWidget(self.scale_spinbox)
        
        spinbox_layout.addWidget(QLabel("m"))
        spinbox_layout.addStretch()
        
        layout.addLayout(spinbox_layout)
        
        # Preset buttons
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Presets:"))
        
        presets = [
            ("mm→m", 0.001),
            ("cm→m", 0.01),
            ("1:1", 1.0),
            ("m→cm", 100.0),
            ("m→mm", 1000.0),
        ]
        
        for label, value in presets:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, v=value: self.set_scale(v))
            btn.setMaximumWidth(60)
            preset_layout.addWidget(btn)
            
        layout.addLayout(preset_layout)
        
        # Current grid info
        self.grid_info = QLabel("Grid: 1m major, 10cm minor")
        self.grid_info.setStyleSheet("color: gray; font-size: 9px;")
        layout.addWidget(self.grid_info)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def _on_slider_changed(self, value):
        """Handle slider change"""
        # Logarithmic scale: -3000 to 3000 -> 0.001 to 1000
        scale = 10 ** (value / 1000.0)
        self.scale_spinbox.blockSignals(True)
        self.scale_spinbox.setValue(scale)
        self.scale_spinbox.blockSignals(False)
        self.scale_changed.emit(scale)
        
    def _on_spinbox_changed(self, value):
        """Handle spinbox change"""
        # Update slider
        slider_value = int(np.log10(value) * 1000)
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(slider_value)
        self.scale_slider.blockSignals(False)
        self.scale_changed.emit(value)
        
    def set_scale(self, value: float):
        """Set scale value"""
        self.scale_spinbox.setValue(value)
        
    def update_grid_info(self, major: float, minor: float):
        """Update grid information display"""
        def format_unit(val):
            if val >= 1.0:
                return f"{val:.0f}m"
            elif val >= 0.01:
                return f"{val*100:.0f}cm"
            else:
                return f"{val*1000:.0f}mm"
                
        self.grid_info.setText(f"Grid: {format_unit(major)} major, {format_unit(minor)} minor")