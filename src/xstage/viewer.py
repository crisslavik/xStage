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
    from pxr import Usd, UsdGeom, Gf, Sdf, UsdShade, Kind, UsdLux, UsdCollectionAPI, UsdRender, UsdSkel, UsdUtils
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    print("Warning: USD Python bindings not found. Install with: pip install usd-core")
    
    # Create dummy classes for type hints
    class UsdLux:
        pass
    class UsdCollectionAPI:
        pass
    class UsdRender:
        pass
    class UsdSkel:
        pass
    class UsdUtils:
        pass

import numpy as np

# Import UsdLux support if available
try:
    from .usd_lux_support import UsdLuxExtractor
except ImportError:
    UsdLuxExtractor = None


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
            'materials': [],
            'collections': [],
            'variants': [],
            'primvars': [],
            'render_settings': [],
            'skeletons': [],
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
                    
            elif USD_AVAILABLE and prim.IsA(UsdLux.Light):
                # Use modern UsdLux instead of deprecated UsdGeom.Light
                if UsdLuxExtractor:
                    light_data = UsdLuxExtractor.extract_light(prim, time_code)
                else:
                    light_data = self._extract_light_fallback(prim, time_code)
                if light_data:
                    geometry_data['lights'].append(light_data)
                    
            elif USD_AVAILABLE and prim.IsA(UsdShade.Material):
                material_data = self._extract_material(prim, time_code)
                if material_data:
                    geometry_data['materials'].append(material_data)
                    
            elif USD_AVAILABLE and prim.HasAPI(UsdCollectionAPI):
                collection_data = self._extract_collection(prim, time_code)
                if collection_data:
                    geometry_data['collections'].append(collection_data)
                    
            elif USD_AVAILABLE and prim.GetVariantSets().GetNames():
                variant_data = self._extract_variants(prim)
                if variant_data:
                    geometry_data['variants'].append(variant_data)
                    
            elif USD_AVAILABLE and prim.IsA(UsdRender.RenderSettings):
                render_data = self._extract_render_settings(prim, time_code)
                if render_data:
                    geometry_data['render_settings'].append(render_data)
                    
            elif USD_AVAILABLE and prim.IsA(UsdSkel.Root):
                skeleton_data = self._extract_skeleton(prim, time_code)
                if skeleton_data:
                    geometry_data['skeletons'].append(skeleton_data)
        
        # Extract primvars from meshes
        for mesh_data in geometry_data['meshes']:
            prim = self.stage.GetPrimAtPath(mesh_data['name'])
            if prim:
                primvars = self._extract_primvars(prim, time_code)
                if primvars:
                    mesh_data['primvars'] = primvars
                    geometry_data['primvars'].extend(primvars)
        
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
        """Extract light data - DEPRECATED: Use UsdLuxExtractor instead"""
        # This method is kept for backward compatibility but should use UsdLuxExtractor
        if USD_AVAILABLE and prim.IsA(UsdLux.Light):
            if UsdLuxExtractor:
                return UsdLuxExtractor.extract_light(prim, time_code)
            else:
                return self._extract_light_fallback(prim, time_code)
        return None
    
    def _extract_light_fallback(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Fallback light extraction if UsdLuxExtractor is not available"""
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
    
    def _extract_material(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract material data"""
        try:
            if not USD_AVAILABLE:
                return None
                
            material = UsdShade.Material(prim)
            material_data = {
                'name': prim.GetPath().pathString,
                'path': prim.GetPath(),
                'surface_output': None,
                'displacement_output': None,
                'volume_output': None,
                'inputs': {},
                'surface_shader': None,
            }
            
            # Get surface output
            surface_output = material.GetSurfaceOutput()
            if surface_output:
                material_data['surface_output'] = {
                    'path': surface_output.GetPath(),
                    'type': str(surface_output.GetTypeName()),
                }
                # Get connected source
                source = surface_output.GetConnectedSource()
                if source:
                    material_data['surface_shader'] = {
                        'path': source[0].GetPath().pathString,
                        'output_name': source[1],
                    }
            
            # Get displacement output
            displacement_output = material.GetDisplacementOutput()
            if displacement_output:
                material_data['displacement_output'] = {
                    'path': displacement_output.GetPath(),
                    'type': str(displacement_output.GetTypeName()),
                }
            
            # Get volume output
            volume_output = material.GetVolumeOutput()
            if volume_output:
                material_data['volume_output'] = {
                    'path': volume_output.GetPath(),
                    'type': str(volume_output.GetTypeName()),
                }
            
            # Extract material inputs
            for input_attr in material.GetInputs():
                input_name = input_attr.GetBaseName()
                input_value = input_attr.Get(time_code)
                material_data['inputs'][input_name] = {
                    'value': input_value,
                    'type': str(input_attr.GetTypeName()),
                }
            
            # Get material binding info
            binding_api = UsdShade.MaterialBindingAPI(prim)
            if binding_api:
                # Get direct binding
                direct_binding = binding_api.GetDirectBinding()
                if direct_binding:
                    material_data['binding'] = {
                        'material': direct_binding.GetMaterial().GetPath().pathString if direct_binding.GetMaterial() else None,
                        'binding_strength': str(direct_binding.GetBindingStrength()),
                    }
            
            return material_data
        except Exception as e:
            print(f"Error extracting material {prim.GetPath()}: {e}")
            return None
    
    def _extract_collection(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract collection data"""
        try:
            if not USD_AVAILABLE:
                return None
                
            collection_apis = UsdCollectionAPI.GetAllCollectionAPIs(prim)
            if not collection_apis:
                return None
            
            collections = []
            for collection_api in collection_apis:
                collection = collection_api.GetCollection()
                collection_data = {
                    'name': collection.GetName(),
                    'prim_path': prim.GetPath().pathString,
                    'expansion_rule': str(collection.GetExpansionRule()),
                    'includes_paths': [str(p) for p in collection.GetIncludesRel().GetTargets()],
                    'excludes_paths': [str(p) for p in collection.GetExcludesRel().GetTargets()],
                }
                
                # Check if it's a relationship-mode collection
                if collection_api.GetCollectionName() == collection.GetName():
                    collection_data['mode'] = 'relationship'
                else:
                    # Pattern-based collection
                    collection_data['mode'] = 'pattern'
                    # Try to get pattern expression
                    try:
                        pattern_attr = prim.GetAttribute(f"collection:{collection.GetName()}:includeRoot")
                        if pattern_attr:
                            collection_data['pattern_expression'] = pattern_attr.Get(time_code)
                    except:
                        pass
                
                collections.append(collection_data)
            
            return {
                'prim_path': prim.GetPath().pathString,
                'collections': collections,
            } if collections else None
        except Exception as e:
            print(f"Error extracting collection {prim.GetPath()}: {e}")
            return None
    
    def _extract_variants(self, prim: Usd.Prim) -> Optional[Dict]:
        """Extract variant sets and selections"""
        try:
            if not USD_AVAILABLE:
                return None
                
            variant_sets = prim.GetVariantSets()
            variant_set_names = variant_sets.GetNames()
            
            if not variant_set_names:
                return None
            
            variants_data = {
                'prim_path': prim.GetPath().pathString,
                'variant_sets': {},
            }
            
            for variant_set_name in variant_set_names:
                variant_set = variant_sets.GetVariantSet(variant_set_name)
                current_selection = variant_set.GetVariantSelection()
                available_variants = variant_set.GetVariantNames()
                
                variants_data['variant_sets'][variant_set_name] = {
                    'current_selection': current_selection,
                    'available_variants': available_variants,
                }
            
            return variants_data
        except Exception as e:
            print(f"Error extracting variants {prim.GetPath()}: {e}")
            return None
    
    def _extract_primvars(self, prim: Usd.Prim, time_code: float) -> Optional[List[Dict]]:
        """Extract primvars from a prim"""
        try:
            if not USD_AVAILABLE:
                return None
                
            primvars_api = UsdGeom.PrimvarsAPI(prim)
            primvars = primvars_api.GetPrimvars()
            
            if not primvars:
                return None
            
            primvar_list = []
            for primvar in primvars:
                primvar_name = primvar.GetPrimvarName()
                interpolation = primvar.GetInterpolation()
                element_size = primvar.GetElementSize()
                
                primvar_data = {
                    'name': primvar_name,
                    'type': str(primvar.GetTypeName()),
                    'interpolation': str(interpolation),
                    'element_size': element_size,
                    'is_indexed': primvar.IsIndexed(),
                }
                
                # Get values
                if primvar.IsIndexed():
                    primvar_data['values'] = primvar.Get(time_code)
                    primvar_data['indices'] = primvar.GetIndices(time_code)
                else:
                    primvar_data['values'] = primvar.Get(time_code)
                
                primvar_list.append(primvar_data)
            
            return primvar_list if primvar_list else None
        except Exception as e:
            print(f"Error extracting primvars {prim.GetPath()}: {e}")
            return None
    
    def _extract_render_settings(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract render settings"""
        try:
            if not USD_AVAILABLE:
                return None
                
            render_settings = UsdRender.RenderSettings(prim)
            render_data = {
                'name': prim.GetPath().pathString,
                'resolution': None,
                'pixel_aspect_ratio': None,
                'aspect_ratio_conform_policy': None,
                'data_windowNDC': None,
                'disable_motion_blur': None,
                'camera': None,
                'included_purposes': [],
                'material_binding_purposes': [],
                'rendering_color_space': None,
                'products': [],
            }
            
            # Get resolution
            if render_settings.GetResolutionAttr():
                render_data['resolution'] = render_settings.GetResolutionAttr().Get(time_code)
            
            # Get pixel aspect ratio
            if render_settings.GetPixelAspectRatioAttr():
                render_data['pixel_aspect_ratio'] = render_settings.GetPixelAspectRatioAttr().Get(time_code)
            
            # Get camera
            if render_settings.GetCameraRel():
                camera_targets = render_settings.GetCameraRel().GetTargets()
                if camera_targets:
                    render_data['camera'] = str(camera_targets[0])
            
            # Get products
            if render_settings.GetProductsRel():
                product_targets = render_settings.GetProductsRel().GetTargets()
                render_data['products'] = [str(p) for p in product_targets]
            
            return render_data
        except Exception as e:
            print(f"Error extracting render settings {prim.GetPath()}: {e}")
            return None
    
    def _extract_skeleton(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract skeleton data"""
        try:
            if not USD_AVAILABLE:
                return None
                
            skel_root = UsdSkel.Root(prim)
            skeleton_data = {
                'name': prim.GetPath().pathString,
                'skeletons': [],
            }
            
            # Get skeleton bindings
            if skel_root.GetSkeletonRel():
                skeleton_targets = skel_root.GetSkeletonRel().GetTargets()
                for skeleton_path in skeleton_targets:
                    skeleton_prim = self.stage.GetPrimAtPath(skeleton_path)
                    if skeleton_prim and skeleton_prim.IsA(UsdSkel.Skeleton):
                        skeleton = UsdSkel.Skeleton(skeleton_prim)
                        joints = skeleton.GetJointsAttr().Get(time_code) if skeleton.GetJointsAttr() else []
                        bind_transforms = skeleton.GetBindTransformsAttr().Get(time_code) if skeleton.GetBindTransformsAttr() else []
                        
                        skeleton_data['skeletons'].append({
                            'path': str(skeleton_path),
                            'joints': joints,
                            'bind_transforms': bind_transforms,
                        })
            
            return skeleton_data if skeleton_data['skeletons'] else None
        except Exception as e:
            print(f"Error extracting skeleton {prim.GetPath()}: {e}")
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
            
        info = {
            'path': self.stage.GetRootLayer().identifier,
            'start_time': self.time_range[0],
            'end_time': self.time_range[1],
            'fps': self.fps,
            'up_axis': UsdGeom.GetStageUpAxis(self.stage),
            'meters_per_unit': UsdGeom.GetStageMetersPerUnit(self.stage),
        }
        
        # Add color space info if available
        if USD_AVAILABLE:
            try:
                from .color_space import ColorSpaceManager
                default_color_space = ColorSpaceManager.get_default_color_space(self.stage)
                if default_color_space:
                    info['default_color_space'] = default_color_space
            except:
                pass
        
        return info


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
        self.payload_manager = None
        
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
        
        view_menu.addSeparator()
        
        # Payload management
        load_payloads_action = QAction("&Load All Payloads", self)
        load_payloads_action.triggered.connect(self.load_all_payloads)
        view_menu.addAction(load_payloads_action)
        
        unload_payloads_action = QAction("&Unload All Payloads", self)
        unload_payloads_action.triggered.connect(self.unload_all_payloads)
        view_menu.addAction(unload_payloads_action)
        
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
        self.hierarchy_tree.itemDoubleClicked.connect(self.on_hierarchy_item_double_clicked)
        dock.setWidget(self.hierarchy_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        
    def create_info_dock(self):
        """Create stage info dock with enhanced information"""
        dock = QDockWidget("Stage Info", self)
        info_widget = QWidget()
        layout = QVBoxLayout()
        
        # Basic stage info
        basic_group = QGroupBox("Stage Information")
        basic_layout = QFormLayout()
        self.info_labels = {}
        for key in ['path', 'start_time', 'end_time', 'fps', 'up_axis', 'meters_per_unit', 'default_color_space']:
            label = QLabel("-")
            self.info_labels[key] = label
            basic_layout.addRow(key.replace('_', ' ').title() + ":", label)
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout()
        self.stats_labels = {}
        for key in ['meshes', 'cameras', 'lights', 'materials', 'collections', 'variants']:
            label = QLabel("0")
            self.stats_labels[key] = label
            stats_layout.addRow(key.replace('_', ' ').title() + ":", label)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Validation button
        validate_btn = QPushButton("Validate USD")
        validate_btn.clicked.connect(self.validate_stage)
        layout.addWidget(validate_btn)
        
        layout.addStretch()
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
            
            # Initialize payload manager
            if USD_AVAILABLE:
                from .payloads import PayloadManager
                self.payload_manager = PayloadManager(self.stage_manager.stage)
            
            # Update UI
            info = self.stage_manager.get_stage_info()
            for key, label in self.info_labels.items():
                if key in info:
                    label.setText(str(info[key]))
            
            # Update statistics
            geometry_data = self.stage_manager.get_geometry_data(self.stage_manager.current_time)
            if hasattr(self, 'stats_labels'):
                self.stats_labels['meshes'].setText(str(len(geometry_data.get('meshes', []))))
                self.stats_labels['cameras'].setText(str(len(geometry_data.get('cameras', []))))
                self.stats_labels['lights'].setText(str(len(geometry_data.get('lights', []))))
                self.stats_labels['materials'].setText(str(len(geometry_data.get('materials', []))))
                self.stats_labels['collections'].setText(str(len(geometry_data.get('collections', []))))
                self.stats_labels['variants'].setText(str(len(geometry_data.get('variants', []))))
            
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
        """Update scene hierarchy tree with enhanced features"""
        self.hierarchy_tree.clear()
        
        if not self.stage_manager.stage:
            return
        
        # Get geometry data to access variants, collections, materials
        geometry_data = self.stage_manager.get_geometry_data(self.stage_manager.current_time)
        
        # Create lookup dictionaries
        variants_dict = {v['prim_path']: v for v in geometry_data.get('variants', [])}
        collections_dict = {c['prim_path']: c for c in geometry_data.get('collections', [])}
        materials_dict = {m['name']: m for m in geometry_data.get('materials', [])}
            
        def add_prim_to_tree(prim: Usd.Prim, parent_item: QTreeWidgetItem = None):
            """Recursively add prims to tree with enhanced info"""
            prim_name = prim.GetName() or prim.GetPath().pathString
            
            # Build display name with type indicators
            display_name = prim_name
            type_indicators = []
            
            # Add type indicators
            if prim.IsA(UsdGeom.Mesh):
                type_indicators.append("📦")
            elif prim.IsA(UsdGeom.Camera):
                type_indicators.append("📷")
            elif USD_AVAILABLE and prim.IsA(UsdLux.Light):
                type_indicators.append("💡")
            elif USD_AVAILABLE and prim.IsA(UsdShade.Material):
                type_indicators.append("🎨")
            elif USD_AVAILABLE and prim.IsA(UsdSkel.Root):
                type_indicators.append("🦴")
            elif USD_AVAILABLE and prim.IsA(UsdRender.RenderSettings):
                type_indicators.append("🎬")
            
            # Add variant indicator
            prim_path_str = prim.GetPath().pathString
            if prim_path_str in variants_dict:
                variant_info = variants_dict[prim_path_str]
                if variant_info['variant_sets']:
                    type_indicators.append("🔀")
            
            # Add collection indicator
            if prim_path_str in collections_dict:
                type_indicators.append("📋")
            
            # Add payload indicator
            if prim.HasPayload():
                type_indicators.append("📥")
            
            if type_indicators:
                display_name = f"{' '.join(type_indicators)} {prim_name}"
            
            item = QTreeWidgetItem([display_name])
            item.setData(0, Qt.ItemDataRole.UserRole, prim.GetPath().pathString)
            
            # Store prim info in item
            item.setToolTip(0, f"Type: {prim.GetTypeName()}\nPath: {prim.GetPath()}")
            
            if parent_item:
                parent_item.addChild(item)
            else:
                self.hierarchy_tree.addTopLevelItem(item)
            
            # Add variant sets as children if present
            if prim_path_str in variants_dict:
                variant_info = variants_dict[prim_path_str]
                for variant_set_name, variant_data in variant_info['variant_sets'].items():
                    variant_item = QTreeWidgetItem([f"🔀 {variant_set_name}: {variant_data['current_selection']}"])
                    variant_item.setData(0, Qt.ItemDataRole.UserRole, f"{prim_path_str}::{variant_set_name}")
                    item.addChild(variant_item)
            
            # Add collections as children if present
            if prim_path_str in collections_dict:
                collection_info = collections_dict[prim_path_str]
                for collection in collection_info['collections']:
                    collection_item = QTreeWidgetItem([f"📋 {collection['name']} ({collection['mode']})"])
                    collection_item.setData(0, Qt.ItemDataRole.UserRole, f"{prim_path_str}::collection::{collection['name']}")
                    item.addChild(collection_item)
            
            # Recursively add children
            for child in prim.GetChildren():
                add_prim_to_tree(child, item)
                
        root = self.stage_manager.stage.GetPseudoRoot()
        for child in root.GetChildren():
            add_prim_to_tree(child)
            
        self.hierarchy_tree.expandAll()
        
    def import_convert_file(self):
        """Import and convert 3D file to USD"""
        from converter import ConverterDialog
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
    
    def validate_stage(self):
        """Validate the current USD stage"""
        if not USD_AVAILABLE:
            QMessageBox.warning(self, "USD Not Available", 
                              "USD Python bindings not installed.")
            return
        
        try:
            from .validation import USDValidator
            
            validator = USDValidator()
            result = validator.validate_stage(self.stage_manager.stage)
            
            # Show results
            message = "USD Validation Results\n\n"
            if result['passed']:
                message += "✅ Validation PASSED\n\n"
            else:
                message += "❌ Validation FAILED\n\n"
            
            if result['errors']:
                message += f"Errors ({len(result['errors'])}):\n"
                for error in result['errors'][:10]:  # Show first 10
                    message += f"  • {error.get('message', str(error))}\n"
                if len(result['errors']) > 10:
                    message += f"  ... and {len(result['errors']) - 10} more\n"
                message += "\n"
            
            if result['warnings']:
                message += f"Warnings ({len(result['warnings'])}):\n"
                for warning in result['warnings'][:10]:  # Show first 10
                    message += f"  • {warning.get('message', str(warning))}\n"
                if len(result['warnings']) > 10:
                    message += f"  ... and {len(result['warnings']) - 10} more\n"
                message += "\n"
            
            if result['info']:
                message += f"Info ({len(result['info'])}):\n"
                for info in result['info'][:5]:  # Show first 5
                    message += f"  • {info.get('message', str(info))}\n"
            
            QMessageBox.information(self, "USD Validation", message)
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Error during validation:\n{e}")
    
    def load_all_payloads(self):
        """Load all payloads in the stage"""
        if not self.payload_manager:
            QMessageBox.warning(self, "Payload Manager", "Payload manager not initialized.")
            return
        
        count = self.payload_manager.load_all_payloads()
        self.statusBar().showMessage(f"Loaded {count} payload(s)", 3000)
        self.update_hierarchy()  # Refresh hierarchy to show loaded state
    
    def unload_all_payloads(self):
        """Unload all payloads in the stage"""
        if not self.payload_manager:
            QMessageBox.warning(self, "Payload Manager", "Payload manager not initialized.")
            return
        
        count = self.payload_manager.unload_all_payloads()
        self.statusBar().showMessage(f"Unloaded {count} payload(s)", 3000)
        self.update_hierarchy()  # Refresh hierarchy to show unloaded state
    
    def on_hierarchy_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click on hierarchy item for variant selection"""
        prim_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not prim_path:
            return
        
        # Check if it's a variant set item
        if "::" in prim_path and not prim_path.startswith("/"):
            # This is a variant set
            parts = prim_path.split("::")
            if len(parts) == 2:
                prim_path_str, variant_set_name = parts
                prim = self.stage_manager.stage.GetPrimAtPath(prim_path_str)
                if prim:
                    self.show_variant_selector(prim, variant_set_name)
    
    def show_variant_selector(self, prim: Usd.Prim, variant_set_name: str):
        """Show dialog to select variant"""
        if not USD_AVAILABLE:
            return
        
        try:
            from .variants import VariantManager
            
            variant_sets = prim.GetVariantSets()
            variant_set = variant_sets.GetVariantSet(variant_set_name)
            available_variants = variant_set.GetVariantNames()
            current_selection = variant_set.GetVariantSelection()
            
            # Create simple selection dialog
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Select Variant: {variant_set_name}")
            layout = QVBoxLayout()
            
            label = QLabel(f"Select variant for {variant_set_name}:")
            layout.addWidget(label)
            
            list_widget = QListWidget()
            for variant in available_variants:
                list_widget.addItem(variant)
                if variant == current_selection:
                    list_widget.setCurrentItem(list_widget.item(list_widget.count() - 1))
            layout.addWidget(list_widget)
            
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Cancel")
            
            def apply_variant():
                selected = list_widget.currentItem()
                if selected:
                    variant_name = selected.text()
                    VariantManager.set_variant_selection(prim, variant_set_name, variant_name)
                    self.update_hierarchy()
                    self.viewport.update_geometry(self.stage_manager.current_time)
                dialog.accept()
            
            ok_button.clicked.connect(apply_variant)
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Variant Selection Error", f"Error selecting variant:\n{e}")


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