"""
Hydra Viewport Implementation
Uses UsdImagingGL (Storm) for high-performance USD rendering, configured to
mirror usdview's setup (OpenUSD 25.11).
"""

import logging

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget

log = logging.getLogger("xstage.rendering.hydra_viewport")

# Import OpenGL for clearing and basic operations
try:
    from OpenGL.GL import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    log.warning("PyOpenGL not available")

try:
    from pxr import Usd, UsdGeom, Gf, UsdImagingGL, Glf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    UsdImagingGL = None
    Glf = None


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

        # True when the stage's up-axis is Z (default in many DCCs).  usdview
        # detects this with UsdGeom.GetStageUpAxis and rotates the camera so
        # the scene appears upright; we do the same in _compute_camera_matrices.
        self.is_z_up = False

        # Hydra components
        self.engine = None
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
        """Configure the GL surface format exactly like usdview does.

        usdview (the proven reference using this same USD build) creates a
        plain QSurfaceFormat with only MSAA enabled — it does NOT request a
        version or a Core profile.  On Linux this yields a high-version
        Compatibility context that provides both the modern draw entry points
        Storm needs (glDrawArraysInstancedBaseInstance, etc.) AND the legacy
        fixed-function enums (GL_POINT_SMOOTH / GL_POINT_SPRITE) that Storm's
        HgiGL unconditionally references.  Requesting a Core profile makes
        those legacy enums illegal, which produces a cascade of GL errors and
        a black viewport.
        """
        fmt = QSurfaceFormat()
        fmt.setSamples(4)  # 4x MSAA, matching usdview's default
        self.setFormat(fmt)
    
    def initializeGL(self):
        """Initialize OpenGL and Hydra/Storm.

        Qt already ensures the context is current when initializeGL() is called.
        Do NOT call makeCurrent() here — it would try to make a context current
        that's already current, which is harmless but confusing.
        """
        if not USD_AVAILABLE:
            return

        try:
            # Initialize GLF (GL Framework) - required for Storm.
            # GlewInit is not available in all builds (absent in pip usd-core).
            if Glf and hasattr(Glf, 'GlewInit'):
                Glf.GlewInit()

            # Create Hydra engine.  SetEnableSceneIndex is a static/global
            # setting in USD 25.11 that enables the Hydra 2 scene index path.
            try:
                if hasattr(UsdImagingGL.Engine, 'SetEnableSceneIndex'):
                    UsdImagingGL.Engine.SetEnableSceneIndex(True)
            except Exception:
                pass

            self.engine = UsdImagingGL.Engine()

            # Select the Storm GPU renderer explicitly.
            available_renderers = self.engine.GetRendererPlugins()
            log.debug("Available Hydra renderers: %s", available_renderers)
            if not available_renderers:
                raise RuntimeError("No Hydra renderer plugins available")
            if 'HdStormRendererPlugin' in available_renderers:
                self.engine.SetRendererPlugin('HdStormRendererPlugin')
            else:
                self.engine.SetRendererPlugin(available_renderers[0])
            log.info("Hydra/Storm renderer: %s", self.engine.GetCurrentRendererId())

            # Render params (mirrors usdview's defaults).
            self.render_params = UsdImagingGL.RenderParams()
            self.render_params.frame = self.current_time
            self.render_params.complexity = 1.0
            self.render_params.drawMode = UsdImagingGL.DrawMode.DRAW_SHADED_SMOOTH
            self.render_params.enableLighting = True
            self.render_params.enableIdRender = False
            self.render_params.enableSampleAlphaToCoverage = True
            self.render_params.highlight = False
            self.render_params.cullStyle = UsdImagingGL.CullStyle.CULL_STYLE_BACK_UNLESS_DOUBLE_SIDED
            self.render_params.showGuides = False
            self.render_params.showProxy = True
            self.render_params.showRender = False
            self.render_params.clearColor = self.background_color

        except Exception as e:
            log.error("Error initializing Hydra: %s", e, exc_info=True)
            self.engine = None
    
    def resizeGL(self, w, h):
        """Handle viewport resize"""
        if not USD_AVAILABLE or not self.engine:
            return
        
        # Set viewport - USD 25.11+ uses GfVec4d(x, y, width, height)
        self.engine.SetRenderViewport(Gf.Vec4d(0, 0, w, h))
    
    def paintGL(self):
        """Render using Hydra/Storm.

        The GL state setup here mirrors usdview's _paintGLWithRenderer():
        clear the widget's framebuffer, enable depth test and alpha blending,
        then let the engine render and composite into it.  Qt makes the
        context current before paintGL, so makeCurrent() is not needed.
        """
        if not USD_AVAILABLE or not self.engine or not self.stage:
            return

        try:
            if OPENGL_AVAILABLE:
                glClearColor(
                    self.background_color[0],
                    self.background_color[1],
                    self.background_color[2],
                    self.background_color[3],
                )
                glEnable(GL_DEPTH_TEST)
                glDepthFunc(GL_LESS)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glEnable(GL_BLEND)
                glDepthMask(GL_TRUE)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            width = self.width()
            height = self.height()
            self.engine.SetRenderViewport(Gf.Vec4d(0, 0, width, height))

            view_matrix, projection_matrix = self._compute_camera_matrices()
            self.engine.SetCameraState(view_matrix, projection_matrix)

            # Without lights Storm renders all geometry black.  usdview enables
            # a camera headlight by default (cameraLightEnabled=True); mirror it.
            self._set_lighting(view_matrix)

            self.render_params.frame = Usd.TimeCode(self.current_time)

            root_prim = self.stage.GetPseudoRoot()
            self.engine.Render(root_prim, self.render_params)

        except Exception as e:
            log.error("Error rendering with Hydra: %s", e, exc_info=True)
    
    def _set_lighting(self, view_matrix):
        """Set a camera headlight + default material, mirroring usdview.

        usdview places a SimpleLight at the camera with the view-inverse as its
        transform and a default material (ambient 0.2, specular 0.1), plus a
        small scene ambient.  Without this, Storm draws every surface black.
        """
        if Glf is None:
            return
        try:
            view_inverse = view_matrix.GetInverse()
            cam_pos = view_inverse.ExtractTranslation()

            light = Glf.SimpleLight()
            light.ambient = Gf.Vec4f(0, 0, 0, 0)
            light.position = Gf.Vec4f(
                float(cam_pos[0]), float(cam_pos[1]), float(cam_pos[2]), 1.0
            )
            light.transform = view_inverse

            material = Glf.SimpleMaterial()
            kA, kS = 0.2, 0.1  # usdview DEFAULT_AMBIENT / DEFAULT_SPECULAR
            material.ambient = Gf.Vec4f(kA, kA, kA, 1.0)
            material.specular = Gf.Vec4f(kS, kS, kS, 1.0)
            material.shininess = 32.0

            scene_ambient = Gf.Vec4f(0.01, 0.01, 0.01, 1.0)
            self.engine.SetLightingState([light], material, scene_ambient)
        except Exception as e:
            log.warning("Could not set lighting state: %s", e)

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
        # The per-view math above is expressed in a Y-up convention.  For a
        # Z-up stage, rotate the camera offset and up vector by +90° about X
        # (Y-up -> Z-up), the same correction usdview applies via
        # Gf.Camera.Y_UP_TO_Z_UP_MATRIX, so the scene appears upright.
        target = Gf.Vec3d(
            self.camera_target[0], self.camera_target[1], self.camera_target[2]
        )
        if self.is_z_up:
            y_up_to_z_up = Gf.Matrix4d().SetRotate(
                Gf.Rotation(Gf.Vec3d.XAxis(), 90)
            )
            offset = y_up_to_z_up.TransformDir(camera_pos - target)
            camera_pos = target + offset
            up_vector = y_up_to_z_up.TransformDir(up_vector)

        view_matrix = Gf.Matrix4d()
        view_matrix.SetLookAt(camera_pos, target, up_vector)
        
        # Create projection matrix using Gf.Frustum — the same API USDView uses.
        # CameraUtil.Frustum is Gf.Frustum (re-exported); calling it with 6
        # plain floats was using a non-existent overload and raised TypeError
        # every frame (silently swallowed by paintGL's except clause).
        if view_mode == "Perspective":
            frustum = Gf.Frustum()
            frustum.SetPerspective(self.camera_fov, True, aspect, self.near_clip, self.far_clip)
            projection_matrix = frustum.ComputeProjectionMatrix()
        else:
            ortho_size = self.camera_distance * 0.5
            left = -ortho_size * aspect
            right = ortho_size * aspect
            bottom = -ortho_size
            top = ortho_size
            near = self.near_clip
            far = self.far_clip
            frustum = Gf.Frustum()
            frustum.SetOrthographic(left, right, bottom, top, near, far)
            projection_matrix = frustum.ComputeProjectionMatrix()
        
        return view_matrix, projection_matrix
    
    def _update_up_axis(self):
        """Detect the stage up-axis (matches usdview's UsdGeom.GetStageUpAxis)."""
        if self.stage:
            self.is_z_up = (
                UsdGeom.GetStageUpAxis(self.stage) == UsdGeom.Tokens.z
            )

    def set_stage_manager(self, manager):
        """Set the USD stage manager"""
        self.stage_manager = manager
        if manager and manager.stage:
            self.stage = manager.stage
            self._update_up_axis()

    def set_stage(self, stage):
        """Set the USD stage directly"""
        self.stage = stage
        self._update_up_axis()

    def update_geometry(self, time_code: float):
        """Update geometry for current time"""
        self.current_time = time_code
        if self.stage_manager:
            self.stage = self.stage_manager.stage
            self._update_up_axis()
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

