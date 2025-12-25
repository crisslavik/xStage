"""
Hydra 2.0 Viewport Implementation
Uses UsdImagingGL for high-performance USD rendering
Based on OpenUSD 25.11 Hydra 2.0 specifications
"""

import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QOpenGLContext, QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget

try:
    from pxr import Usd, UsdGeom, Gf, UsdImagingGL, Glf, CameraUtil
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    UsdImagingGL = None
    Glf = None
    CameraUtil = None


class HydraViewportWidget(QOpenGLWidget):
    """
    Hydra 2.0 viewport using UsdImagingGL for rendering
    Provides better performance and proper material rendering
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage_manager = None
        self.stage = None
        self.current_time = 0.0
        
        # Hydra components
        self.engine = None
        self.renderer = None
        self.render_params = None
        
        # Camera controls
        self.camera_distance = 10.0
        self.camera_rotation_x = 30.0
        self.camera_rotation_y = 45.0
        self.camera_target = Gf.Vec3d(0.0, 0.0, 0.0)
        
        # View settings
        self.background_color = Gf.Vec4f(0.18, 0.18, 0.18, 1.0)
        self.camera_fov = 60.0
        self.near_clip = 0.01
        self.far_clip = 100000.0
        
        # Scene scale
        self.scene_scale = 1.0
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.is_rotating = False
        self.is_panning = False
        
        # Grid settings
        self.grid_enabled = True
        
        # Set up OpenGL context
        self._setup_opengl_context()
    
    def _setup_opengl_context(self):
        """Configure OpenGL context for Hydra"""
        format = QSurfaceFormat()
        format.setVersion(4, 1)  # OpenGL 4.1 minimum for Hydra
        format.setProfile(QSurfaceFormat.CoreProfile)
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setSamples(4)  # Multisampling
        format.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        self.setFormat(format)
    
    def initializeGL(self):
        """Initialize OpenGL and Hydra"""
        if not USD_AVAILABLE:
            return
        
        try:
            # Initialize GLF (GL Framework)
            if Glf:
                Glf.GlewInit()
            
            # Create Hydra engine
            self.engine = UsdImagingGL.Engine()
            
            # Get renderer
            self.renderer = self.engine.GetRenderer()
            
            # Set render params
            self.render_params = UsdImagingGL.RenderParams()
            self.render_params.frame = self.current_time
            self.render_params.complexity = 1.0
            self.render_params.drawMode = UsdImagingGL.DrawMode.DRAW_SHADED_SMOOTH
            self.render_params.enableLighting = True
            self.render_params.enableIdRender = False
            self.render_params.enableSampleAlphaToCoverage = False
            self.render_params.highlight = False
            self.render_params.cullStyle = UsdImagingGL.CullStyle.CULL_STYLE_BACK
            
            # Set background color
            self.render_params.clearColor = self.background_color
            
        except Exception as e:
            print(f"Error initializing Hydra: {e}")
            self.engine = None
    
    def resizeGL(self, w, h):
        """Handle viewport resize"""
        if not USD_AVAILABLE or not self.engine:
            return
        
        # Set viewport
        self.engine.SetRenderViewport(Gf.Rect2i(Gf.Vec2i(0, 0), w, h))
    
    def paintGL(self):
        """Render using Hydra"""
        if not USD_AVAILABLE or not self.engine or not self.stage:
            return
        
        try:
            # Clear
            glClearColor(
                self.background_color[0],
                self.background_color[1],
                self.background_color[2],
                self.background_color[3]
            )
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Set up camera
            camera_matrix = self._compute_camera_matrix()
            
            # Set render params
            self.render_params.frame = self.current_time
            
            # Render
            root_prim = self.stage.GetPseudoRoot()
            self.engine.Render(root_prim, self.render_params, camera_matrix)
            
        except Exception as e:
            print(f"Error rendering with Hydra: {e}")
    
    def _compute_camera_matrix(self):
        """Compute camera view and projection matrices"""
        # Calculate camera position
        cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
        cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        
        camera_pos = Gf.Vec3d(
            self.camera_target[0] + cam_x,
            self.camera_target[1] + cam_y,
            self.camera_target[2] + cam_z
        )
        
        # Create view matrix
        view_matrix = Gf.Matrix4d()
        view_matrix.SetLookAt(
            Gf.Vec3d(camera_pos[0], camera_pos[1], camera_pos[2]),
            Gf.Vec3d(self.camera_target[0], self.camera_target[1], self.camera_target[2]),
            Gf.Vec3d(0, 1, 0)
        )
        
        # Create projection matrix
        aspect = self.width() / max(self.height(), 1)
        projection_matrix = CameraUtil.Frustum(
            -self.near_clip * np.tan(np.radians(self.camera_fov / 2.0)) * aspect,
            self.near_clip * np.tan(np.radians(self.camera_fov / 2.0)) * aspect,
            -self.near_clip * np.tan(np.radians(self.camera_fov / 2.0)),
            self.near_clip * np.tan(np.radians(self.camera_fov / 2.0)),
            self.near_clip,
            self.far_clip
        )
        
        return projection_matrix * view_matrix
    
    def set_stage_manager(self, manager):
        """Set the USD stage manager"""
        self.stage_manager = manager
        if manager and manager.stage:
            self.stage = manager.stage
    
    def set_stage(self, stage):
        """Set the USD stage directly"""
        self.stage = stage
    
    def update_geometry(self, time_code: float):
        """Update geometry for current time"""
        self.current_time = time_code
        if self.stage_manager:
            self.stage = self.stage_manager.stage
        self.update()
    
    def frame_bounds(self, bounds: dict):
        """Frame camera to fit bounds"""
        if not bounds:
            return
        
        center = bounds.get('center', np.array([0, 0, 0]))
        size = bounds.get('size', np.array([1, 1, 1]))
        
        # Account for scene scale
        center_scaled = center * self.scene_scale
        size_scaled = np.max(size) * self.scene_scale
        
        self.camera_target = Gf.Vec3d(center_scaled[0], center_scaled[1], center_scaled[2])
        self.camera_distance = size_scaled * 2.0
    
    def set_scene_scale(self, scale: float):
        """Set global scene scale"""
        self.scene_scale = scale
        self.update()
    
    def set_background_color(self, color: tuple):
        """Set background color"""
        self.background_color = Gf.Vec4f(color[0], color[1], color[2], color[3] if len(color) > 3 else 1.0)
        if self.render_params:
            self.render_params.clearColor = self.background_color
        self.update()
    
    def set_draw_mode(self, mode: str):
        """Set draw mode (wireframe, shaded, etc.)"""
        if not self.render_params:
            return
        
        mode_map = {
            'wireframe': UsdImagingGL.DrawMode.DRAW_WIREFRAME,
            'shaded': UsdImagingGL.DrawMode.DRAW_SHADED_SMOOTH,
            'points': UsdImagingGL.DrawMode.DRAW_POINTS,
            'bounds': UsdImagingGL.DrawMode.DRAW_BOUNDS,
        }
        
        if mode in mode_map:
            self.render_params.drawMode = mode_map[mode]
            self.update()
    
    def set_complexity(self, complexity: float):
        """Set render complexity (tessellation level)"""
        if self.render_params:
            self.render_params.complexity = complexity
            self.update()
    
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
            # Pan camera target
            pan_speed = self.camera_distance * 0.001
            right = Gf.Vec3d(
                np.cos(np.radians(self.camera_rotation_y)),
                0,
                -np.sin(np.radians(self.camera_rotation_y))
            )
            up = Gf.Vec3d(0, 1, 0)
            
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
    
    def is_hydra_available(self) -> bool:
        """Check if Hydra is available and working"""
        return USD_AVAILABLE and self.engine is not None

