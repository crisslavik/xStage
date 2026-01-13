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

# Import OpenGL for clearing and basic operations
try:
    from OpenGL.GL import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    print("Warning: PyOpenGL not available")

try:
    from pxr import Usd, UsdGeom, Gf, UsdImagingGL, Glf, CameraUtil
    USD_AVAILABLE = True
    # Check if Orthographic is available (may not be in all USD versions)
    ORTHOGRAPHIC_AVAILABLE = hasattr(CameraUtil, 'Orthographic')
except ImportError:
    USD_AVAILABLE = False
    UsdImagingGL = None
    Glf = None
    CameraUtil = None
    ORTHOGRAPHIC_AVAILABLE = False


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
        
        # View mode (Perspective, Top, Front, Left, Back, Right)
        self.view_mode = "Perspective"
        self.current_usd_camera = None  # USD camera prim if using USD camera
        
        # Store initial camera state (home position)
        self.home_camera_distance = 10.0
        self.home_camera_rotation_x = 30.0
        self.home_camera_rotation_y = 45.0
        self.home_camera_target = Gf.Vec3d(0.0, 0.0, 0.0)
        
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
        format.setVersion(4, 5)  # OpenGL 4.5 required for Storm renderer
        format.setProfile(QSurfaceFormat.CoreProfile)
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setSamples(4)  # Multisampling
        format.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        QSurfaceFormat.setDefaultFormat(format)  # Set as default
        self.setFormat(format)
    
    def initializeGL(self):
        """Initialize OpenGL and Hydra 2.0"""
        if not USD_AVAILABLE:
            return
        
        try:
            # CRITICAL: Make OpenGL context current before any GL calls
            self.makeCurrent()
            
            # Initialize GLF (GL Framework) - required for Storm
            # Note: GlewInit is not available in pip-installed USD
            if Glf and hasattr(Glf, 'GlewInit'):
                Glf.GlewInit()
            elif Glf:
                print("⚠️  Glf.GlewInit not available (pip-installed USD)")
            
            # CRITICAL: Enable Scene Index BEFORE creating engine (Hydra 2.0 requirement)
            try:
                if hasattr(UsdImagingGL.Engine, 'SetEnableSceneIndex'):
                    UsdImagingGL.Engine.SetEnableSceneIndex(True)
                    print("✅ Hydra 2.0 Scene Index enabled (static)")
            except Exception as e:
                print(f"⚠️  Scene Index enable failed: {e}")
            
            # Create Hydra engine AFTER enabling scene index
            self.engine = UsdImagingGL.Engine()
            
            # CRITICAL: Set Storm renderer explicitly (Hydra 2.0 GPU renderer)
            try:
                available_renderers = self.engine.GetRendererPlugins()
                print(f"Available renderers: {available_renderers}")
                
                if available_renderers:
                    if 'HdStormRendererPlugin' in available_renderers:
                        self.engine.SetRendererPlugin('HdStormRendererPlugin')
                        print("✅ Storm renderer (Hydra 2.0 GPU) enabled")
                    else:
                        # Use first available renderer
                        self.engine.SetRendererPlugin(available_renderers[0])
                        print(f"✅ Using renderer: {available_renderers[0]}")
                else:
                    print("❌ No renderer plugins found - check USD installation")
                    raise RuntimeError("No Hydra renderer plugins available")
            except Exception as e:
                print(f"❌ Renderer plugin selection failed: {e}")
                raise
            
            # Get renderer (for verification)
            try:
                self.renderer = self.engine.GetRenderer()
                current_renderer = self.engine.GetCurrentRendererId()
                print(f"Current renderer: {current_renderer}")
            except Exception as e:
                print(f"⚠️  Could not get renderer info: {e}")
            
            # Set render params
            self.render_params = UsdImagingGL.RenderParams()
            self.render_params.frame = self.current_time
            self.render_params.complexity = 1.0
            self.render_params.drawMode = UsdImagingGL.DrawMode.DRAW_SHADED_SMOOTH
            self.render_params.enableLighting = True
            self.render_params.enableIdRender = False
            self.render_params.enableSampleAlphaToCoverage = True  # Better transparency
            self.render_params.highlight = False
            self.render_params.cullStyle = UsdImagingGL.CullStyle.CULL_STYLE_BACK_UNLESS_DOUBLE_SIDED
            self.render_params.showGuides = False
            self.render_params.showProxy = True
            self.render_params.showRender = False
            
            # Set background color
            self.render_params.clearColor = self.background_color
            
            print("✅ Hydra engine initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing Hydra: {e}")
            import traceback
            traceback.print_exc()
            self.engine = None
    
    def resizeGL(self, w, h):
        """Handle viewport resize"""
        if not USD_AVAILABLE or not self.engine:
            return
        
        # Set viewport
        self.engine.SetRenderViewport(Gf.Rect2i(Gf.Vec2i(0, 0), w, h))
    
    def paintGL(self):
        """Render using Hydra 2.0"""
        if not USD_AVAILABLE or not self.engine or not self.stage:
            return
        
        try:
            # Make context current
            self.makeCurrent()
            
            # Clear
            if OPENGL_AVAILABLE:
                glClearColor(
                    self.background_color[0],
                    self.background_color[1],
                    self.background_color[2],
                    self.background_color[3]
                )
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Set viewport size
            width = self.width()
            height = self.height()
            self.engine.SetRenderViewport(Gf.Rect2i(Gf.Vec2i(0, 0), width, height))
            
            # Compute camera matrices
            view_matrix, projection_matrix = self._compute_camera_matrices()
            
            # CRITICAL: Set camera state (Hydra 2.0 requirement)
            try:
                self.engine.SetCameraState(view_matrix, projection_matrix)
            except Exception as e:
                print(f"⚠️  SetCameraState failed (may use legacy API): {e}")
                # Fallback to legacy matrix multiplication
                camera_matrix = projection_matrix * view_matrix
            
            # Set render params
            self.render_params.frame = Usd.TimeCode(self.current_time)
            
            # Render root prim
            root_prim = self.stage.GetPseudoRoot()
            
            # Try new API first (Hydra 2.0)
            try:
                self.engine.Render(root_prim, self.render_params)
            except TypeError:
                # Fallback to legacy API with matrix
                camera_matrix = projection_matrix * view_matrix
                self.engine.Render(root_prim, self.render_params, camera_matrix)
            
        except Exception as e:
            print(f"❌ Error rendering with Hydra: {e}")
            import traceback
            traceback.print_exc()
    
    def _compute_camera_matrices(self):
        """Compute camera view and projection matrices (separate for Hydra 2.0)"""
        aspect = self.width() / max(self.height(), 1)
        
        # Calculate camera position and orientation based on view mode
        view_mode = getattr(self, 'view_mode', 'Perspective')
        
        if view_mode == "Perspective":
            # Free camera (perspective)
            cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
            cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            camera_pos = Gf.Vec3d(
                self.camera_target[0] + cam_x,
                self.camera_target[1] + cam_y,
                self.camera_target[2] + cam_z
            )
            up_vector = Gf.Vec3d(0, 1, 0)
        elif view_mode == "Top":
            # Top view: camera above, looking down
            camera_pos = Gf.Vec3d(
                self.camera_target[0],
                self.camera_target[1] + self.camera_distance,
                self.camera_target[2]
            )
            up_vector = Gf.Vec3d(0, 0, -1)  # Negative Z is "up" in top view
        elif view_mode == "Front":
            # Front view: camera in front, looking back
            camera_pos = Gf.Vec3d(
                self.camera_target[0],
                self.camera_target[1],
                self.camera_target[2] + self.camera_distance
            )
            up_vector = Gf.Vec3d(0, 1, 0)
        elif view_mode == "Left":
            # Left view: camera on left, looking right
            camera_pos = Gf.Vec3d(
                self.camera_target[0] - self.camera_distance,
                self.camera_target[1],
                self.camera_target[2]
            )
            up_vector = Gf.Vec3d(0, 1, 0)
        elif view_mode == "Back":
            # Back view: camera behind, looking forward
            camera_pos = Gf.Vec3d(
                self.camera_target[0],
                self.camera_target[1],
                self.camera_target[2] - self.camera_distance
            )
            up_vector = Gf.Vec3d(0, 1, 0)
        elif view_mode == "Right":
            # Right view: camera on right, looking left
            camera_pos = Gf.Vec3d(
                self.camera_target[0] + self.camera_distance,
                self.camera_target[1],
                self.camera_target[2]
            )
            up_vector = Gf.Vec3d(0, 1, 0)
        else:
            # Default to perspective
            cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
            cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            camera_pos = Gf.Vec3d(
                self.camera_target[0] + cam_x,
                self.camera_target[1] + cam_y,
                self.camera_target[2] + cam_z
            )
            up_vector = Gf.Vec3d(0, 1, 0)
        
        # Create view matrix
        view_matrix = Gf.Matrix4d()
        view_matrix.SetLookAt(
            camera_pos,
            Gf.Vec3d(self.camera_target[0], self.camera_target[1], self.camera_target[2]),
            up_vector
        )
        
        # Create projection matrix
        if view_mode == "Perspective":
            # Perspective projection
            projection_matrix = CameraUtil.Frustum(
                -self.near_clip * np.tan(np.radians(self.camera_fov / 2.0)) * aspect,
                self.near_clip * np.tan(np.radians(self.camera_fov / 2.0)) * aspect,
                -self.near_clip * np.tan(np.radians(self.camera_fov / 2.0)),
                self.near_clip * np.tan(np.radians(self.camera_fov / 2.0)),
                self.near_clip,
                self.far_clip
            )
        else:
            # Orthographic projection for ortho views
            ortho_size = self.camera_distance * 0.5
            if ORTHOGRAPHIC_AVAILABLE and hasattr(CameraUtil, 'Orthographic'):
                projection_matrix = CameraUtil.Orthographic(
                    -ortho_size * aspect,
                    ortho_size * aspect,
                    -ortho_size,
                    ortho_size,
                    self.near_clip,
                    self.far_clip
                )
            else:
                # Fallback: create orthographic matrix manually
                # Orthographic: left, right, bottom, top, near, far
                left = -ortho_size * aspect
                right = ortho_size * aspect
                bottom = -ortho_size
                top = ortho_size
                near = self.near_clip
                far = self.far_clip
                
                # Create orthographic projection matrix
                projection_matrix = Gf.Matrix4d()
                projection_matrix[0][0] = 2.0 / (right - left)
                projection_matrix[1][1] = 2.0 / (top - bottom)
                projection_matrix[2][2] = -2.0 / (far - near)
                projection_matrix[3][0] = -(right + left) / (right - left)
                projection_matrix[3][1] = -(top + bottom) / (top - bottom)
                projection_matrix[3][2] = -(far + near) / (far - near)
                projection_matrix[3][3] = 1.0
        
        return view_matrix, projection_matrix
    
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
        self.update()
    
    def frame_selected(self):
        """Frame selected prim or all geometry (F key)"""
        if not self.stage_manager:
            return
        
        # Get geometry data from stage manager
        geometry_data = self.stage_manager.get_geometry_data(self.current_time)
        
        # Frame all geometry bounds
        if geometry_data and 'bounds' in geometry_data and geometry_data['bounds']:
            self.frame_bounds(geometry_data['bounds'])
        else:
            # Fallback: frame to origin
            self.camera_target = Gf.Vec3d(0.0, 0.0, 0.0)
            self.camera_distance = 10.0
            self.update()
    
    def go_home(self):
        """Reset camera to initial/home position (H key)"""
        self.camera_distance = self.home_camera_distance
        self.camera_rotation_x = self.home_camera_rotation_x
        self.camera_rotation_y = self.home_camera_rotation_y
        self.camera_target = self.home_camera_target
        self.update()
    
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
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for viewport navigation"""
        from PySide6.QtCore import Qt
        
        key = event.key()
        
        # F key: Frame selected/all geometry
        if key == Qt.Key.Key_F:
            self.frame_selected()
            event.accept()
            return
        
        # H key: Go home (reset camera to initial position)
        elif key == Qt.Key.Key_H:
            self.go_home()
            event.accept()
            return
        
        # Let parent handle other keys
        super().keyPressEvent(event)
    
    def is_hydra_available(self) -> bool:
        """Check if Hydra is available and working"""
        return USD_AVAILABLE and self.engine is not None

