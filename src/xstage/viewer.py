#!/usr/bin/env python3
"""
USD Viewer and Converter Application
Professional USD file viewer with playback controls and 3D format conversion
Designed for VFX pipeline integration on RHEL9/AlmaLinux
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QFileDialog, QSlider,
    QPushButton, QLabel, QDockWidget, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QProgressDialog, QComboBox, QSpinBox, QGroupBox,
    QFormLayout, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QThread
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

try:
    from pxr import Usd, UsdGeom, Gf, Sdf, UsdShade, Kind
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    print("Warning: USD Python bindings not found. Install with: pip install usd-core")

import numpy as np


@dataclass
class ViewerSettings:
    """Viewer configuration and preferences"""
    background_color: tuple = (0.2, 0.2, 0.2, 1.0)
    grid_enabled: bool = True
    axis_enabled: bool = True
    auto_frame: bool = True
    fps: float = 24.0
    camera_fov: float = 60.0
    near_clip: float = 0.1
    far_clip: float = 10000.0


class USDStageManager:
    """Manages USD stage loading, playback, and queries"""
    
    def __init__(self):
        self.stage: Optional[Usd.Stage] = None
        self.current_time: float = 0.0
        self.time_range: tuple = (0.0, 0.0)
        self.fps: float = 24.0
        self.root_prim: Optional[Usd.Prim] = None
        
    def load_stage(self, filepath: str) -> bool:
        """Load a USD stage from file"""
        if not USD_AVAILABLE:
            return False
            
        try:
            self.stage = Usd.Stage.Open(filepath)
            if not self.stage:
                return False
                
            # Get time sampling info
            self.time_range = (
                self.stage.GetStartTimeCode(),
                self.stage.GetEndTimeCode()
            )
            self.fps = self.stage.GetFramesPerSecond()
            self.current_time = self.time_range[0]
            self.root_prim = self.stage.GetPseudoRoot()
            
            return True
        except Exception as e:
            print(f"Error loading USD stage: {e}")
            return False
    
    def get_geometry_data(self, time_code: float) -> Dict:
        """Extract geometry data at specific time for rendering"""
        if not self.stage:
            return {}
            
        geometry_data = {
            'meshes': [],
            'cameras': [],
            'lights': [],
            'bounds': None
        }
        
        # Traverse stage and collect renderable geometry
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                mesh_data = self._extract_mesh(prim, time_code)
                if mesh_data:
                    geometry_data['meshes'].append(mesh_data)
                    
            elif prim.IsA(UsdGeom.Camera):
                cam_data = self._extract_camera(prim, time_code)
                if cam_data:
                    geometry_data['cameras'].append(cam_data)
                    
            elif prim.IsA(UsdGeom.Light):
                light_data = self._extract_light(prim, time_code)
                if light_data:
                    geometry_data['lights'].append(light_data)
        
        # Calculate scene bounds
        if geometry_data['meshes']:
            geometry_data['bounds'] = self._calculate_bounds(geometry_data['meshes'])
            
        return geometry_data
    
    def _extract_mesh(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract mesh geometry data"""
        try:
            mesh = UsdGeom.Mesh(prim)
            
            # Get points
            points_attr = mesh.GetPointsAttr()
            points = points_attr.Get(time_code)
            if not points:
                return None
                
            # Get face vertex counts and indices
            fvc_attr = mesh.GetFaceVertexCountsAttr()
            fvi_attr = mesh.GetFaceVertexIndicesAttr()
            
            face_vertex_counts = fvc_attr.Get(time_code)
            face_vertex_indices = fvi_attr.Get(time_code)
            
            # Get transform
            xformable = UsdGeom.Xformable(prim)
            transform_matrix = xformable.ComputeLocalToWorldTransform(time_code)
            
            # Get normals if available
            normals_attr = mesh.GetNormalsAttr()
            normals = normals_attr.Get(time_code) if normals_attr else None
            
            return {
                'name': prim.GetPath().pathString,
                'points': np.array(points, dtype=np.float32),
                'face_vertex_counts': np.array(face_vertex_counts, dtype=np.int32),
                'face_vertex_indices': np.array(face_vertex_indices, dtype=np.int32),
                'normals': np.array(normals, dtype=np.float32) if normals else None,
                'transform': np.array(transform_matrix, dtype=np.float32).reshape(4, 4),
            }
        except Exception as e:
            print(f"Error extracting mesh {prim.GetPath()}: {e}")
            return None
    
    def _extract_camera(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract camera data"""
        try:
            camera = UsdGeom.Camera(prim)
            xformable = UsdGeom.Xformable(prim)
            transform = xformable.ComputeLocalToWorldTransform(time_code)
            
            return {
                'name': prim.GetPath().pathString,
                'transform': np.array(transform, dtype=np.float32).reshape(4, 4),
                'focal_length': camera.GetFocalLengthAttr().Get(time_code),
                'h_aperture': camera.GetHorizontalApertureAttr().Get(time_code),
                'v_aperture': camera.GetVerticalApertureAttr().Get(time_code),
            }
        except Exception as e:
            print(f"Error extracting camera {prim.GetPath()}: {e}")
            return None
    
    def _extract_light(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract light data"""
        try:
            xformable = UsdGeom.Xformable(prim)
            transform = xformable.ComputeLocalToWorldTransform(time_code)
            
            return {
                'name': prim.GetPath().pathString,
                'type': prim.GetTypeName(),
                'transform': np.array(transform, dtype=np.float32).reshape(4, 4),
            }
        except Exception as e:
            print(f"Error extracting light {prim.GetPath()}: {e}")
            return None
    
    def _calculate_bounds(self, meshes: List[Dict]) -> Dict:
        """Calculate bounding box for all meshes"""
        if not meshes:
            return {'min': np.array([0, 0, 0]), 'max': np.array([0, 0, 0]), 'center': np.array([0, 0, 0])}
            
        all_points = []
        for mesh in meshes:
            points = mesh['points']
            transform = mesh['transform']
            
            # Transform points to world space
            homogeneous = np.hstack([points, np.ones((len(points), 1))])
            transformed = (transform @ homogeneous.T).T[:, :3]
            all_points.append(transformed)
        
        all_points = np.vstack(all_points)
        bounds_min = np.min(all_points, axis=0)
        bounds_max = np.max(all_points, axis=0)
        center = (bounds_min + bounds_max) / 2.0
        
        return {
            'min': bounds_min,
            'max': bounds_max,
            'center': center,
            'size': bounds_max - bounds_min
        }
    
    def get_stage_info(self) -> Dict:
        """Get stage metadata and info"""
        if not self.stage:
            return {}
            
        return {
            'path': self.stage.GetRootLayer().identifier,
            'start_time': self.time_range[0],
            'end_time': self.time_range[1],
            'fps': self.fps,
            'up_axis': UsdGeom.GetStageUpAxis(self.stage),
            'meters_per_unit': UsdGeom.GetStageMetersPerUnit(self.stage),
        }


class ViewportWidget(QOpenGLWidget):
    """OpenGL viewport for USD rendering"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage_manager = None
        self.geometry_data = {}
        self.settings = ViewerSettings()
        
        # Camera controls
        self.camera_distance = 10.0
        self.camera_rotation_x = 30.0
        self.camera_rotation_y = 45.0
        self.camera_target = np.array([0.0, 0.0, 0.0])
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.is_rotating = False
        self.is_panning = False
        
    def set_stage_manager(self, manager: USDStageManager):
        """Set the USD stage manager"""
        self.stage_manager = manager
        
    def update_geometry(self, time_code: float):
        """Update geometry for current time"""
        if self.stage_manager:
            self.geometry_data = self.stage_manager.get_geometry_data(time_code)
            
            # Auto-frame on first load
            if self.settings.auto_frame and 'bounds' in self.geometry_data and self.geometry_data['bounds']:
                self.frame_bounds(self.geometry_data['bounds'])
                self.settings.auto_frame = False
                
            self.update()
    
    def frame_bounds(self, bounds: Dict):
        """Frame camera to fit bounds"""
        if not bounds:
            return
            
        self.camera_target = bounds['center']
        size = np.max(bounds['size'])
        self.camera_distance = size * 2.0
        
    def initializeGL(self):
        """Initialize OpenGL settings"""
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
        
    def resizeGL(self, w, h):
        """Handle viewport resize"""
        glViewport(0, 0, w, h)
        
    def paintGL(self):
        """Render the scene"""
        # Clear buffers
        bg = self.settings.background_color
        glClearColor(*bg)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width() / max(self.height(), 1)
        gluPerspective(self.settings.camera_fov, aspect, 
                      self.settings.near_clip, self.settings.far_clip)
        
        # Set up camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Calculate camera position from rotation
        cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
        cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        
        camera_pos = self.camera_target + np.array([cam_x, cam_y, cam_z])
        
        gluLookAt(
            camera_pos[0], camera_pos[1], camera_pos[2],
            self.camera_target[0], self.camera_target[1], self.camera_target[2],
            0, 1, 0
        )
        
        # Draw grid
        if self.settings.grid_enabled:
            self.draw_grid()
        
        # Draw axis
        if self.settings.axis_enabled:
            self.draw_axis()
        
        # Draw geometry
        self.draw_geometry()
        
    def draw_grid(self):
        """Draw ground grid"""
        glDisable(GL_LIGHTING)
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        
        grid_size = 20
        grid_spacing = 1.0
        
        for i in range(-grid_size, grid_size + 1):
            # Lines along X
            glVertex3f(-grid_size * grid_spacing, 0, i * grid_spacing)
            glVertex3f(grid_size * grid_spacing, 0, i * grid_spacing)
            # Lines along Z
            glVertex3f(i * grid_spacing, 0, -grid_size * grid_spacing)
            glVertex3f(i * grid_spacing, 0, grid_size * grid_spacing)
            
        glEnd()
        glEnable(GL_LIGHTING)
        
    def draw_axis(self):
        """Draw coordinate axis"""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        
        # X axis - Red
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(2, 0, 0)
        
        # Y axis - Green
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 2, 0)
        
        # Z axis - Blue
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 2)
        
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
        
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
    
    def draw_mesh(self, mesh: Dict):
        """Draw a single mesh"""
        points = mesh['points']
        fvc = mesh['face_vertex_counts']
        fvi = mesh['face_vertex_indices']
        normals = mesh['normals']
        
        # Apply transform
        glPushMatrix()
        transform = mesh['transform'].T  # OpenGL uses column-major
        glMultMatrixf(transform.flatten())
        
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
            
        self.camera_distance = np.clip(self.camera_distance, 0.1, 1000.0)
        self.update()


class USDViewerWindow(QMainWindow):
    """Main window for USD viewer application"""
    
    def __init__(self):
        super().__init__()
        self.stage_manager = USDStageManager()
        self.current_file = None
        self.is_playing = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.advance_frame)
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("USD Viewer - NOX VFX")
        self.setGeometry(100, 100, 1600, 900)
        
        # Create central widget with viewport
        self.viewport = ViewportWidget()
        self.viewport.set_stage_manager(self.stage_manager)
        self.setCentralWidget(self.viewport)
        
        # Create menus
        self.create_menus()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create dock widgets
        self.create_hierarchy_dock()
        self.create_info_dock()
        self.create_playback_dock()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open USD...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        import_action = QAction("&Import and Convert...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_convert_file)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        grid_action = QAction("Show &Grid", self, checkable=True)
        grid_action.setChecked(True)
        grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(grid_action)
        
        axis_action = QAction("Show &Axis", self, checkable=True)
        axis_action.setChecked(True)
        axis_action.triggered.connect(self.toggle_axis)
        view_menu.addAction(axis_action)
        
        frame_action = QAction("&Frame All", self)
        frame_action.setShortcut("F")
        frame_action.triggered.connect(self.frame_all)
        view_menu.addAction(frame_action)
        
    def create_toolbar(self):
        """Create main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # File operations
        open_btn = QPushButton("Open USD")
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)
        
        import_btn = QPushButton("Import/Convert")
        import_btn.clicked.connect(self.import_convert_file)
        toolbar.addWidget(import_btn)
        
        toolbar.addSeparator()
        
        # View controls
        frame_btn = QPushButton("Frame All")
        frame_btn.clicked.connect(self.frame_all)
        toolbar.addWidget(frame_btn)
        
    def create_hierarchy_dock(self):
        """Create scene hierarchy dock"""
        dock = QDockWidget("Scene Hierarchy", self)
        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree.setHeaderLabel("Prims")
        dock.setWidget(self.hierarchy_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        
    def create_info_dock(self):
        """Create stage info dock"""
        dock = QDockWidget("Stage Info", self)
        info_widget = QWidget()
        layout = QFormLayout()
        
        self.info_labels = {}
        for key in ['path', 'start_time', 'end_time', 'fps', 'up_axis', 'meters_per_unit']:
            label = QLabel("-")
            self.info_labels[key] = label
            layout.addRow(key.replace('_', ' ').title() + ":", label)
            
        info_widget.setLayout(layout)
        dock.setWidget(info_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        
    def create_playback_dock(self):
        """Create playback controls dock"""
        dock = QDockWidget("Playback", self)
        playback_widget = QWidget()
        layout = QVBoxLayout()
        
        # Timeline slider
        timeline_layout = QHBoxLayout()
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.valueChanged.connect(self.on_timeline_changed)
        self.frame_label = QLabel("Frame: 0")
        timeline_layout.addWidget(self.timeline_slider)
        timeline_layout.addWidget(self.frame_label)
        layout.addLayout(timeline_layout)
        
        # Playback buttons
        button_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_playback)
        button_layout.addWidget(self.play_button)
        
        first_frame_btn = QPushButton("|<")
        first_frame_btn.clicked.connect(self.goto_first_frame)
        button_layout.addWidget(first_frame_btn)
        
        prev_frame_btn = QPushButton("<")
        prev_frame_btn.clicked.connect(self.prev_frame)
        button_layout.addWidget(prev_frame_btn)
        
        next_frame_btn = QPushButton(">")
        next_frame_btn.clicked.connect(self.next_frame)
        button_layout.addWidget(next_frame_btn)
        
        last_frame_btn = QPushButton(">|")
        last_frame_btn.clicked.connect(self.goto_last_frame)
        button_layout.addWidget(last_frame_btn)
        
        layout.addLayout(button_layout)
        
        # FPS control
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 120)
        self.fps_spinbox.setValue(24)
        self.fps_spinbox.valueChanged.connect(self.on_fps_changed)
        fps_layout.addWidget(self.fps_spinbox)
        fps_layout.addStretch()
        layout.addLayout(fps_layout)
        
        playback_widget.setLayout(layout)
        dock.setWidget(playback_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        
    def setup_connections(self):
        """Setup signal/slot connections"""
        pass
        
    def open_file(self):
        """Open USD file dialog"""
        if not USD_AVAILABLE:
            QMessageBox.warning(self, "USD Not Available", 
                              "USD Python bindings not installed. Please install usd-core.")
            return
            
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open USD File", "",
            "USD Files (*.usd *.usda *.usdc *.usdz);;All Files (*)"
        )
        
        if filepath:
            self.load_usd_file(filepath)
            
    def load_usd_file(self, filepath: str):
        """Load and display USD file"""
        self.statusBar().showMessage(f"Loading {filepath}...")
        
        if self.stage_manager.load_stage(filepath):
            self.current_file = filepath
            
            # Update UI
            info = self.stage_manager.get_stage_info()
            for key, label in self.info_labels.items():
                if key in info:
                    label.setText(str(info[key]))
            
            # Setup timeline
            start = int(self.stage_manager.time_range[0])
            end = int(self.stage_manager.time_range[1])
            self.timeline_slider.setRange(start, end)
            self.timeline_slider.setValue(start)
            self.fps_spinbox.setValue(int(self.stage_manager.fps))
            
            # Update viewport
            self.viewport.update_geometry(float(start))
            
            # Update hierarchy
            self.update_hierarchy()
            
            self.statusBar().showMessage(f"Loaded: {filepath}", 5000)
            self.setWindowTitle(f"USD Viewer - {Path(filepath).name}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to load USD file:\n{filepath}")
            self.statusBar().showMessage("Ready")
            
    def update_hierarchy(self):
        """Update scene hierarchy tree"""
        self.hierarchy_tree.clear()
        
        if not self.stage_manager.stage:
            return
            
        def add_prim_to_tree(prim: Usd.Prim, parent_item: QTreeWidgetItem = None):
            """Recursively add prims to tree"""
            item = QTreeWidgetItem([prim.GetName()])
            
            if parent_item:
                parent_item.addChild(item)
            else:
                self.hierarchy_tree.addTopLevelItem(item)
            
            for child in prim.GetChildren():
                add_prim_to_tree(child, item)
                
        root = self.stage_manager.stage.GetPseudoRoot()
        for child in root.GetChildren():
            add_prim_to_tree(child)
            
        self.hierarchy_tree.expandAll()
        
    def import_convert_file(self):
        """Import and convert 3D file to USD"""
        from converter_dialog import ConverterDialog
        dialog = ConverterDialog(self)
        if dialog.exec():
            output_path = dialog.get_output_path()
            if output_path and os.path.exists(output_path):
                self.load_usd_file(output_path)
                
    def toggle_playback(self):
        """Toggle playback on/off"""
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_button.setText("Pause")
            fps = self.fps_spinbox.value()
            interval = int(1000.0 / fps)
            self.playback_timer.start(interval)
        else:
            self.play_button.setText("Play")
            self.playback_timer.stop()
            
    def advance_frame(self):
        """Advance to next frame during playback"""
        current = self.timeline_slider.value()
        maximum = self.timeline_slider.maximum()
        
        if current >= maximum:
            current = self.timeline_slider.minimum()
        else:
            current += 1
            
        self.timeline_slider.setValue(current)
        
    def on_timeline_changed(self, value):
        """Handle timeline slider change"""
        self.frame_label.setText(f"Frame: {value}")
        self.viewport.update_geometry(float(value))
        
    def on_fps_changed(self, fps):
        """Handle FPS change"""
        if self.is_playing:
            interval = int(1000.0 / fps)
            self.playback_timer.setInterval(interval)
            
    def goto_first_frame(self):
        """Jump to first frame"""
        self.timeline_slider.setValue(self.timeline_slider.minimum())
        
    def goto_last_frame(self):
        """Jump to last frame"""
        self.timeline_slider.setValue(self.timeline_slider.maximum())
        
    def prev_frame(self):
        """Go to previous frame"""
        self.timeline_slider.setValue(self.timeline_slider.value() - 1)
        
    def next_frame(self):
        """Go to next frame"""
        self.timeline_slider.setValue(self.timeline_slider.value() + 1)
        
    def toggle_grid(self, checked):
        """Toggle grid display"""
        self.viewport.settings.grid_enabled = checked
        self.viewport.update()
        
    def toggle_axis(self, checked):
        """Toggle axis display"""
        self.viewport.settings.axis_enabled = checked
        self.viewport.update()
        
    def frame_all(self):
        """Frame all geometry in view"""
        if self.viewport.geometry_data and 'bounds' in self.viewport.geometry_data:
            self.viewport.frame_bounds(self.viewport.geometry_data['bounds'])
            self.viewport.update()


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("USD Viewer")
    app.setOrganizationName("NOX VFX")
    
    window = USDViewerWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()