"""
3D Transform Gizmo (Omniverse-style)
Interactive manipulator for translating, rotating, and scaling prims in the viewport
"""

from typing import Optional, Tuple, List
import numpy as np
from enum import Enum

try:
    from pxr import Usd, UsdGeom, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class GizmoMode(Enum):
    """Gizmo transformation mode"""
    TRANSLATE = "translate"
    ROTATE = "rotate"
    SCALE = "scale"


class GizmoAxis(Enum):
    """Gizmo axis"""
    X = "x"
    Y = "y"
    Z = "z"
    XY = "xy"
    XZ = "xz"
    YZ = "yz"
    NONE = "none"


class TransformGizmo:
    """3D transform gizmo for manipulating prims (Omniverse-style)"""
    
    def __init__(self):
        self.mode = GizmoMode.TRANSLATE
        self.selected_axis = GizmoAxis.NONE
        self.is_active = False
        self.position = np.array([0.0, 0.0, 0.0])
        self.size = 1.0  # Gizmo size in world units
        self.hover_axis = GizmoAxis.NONE
        
        # Colors (Omniverse-style: Red=X, Green=Y, Blue=Z)
        self.colors = {
            GizmoAxis.X: (1.0, 0.2, 0.2),
            GizmoAxis.Y: (0.2, 1.0, 0.2),
            GizmoAxis.Z: (0.2, 0.2, 1.0),
            GizmoAxis.XY: (1.0, 1.0, 0.2),
            GizmoAxis.XZ: (1.0, 0.2, 1.0),
            GizmoAxis.YZ: (0.2, 1.0, 1.0),
        }
        
        # Highlight color
        self.highlight_color = (1.0, 1.0, 0.0)  # Yellow
        
        # Drag state
        self.drag_start_pos = None
        self.drag_start_mouse = None
        self.drag_plane_normal = None
    
    def set_mode(self, mode: GizmoMode):
        """Set gizmo transformation mode"""
        self.mode = mode
        self.selected_axis = GizmoAxis.NONE
    
    def set_position(self, position: np.ndarray):
        """Set gizmo position (world space)"""
        self.position = np.array(position)
    
    def set_size(self, size: float):
        """Set gizmo size (world units)"""
        self.size = max(0.1, size)
    
    def get_screen_space_position(self, camera_pos: np.ndarray, camera_target: np.ndarray, 
                                   view_matrix, projection_matrix, viewport_size: Tuple[int, int]) -> Tuple[float, float]:
        """Convert gizmo world position to screen space coordinates"""
        # This is a simplified version - in a real implementation, you'd use proper projection
        # For now, we'll use a distance-based approximation
        to_gizmo = self.position - camera_pos
        distance = np.linalg.norm(to_gizmo)
        
        # Simple screen space calculation (would need proper matrix multiplication in real implementation)
        return (viewport_size[0] / 2, viewport_size[1] / 2)
    
    def pick_axis(self, mouse_pos: Tuple[float, float], camera_pos: np.ndarray, 
                  camera_target: np.ndarray, view_matrix, projection_matrix,
                  viewport_size: Tuple[int, int], view_direction: np.ndarray) -> GizmoAxis:
        """Pick which gizmo axis/handle is under the mouse cursor"""
        # Calculate distance from gizmo to camera
        to_gizmo = self.position - camera_pos
        distance = np.linalg.norm(to_gizmo)
        
        # Convert gizmo position to screen space (simplified)
        # In a real implementation, you'd project the gizmo handles to screen space
        # and check which one is closest to the mouse position
        
        # For now, return NONE - this would need proper ray casting or screen-space picking
        return GizmoAxis.NONE
    
    def start_drag(self, mouse_pos: Tuple[float, float], camera_pos: np.ndarray,
                   camera_target: np.ndarray, view_direction: np.ndarray):
        """Start dragging the gizmo"""
        self.is_active = True
        self.drag_start_mouse = mouse_pos
        self.drag_start_pos = self.position.copy()
        
        # Calculate drag plane normal based on selected axis
        if self.selected_axis == GizmoAxis.X:
            self.drag_plane_normal = np.array([0, 1, 0])  # Drag in YZ plane
        elif self.selected_axis == GizmoAxis.Y:
            self.drag_plane_normal = np.array([1, 0, 0])  # Drag in XZ plane
        elif self.selected_axis == GizmoAxis.Z:
            self.drag_plane_normal = np.array([0, 1, 0])  # Drag in XY plane
        else:
            # Free drag - use camera plane
            self.drag_plane_normal = view_direction
    
    def update_drag(self, mouse_pos: Tuple[float, float], camera_pos: np.ndarray,
                    camera_target: np.ndarray, view_direction: np.ndarray,
                    view_matrix, projection_matrix, viewport_size: Tuple[int, int]) -> Optional[np.ndarray]:
        """Update drag and return transform delta"""
        if not self.is_active or self.selected_axis == GizmoAxis.NONE:
            return None
        
        # Calculate mouse delta
        mouse_delta = np.array([
            mouse_pos[0] - self.drag_start_mouse[0],
            mouse_pos[1] - self.drag_start_mouse[1],
            0.0
        ])
        
        # Convert screen delta to world delta based on mode and axis
        if self.mode == GizmoMode.TRANSLATE:
            return self._calculate_translate_delta(mouse_delta, camera_pos, view_direction)
        elif self.mode == GizmoMode.ROTATE:
            return self._calculate_rotate_delta(mouse_pos, camera_pos, camera_target)
        elif self.mode == GizmoMode.SCALE:
            return self._calculate_scale_delta(mouse_delta, camera_pos, view_direction)
        
        return None
    
    def _calculate_translate_delta(self, mouse_delta: np.ndarray, camera_pos: np.ndarray,
                                   view_direction: np.ndarray) -> np.ndarray:
        """Calculate translation delta from mouse movement"""
        # Scale based on distance to gizmo
        to_gizmo = self.position - camera_pos
        distance = np.linalg.norm(to_gizmo)
        sensitivity = distance * 0.001
        
        delta = np.array([0.0, 0.0, 0.0])
        
        if self.selected_axis == GizmoAxis.X:
            # Move along X axis
            delta[0] = mouse_delta[0] * sensitivity
        elif self.selected_axis == GizmoAxis.Y:
            # Move along Y axis
            delta[1] = -mouse_delta[1] * sensitivity  # Invert Y
        elif self.selected_axis == GizmoAxis.Z:
            # Move along Z axis (depth)
            delta[2] = mouse_delta[1] * sensitivity
        elif self.selected_axis == GizmoAxis.XY:
            # Move in XY plane
            delta[0] = mouse_delta[0] * sensitivity
            delta[1] = -mouse_delta[1] * sensitivity
        elif self.selected_axis == GizmoAxis.XZ:
            # Move in XZ plane
            delta[0] = mouse_delta[0] * sensitivity
            delta[2] = mouse_delta[1] * sensitivity
        elif self.selected_axis == GizmoAxis.YZ:
            # Move in YZ plane
            delta[1] = -mouse_delta[1] * sensitivity
            delta[2] = mouse_delta[0] * sensitivity
        
        return delta
    
    def _calculate_rotate_delta(self, mouse_pos: Tuple[float, float], 
                                camera_pos: np.ndarray, camera_target: np.ndarray) -> np.ndarray:
        """Calculate rotation delta from mouse movement"""
        # Rotation is more complex - would need proper arcball or trackball calculation
        # For now, return a simple delta
        return np.array([0.0, 0.0, 0.0])
    
    def _calculate_scale_delta(self, mouse_delta: np.ndarray, camera_pos: np.ndarray,
                               view_direction: np.ndarray) -> np.ndarray:
        """Calculate scale delta from mouse movement"""
        to_gizmo = self.position - camera_pos
        distance = np.linalg.norm(to_gizmo)
        sensitivity = distance * 0.001
        
        delta = np.array([1.0, 1.0, 1.0])  # Scale is multiplicative
        
        if self.selected_axis == GizmoAxis.X:
            delta[0] = 1.0 + mouse_delta[0] * sensitivity
        elif self.selected_axis == GizmoAxis.Y:
            delta[1] = 1.0 - mouse_delta[1] * sensitivity
        elif self.selected_axis == GizmoAxis.Z:
            delta[2] = 1.0 + mouse_delta[1] * sensitivity
        
        return delta
    
    def end_drag(self):
        """End dragging"""
        self.is_active = False
        self.drag_start_pos = None
        self.drag_start_mouse = None
        self.drag_plane_normal = None
    
    def draw(self, gl_enable, gl_disable, gl_begin, gl_end, gl_vertex3f, gl_color3f,
             gl_line_width, gl_point_size, gl_push_matrix, gl_pop_matrix, gl_translatef,
             gl_rotatef, gl_scalef, gl_mult_matrixf):
        """Draw the gizmo using OpenGL calls"""
        if self.mode == GizmoMode.TRANSLATE:
            self._draw_translate_gizmo(gl_enable, gl_disable, gl_begin, gl_end, gl_vertex3f,
                                      gl_color3f, gl_line_width, gl_push_matrix, gl_pop_matrix,
                                      gl_translatef)
        elif self.mode == GizmoMode.ROTATE:
            self._draw_rotate_gizmo(gl_enable, gl_disable, gl_begin, gl_end, gl_vertex3f,
                                   gl_color3f, gl_line_width, gl_push_matrix, gl_pop_matrix,
                                   gl_translatef, gl_rotatef)
        elif self.mode == GizmoMode.SCALE:
            self._draw_scale_gizmo(gl_enable, gl_disable, gl_begin, gl_end, gl_vertex3f,
                                  gl_color3f, gl_line_width, gl_push_matrix, gl_pop_matrix,
                                  gl_translatef)
    
    def _draw_translate_gizmo(self, gl_enable, gl_disable, gl_begin, gl_end, gl_vertex3f,
                              gl_color3f, gl_line_width, gl_push_matrix, gl_pop_matrix,
                              gl_translatef):
        """Draw translation gizmo (arrows)"""
        gl_disable('GL_LIGHTING')
        gl_disable('GL_DEPTH_TEST')
        
        gl_push_matrix()
        gl_translatef(self.position[0], self.position[1], self.position[2])
        
        arrow_length = self.size
        arrow_shaft_length = arrow_length * 0.7
        arrow_head_length = arrow_length * 0.3
        arrow_head_width = self.size * 0.1
        
        # X axis (Red)
        color = self.highlight_color if self.selected_axis == GizmoAxis.X else self.colors[GizmoAxis.X]
        gl_color3f(*color)
        gl_line_width(3.0)
        gl_begin('GL_LINES')
        gl_vertex3f(0, 0, 0)
        gl_vertex3f(arrow_shaft_length, 0, 0)
        gl_end()
        
        # Arrow head
        gl_begin('GL_TRIANGLES')
        gl_vertex3f(arrow_shaft_length, 0, 0)
        gl_vertex3f(arrow_shaft_length - arrow_head_length, arrow_head_width, 0)
        gl_vertex3f(arrow_shaft_length - arrow_head_length, -arrow_head_width, 0)
        gl_vertex3f(arrow_shaft_length, 0, 0)
        gl_vertex3f(arrow_shaft_length - arrow_head_length, 0, arrow_head_width)
        gl_vertex3f(arrow_shaft_length - arrow_head_length, 0, -arrow_head_width)
        gl_end()
        
        # Y axis (Green)
        color = self.highlight_color if self.selected_axis == GizmoAxis.Y else self.colors[GizmoAxis.Y]
        gl_color3f(*color)
        gl_begin('GL_LINES')
        gl_vertex3f(0, 0, 0)
        gl_vertex3f(0, arrow_shaft_length, 0)
        gl_end()
        
        # Arrow head
        gl_begin('GL_TRIANGLES')
        gl_vertex3f(0, arrow_shaft_length, 0)
        gl_vertex3f(arrow_head_width, arrow_shaft_length - arrow_head_length, 0)
        gl_vertex3f(-arrow_head_width, arrow_shaft_length - arrow_head_length, 0)
        gl_vertex3f(0, arrow_shaft_length, 0)
        gl_vertex3f(0, arrow_shaft_length - arrow_head_length, arrow_head_width)
        gl_vertex3f(0, arrow_shaft_length - arrow_head_length, -arrow_head_width)
        gl_end()
        
        # Z axis (Blue)
        color = self.highlight_color if self.selected_axis == GizmoAxis.Z else self.colors[GizmoAxis.Z]
        gl_color3f(*color)
        gl_begin('GL_LINES')
        gl_vertex3f(0, 0, 0)
        gl_vertex3f(0, 0, arrow_shaft_length)
        gl_end()
        
        # Arrow head
        gl_begin('GL_TRIANGLES')
        gl_vertex3f(0, 0, arrow_shaft_length)
        gl_vertex3f(arrow_head_width, 0, arrow_shaft_length - arrow_head_length)
        gl_vertex3f(-arrow_head_width, 0, arrow_shaft_length - arrow_head_length)
        gl_vertex3f(0, 0, arrow_shaft_length)
        gl_vertex3f(0, arrow_head_width, arrow_shaft_length - arrow_head_length)
        gl_vertex3f(0, -arrow_head_width, arrow_shaft_length - arrow_head_length)
        gl_end()
        
        gl_line_width(1.0)
        gl_pop_matrix()
        gl_enable('GL_DEPTH_TEST')
        gl_enable('GL_LIGHTING')
    
    def _draw_rotate_gizmo(self, gl_enable, gl_disable, gl_begin, gl_end, gl_vertex3f,
                           gl_color3f, gl_line_width, gl_push_matrix, gl_pop_matrix,
                           gl_translatef, gl_rotatef):
        """Draw rotation gizmo (circles)"""
        gl_disable('GL_LIGHTING')
        gl_disable('GL_DEPTH_TEST')
        
        gl_push_matrix()
        gl_translatef(self.position[0], self.position[1], self.position[2])
        
        circle_radius = self.size
        num_segments = 64
        
        # X axis circle (Red) - in YZ plane
        color = self.highlight_color if self.selected_axis == GizmoAxis.X else self.colors[GizmoAxis.X]
        gl_color3f(*color)
        gl_line_width(3.0)
        gl_begin('GL_LINE_LOOP')
        for i in range(num_segments):
            angle = 2.0 * np.pi * i / num_segments
            gl_vertex3f(0, circle_radius * np.cos(angle), circle_radius * np.sin(angle))
        gl_end()
        
        # Y axis circle (Green) - in XZ plane
        color = self.highlight_color if self.selected_axis == GizmoAxis.Y else self.colors[GizmoAxis.Y]
        gl_color3f(*color)
        gl_begin('GL_LINE_LOOP')
        for i in range(num_segments):
            angle = 2.0 * np.pi * i / num_segments
            gl_vertex3f(circle_radius * np.cos(angle), 0, circle_radius * np.sin(angle))
        gl_end()
        
        # Z axis circle (Blue) - in XY plane
        color = self.highlight_color if self.selected_axis == GizmoAxis.Z else self.colors[GizmoAxis.Z]
        gl_color3f(*color)
        gl_begin('GL_LINE_LOOP')
        for i in range(num_segments):
            angle = 2.0 * np.pi * i / num_segments
            gl_vertex3f(circle_radius * np.cos(angle), circle_radius * np.sin(angle), 0)
        gl_end()
        
        gl_line_width(1.0)
        gl_pop_matrix()
        gl_enable('GL_DEPTH_TEST')
        gl_enable('GL_LIGHTING')
    
    def _draw_scale_gizmo(self, gl_enable, gl_disable, gl_begin, gl_end, gl_vertex3f,
                          gl_color3f, gl_line_width, gl_push_matrix, gl_pop_matrix,
                          gl_translatef):
        """Draw scale gizmo (boxes/arrows)"""
        gl_disable('GL_LIGHTING')
        gl_disable('GL_DEPTH_TEST')
        
        gl_push_matrix()
        gl_translatef(self.position[0], self.position[1], self.position[2])
        
        box_size = self.size * 0.15
        
        # X axis (Red)
        color = self.highlight_color if self.selected_axis == GizmoAxis.X else self.colors[GizmoAxis.X]
        gl_color3f(*color)
        gl_line_width(3.0)
        gl_begin('GL_LINES')
        gl_vertex3f(0, 0, 0)
        gl_vertex3f(self.size, 0, 0)
        gl_end()
        
        # Box at end
        gl_begin('GL_QUADS')
        # Front face
        gl_vertex3f(self.size, -box_size, -box_size)
        gl_vertex3f(self.size, box_size, -box_size)
        gl_vertex3f(self.size, box_size, box_size)
        gl_vertex3f(self.size, -box_size, box_size)
        # Back face
        gl_vertex3f(self.size, -box_size, -box_size)
        gl_vertex3f(self.size, -box_size, box_size)
        gl_vertex3f(self.size, box_size, box_size)
        gl_vertex3f(self.size, box_size, -box_size)
        gl_end()
        
        # Y axis (Green)
        color = self.highlight_color if self.selected_axis == GizmoAxis.Y else self.colors[GizmoAxis.Y]
        gl_color3f(*color)
        gl_begin('GL_LINES')
        gl_vertex3f(0, 0, 0)
        gl_vertex3f(0, self.size, 0)
        gl_end()
        
        # Box at end
        gl_begin('GL_QUADS')
        gl_vertex3f(-box_size, self.size, -box_size)
        gl_vertex3f(box_size, self.size, -box_size)
        gl_vertex3f(box_size, self.size, box_size)
        gl_vertex3f(-box_size, self.size, box_size)
        gl_vertex3f(-box_size, self.size, -box_size)
        gl_vertex3f(-box_size, self.size, box_size)
        gl_vertex3f(box_size, self.size, box_size)
        gl_vertex3f(box_size, self.size, -box_size)
        gl_end()
        
        # Z axis (Blue)
        color = self.highlight_color if self.selected_axis == GizmoAxis.Z else self.colors[GizmoAxis.Z]
        gl_color3f(*color)
        gl_begin('GL_LINES')
        gl_vertex3f(0, 0, 0)
        gl_vertex3f(0, 0, self.size)
        gl_end()
        
        # Box at end
        gl_begin('GL_QUADS')
        gl_vertex3f(-box_size, -box_size, self.size)
        gl_vertex3f(box_size, -box_size, self.size)
        gl_vertex3f(box_size, box_size, self.size)
        gl_vertex3f(-box_size, box_size, self.size)
        gl_vertex3f(-box_size, -box_size, self.size)
        gl_vertex3f(-box_size, box_size, self.size)
        gl_vertex3f(box_size, box_size, self.size)
        gl_vertex3f(box_size, -box_size, self.size)
        gl_end()
        
        gl_line_width(1.0)
        gl_pop_matrix()
        gl_enable('GL_DEPTH_TEST')
        gl_enable('GL_LIGHTING')
