#!/usr/bin/env python3
"""
USD Viewer and Converter Application
Professional USD file viewer with playback controls and 3D format conversion
Designed for VFX pipeline integration on RHEL9/AlmaLinux
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar, QFileDialog, QSlider,
    QPushButton, QLabel, QDockWidget, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QProgressDialog, QComboBox, QSpinBox, QGroupBox,
    QFormLayout, QSplitter, QInputDialog, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QThread, QUrl
from PySide6.QtGui import QAction, QKeySequence, QIcon, QPalette, QColor, QSurfaceFormat, QDragEnterEvent, QDropEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

try:
    from pxr import Usd, UsdGeom, Gf, Sdf, UsdShade, Kind, UsdLux, UsdRender, UsdSkel, UsdUtils
    USD_AVAILABLE = True
    
    # Check if UsdLux.LightAPI exists (it's the correct way to check for lights)
    try:
        _ = UsdLux.LightAPI
        USDLUX_LIGHTAPI_AVAILABLE = True
    except AttributeError:
        USDLUX_LIGHTAPI_AVAILABLE = False
    
    # Check if UsdLux.ColorSpaceAPI exists
    try:
        _ = UsdLux.ColorSpaceAPI
        USDLUX_COLORSPACEAPI_AVAILABLE = True
    except AttributeError:
        USDLUX_COLORSPACEAPI_AVAILABLE = False
    
    # Check if UsdRender.RenderSettings exists
    try:
        _ = UsdRender.RenderSettings
        USDRENDER_RENDERSETTINGS_AVAILABLE = True
    except AttributeError:
        USDRENDER_RENDERSETTINGS_AVAILABLE = False
    
    # Try to import UsdCollectionAPI separately as it may not be available in all USD versions
    try:
        from pxr import UsdCollectionAPI
        USDCOLLECTIONAPI_AVAILABLE = True
    except ImportError:
        # UsdCollectionAPI not available - create fallback class
        USDCOLLECTIONAPI_AVAILABLE = False
        class UsdCollectionAPI:
            @staticmethod
            def GetAllCollectionAPIs(prim):
                return []
            @staticmethod
            def ApplyCollection(prim, name, **kwargs):
                return None
except ImportError:
    USD_AVAILABLE = False
    print("Warning: USD Python bindings not found. Install with: pip install usd-core")
    
    # Create dummy classes for type hints
    USDLUX_LIGHTAPI_AVAILABLE = False
    USDLUX_COLORSPACEAPI_AVAILABLE = False
    USDCOLLECTIONAPI_AVAILABLE = False
    USDRENDER_RENDERSETTINGS_AVAILABLE = False
    class UsdLux:
        pass
    class UsdCollectionAPI:
        @staticmethod
        def GetAllCollectionAPIs(prim):
            return []
        @staticmethod
        def ApplyCollection(prim, name, **kwargs):
            return None
    class UsdRender:
        pass
    class UsdSkel:
        pass
    class UsdUtils:
        pass

# Import USD version detection
try:
    from ..utils.usd_version import (
        USD_VERSION_STRING, USD_VERSION_TUPLE, USD_FEATURES,
        USD_VERSION_AT_LEAST, check_feature
    )
except ImportError:
    USD_VERSION_STRING = None
    USD_VERSION_TUPLE = (0, 0, 0)
    USD_FEATURES = {}
    def USD_VERSION_AT_LEAST(major, minor=0, patch=0):
        return False
    def check_feature(feature_name):
        return False

import numpy as np

# Import from reorganized structure
try:
    from ..utils.usd_lux_support import UsdLuxExtractor
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


def _is_light_prim(prim) -> bool:
    """Check if a prim is a light (safe for all USD versions)"""
    if not USD_AVAILABLE or not prim:
        return False
    
    try:
        # Try LightAPI first (most common)
        if USDLUX_LIGHTAPI_AVAILABLE:
            if prim.IsA(UsdLux.LightAPI):
                return True
        
        # Check for specific light types
        light_types = [
            'DistantLight', 'SphereLight', 'RectLight', 'DiskLight',
            'CylinderLight', 'DomeLight', 'PortalLight', 'GeometryLight'
        ]
        for light_type in light_types:
            try:
                light_class = getattr(UsdLux, light_type, None)
                if light_class and prim.IsA(light_class):
                    return True
            except (AttributeError, TypeError):
                continue
        
        return False
    except Exception:
        return False


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
            # Check visibility - skip invisible prims
            if USD_AVAILABLE:
                imageable = UsdGeom.Imageable(prim)
                if imageable:
                    visibility = imageable.ComputeVisibility(time_code)
                    if visibility == UsdGeom.Tokens.invisible:
                        continue  # Skip invisible prims
            
            if prim.IsA(UsdGeom.Mesh):
                mesh_data = self._extract_mesh(prim, time_code)
                if mesh_data:
                    geometry_data['meshes'].append(mesh_data)
                    
            elif prim.IsA(UsdGeom.Camera):
                cam_data = self._extract_camera(prim, time_code)
                if cam_data:
                    geometry_data['cameras'].append(cam_data)
                    
            elif _is_light_prim(prim):
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
                    
            elif USD_AVAILABLE and USDCOLLECTIONAPI_AVAILABLE and prim.HasAPI(UsdCollectionAPI):
                collection_data = self._extract_collection(prim, time_code)
                if collection_data:
                    geometry_data['collections'].append(collection_data)
                    
            elif USD_AVAILABLE and prim.GetVariantSets().GetNames():
                variant_data = self._extract_variants(prim)
                if variant_data:
                    geometry_data['variants'].append(variant_data)
                    
            elif USD_AVAILABLE and USDRENDER_RENDERSETTINGS_AVAILABLE and prim.IsA(UsdRender.RenderSettings):
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
        if _is_light_prim(prim):
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
            if not USD_AVAILABLE or not USDCOLLECTIONAPI_AVAILABLE:
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
            if not USD_AVAILABLE or not USDRENDER_RENDERSETTINGS_AVAILABLE:
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
                from ..utils.color_space import ColorSpaceManager
                default_color_space = ColorSpaceManager.get_default_color_space(self.stage)
                if default_color_space:
                    info['default_color_space'] = default_color_space
            except:
                pass
        
        return info


class ViewportWidget(QOpenGLWidget):
    """OpenGL viewport for USD rendering"""
    
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
        self.settings = ViewerSettings()
        
        # Camera controls
        self.camera_distance = 10.0
        self.camera_rotation_x = 30.0
        self.camera_rotation_y = 45.0
        self.camera_target = np.array([0.0, 0.0, 0.0])
        
        # View mode (Perspective, Top, Front, Left, Back, Right)
        self.view_mode = "Perspective"
        self.current_usd_camera = None  # USD camera prim if using USD camera
        
        # Store initial camera state (home position)
        self.home_camera_distance = 10.0
        self.home_camera_rotation_x = 30.0
        self.home_camera_rotation_y = 45.0
        self.home_camera_target = np.array([0.0, 0.0, 0.0])
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.is_rotating = False
        self.is_panning = False
        self.is_gizmo_dragging = False
        
        # Gizmo
        from ..rendering.gizmo import TransformGizmo, GizmoMode, GizmoAxis
        self.gizmo = TransformGizmo()
        self.gizmo_mode = GizmoMode.TRANSLATE
        self.GizmoAxis = GizmoAxis  # Store for use in drawing methods
        
        # Enable keyboard focus for shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def set_stage_manager(self, manager: USDStageManager):
        """Set the USD stage manager"""
        self.stage_manager = manager
        
    def update_geometry(self, time_code: float):
        """Update geometry for current time"""
        if self.stage_manager:
            self.geometry_data = self.stage_manager.get_geometry_data(time_code)
            print(f"DEBUG: update_geometry called. Meshes: {len(self.geometry_data.get('meshes', []))}, "
                  f"Cameras: {len(self.geometry_data.get('cameras', []))}, "
                  f"Lights: {len(self.geometry_data.get('lights', []))}")
            
            # Auto-frame on first load
            if self.settings.auto_frame and 'bounds' in self.geometry_data and self.geometry_data['bounds']:
                bounds = self.geometry_data['bounds']
                print(f"DEBUG: Auto-framing to bounds: center={bounds.get('center')}, size={bounds.get('size')}")
                self.frame_bounds(self.geometry_data['bounds'])
                self.settings.auto_frame = False
            else:
                print(f"DEBUG: Not auto-framing. auto_frame={self.settings.auto_frame}, "
                      f"has_bounds={'bounds' in self.geometry_data}")
                
            self.update()
            print(f"DEBUG: Viewport update() called")
    
    def frame_bounds(self, bounds: Dict):
        """Frame camera to fit bounds"""
        if not bounds:
            return
        
        center = bounds.get('center', np.array([0.0, 0.0, 0.0]))
        size_array = bounds.get('size', np.array([1.0, 1.0, 1.0]))
        
        # Ensure center and size are numpy arrays
        if not isinstance(center, np.ndarray):
            center = np.array(center)
        if not isinstance(size_array, np.ndarray):
            size_array = np.array(size_array)
            
        self.camera_target = center
        size = np.max(size_array)
        # Calculate distance to fit the entire bounding box
        # Use FOV to calculate appropriate distance
        fov_rad = np.radians(self.settings.camera_fov)
        distance = size / (2.0 * np.tan(fov_rad / 2.0)) * 1.5  # Add 50% padding
        self.camera_distance = max(distance, 0.1)  # Ensure minimum distance
        
        print(f"DEBUG: Framed camera. Target: {self.camera_target}, Distance: {self.camera_distance}, Size: {size}")
        self.update()
    
    def frame_selected(self):
        """Frame selected prim or all geometry (F key)"""
        if not self.geometry_data:
            return
        
        # Frame all geometry bounds
        if 'bounds' in self.geometry_data and self.geometry_data['bounds']:
            self.frame_bounds(self.geometry_data['bounds'])
        else:
            # Fallback: frame to origin
            self.camera_target = np.array([0.0, 0.0, 0.0])
            self.camera_distance = 10.0
            self.update()
    
    def go_home(self):
        """Reset camera to initial/home position (H key)"""
        self.camera_distance = self.home_camera_distance
        self.camera_rotation_x = self.home_camera_rotation_x
        self.camera_rotation_y = self.home_camera_rotation_y
        self.camera_target = self.home_camera_target.copy()
        self.update()
        
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
        # Record frame for FPS calculation
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.record_frame()
        
        # Clear buffers
        bg = self.settings.background_color
        glClearColor(*bg)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width() / max(self.height(), 1)
        
        # Use orthographic for ortho views, perspective for perspective view
        view_mode = getattr(self, 'view_mode', 'Perspective')
        if view_mode == "Perspective":
            gluPerspective(self.settings.camera_fov, aspect, 
                          self.settings.near_clip, self.settings.far_clip)
        else:
            # Orthographic projection for ortho views
            ortho_size = self.camera_distance * 0.5
            glOrtho(-ortho_size * aspect, ortho_size * aspect,
                   -ortho_size, ortho_size,
                   self.settings.near_clip, self.settings.far_clip)
        
        # Set up camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Calculate camera position and orientation based on view mode
        if view_mode == "Perspective":
            # Free camera (perspective)
            cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
            cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            camera_pos = self.camera_target + np.array([cam_x, cam_y, cam_z])
            up_vector = np.array([0, 1, 0])
        elif view_mode == "Top":
            # Top view: camera above, looking down
            camera_pos = self.camera_target + np.array([0, self.camera_distance, 0])
            up_vector = np.array([0, 0, -1])  # Negative Z is "up" in top view
        elif view_mode == "Front":
            # Front view: camera in front, looking back
            camera_pos = self.camera_target + np.array([0, 0, self.camera_distance])
            up_vector = np.array([0, 1, 0])
        elif view_mode == "Left":
            # Left view: camera on left, looking right
            camera_pos = self.camera_target + np.array([-self.camera_distance, 0, 0])
            up_vector = np.array([0, 1, 0])
        elif view_mode == "Back":
            # Back view: camera behind, looking forward
            camera_pos = self.camera_target + np.array([0, 0, -self.camera_distance])
            up_vector = np.array([0, 1, 0])
        elif view_mode == "Right":
            # Right view: camera on right, looking left
            camera_pos = self.camera_target + np.array([self.camera_distance, 0, 0])
            up_vector = np.array([0, 1, 0])
        else:
            # Default to perspective
            cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
            cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
            camera_pos = self.camera_target + np.array([cam_x, cam_y, cam_z])
            up_vector = np.array([0, 1, 0])
        
        gluLookAt(
            camera_pos[0], camera_pos[1], camera_pos[2],
            self.camera_target[0], self.camera_target[1], self.camera_target[2],
            up_vector[0], up_vector[1], up_vector[2]
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
        """Draw 3D coordinate axis that rotates with the view (like Blender/Maya)"""
        glDisable(GL_LIGHTING)
        glLineWidth(3.0)
        
        # Position in bottom-left corner of viewport (in 3D space, not 2D overlay)
        # Calculate screen-space position
        axis_size = 1.0  # Size in world units
        padding = 0.5  # Offset from corner
        
        # Get current viewport dimensions for positioning
        # We'll position it in world space at the bottom-left of the visible area
        # Calculate a position that's always visible in the bottom-left
        
        # Get camera position and direction
        cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
        cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        camera_pos = self.camera_target + np.array([cam_x, cam_y, cam_z])
        
        # Calculate axis origin in world space (bottom-left of view)
        # Use camera target as reference, offset to bottom-left
        view_right = np.array([1, 0, 0])  # Will be transformed by view
        view_up = np.array([0, 1, 0])
        view_forward = np.array([0, 0, 1])
        
        # Position axis at camera target with offset
        axis_origin = self.camera_target.copy()
        
        # Draw axis lines in 3D space (will rotate with view)
        glBegin(GL_LINES)
        
        # X axis - Red (right)
        glColor3f(1, 0, 0)
        glVertex3f(axis_origin[0], axis_origin[1], axis_origin[2])
        glVertex3f(axis_origin[0] + axis_size, axis_origin[1], axis_origin[2])
        
        # Y axis - Green (up)
        glColor3f(0, 1, 0)
        glVertex3f(axis_origin[0], axis_origin[1], axis_origin[2])
        glVertex3f(axis_origin[0], axis_origin[1] + axis_size, axis_origin[2])
        
        # Z axis - Blue (forward)
        glColor3f(0, 0, 1)
        glVertex3f(axis_origin[0], axis_origin[1], axis_origin[2])
        glVertex3f(axis_origin[0], axis_origin[1], axis_origin[2] + axis_size)
        
        glEnd()
        
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
        
    def draw_geometry(self):
        """Draw USD geometry"""
        if not self.geometry_data or 'meshes' not in self.geometry_data:
            # Debug: print if geometry data is missing
            if not self.geometry_data:
                print("DEBUG: No geometry_data in viewport")
            elif 'meshes' not in self.geometry_data:
                print(f"DEBUG: geometry_data missing 'meshes' key. Keys: {list(self.geometry_data.keys())}")
            return
        
        if not self.geometry_data['meshes']:
            # No meshes to draw
            print(f"DEBUG: geometry_data['meshes'] is empty. Total meshes: {len(self.geometry_data.get('meshes', []))}")
            return
        
        # Don't print every frame - too verbose
        # print(f"DEBUG: Drawing {len(self.geometry_data['meshes'])} meshes")
        
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_NORMALIZE)  # Normalize normals for proper lighting
        
        # Brighter material properties for better visibility
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])  # Brighter ambient
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.9, 0.9, 0.9, 1.0])  # Brighter diffuse
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])  # Brighter specular
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64.0)
        
        # Enable color material for better visibility
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glColor3f(0.8, 0.8, 0.8)  # Default gray color
        
        for mesh in self.geometry_data['meshes']:
            if mesh and 'points' in mesh and len(mesh['points']) > 0:
                self.draw_mesh(mesh)
        
        glDisable(GL_COLOR_MATERIAL)
    
    def draw_mesh(self, mesh: Dict):
        """Draw a single mesh"""
        points = mesh.get('points')
        fvc = mesh.get('face_vertex_counts')
        fvi = mesh.get('face_vertex_indices')
        normals = mesh.get('normals')
        
        # Check if arrays exist and have data (handle numpy arrays properly)
        if points is None or len(points) == 0:
            return
        if fvc is None or len(fvc) == 0:
            return
        if fvi is None or len(fvi) == 0:
            return
        
        # Apply transform
        glPushMatrix()
        if 'transform' in mesh and mesh['transform'] is not None:
            transform = mesh['transform'].T  # OpenGL uses column-major
            glMultMatrixf(transform.flatten())
        
        # Draw faces
        idx = 0
        for count in fvc:
            if count < 3:  # Skip invalid face counts
                idx += count
                continue
                
            if count == 3:
                glBegin(GL_TRIANGLES)
            elif count == 4:
                glBegin(GL_QUADS)
            else:
                glBegin(GL_POLYGON)
                
            for i in range(count):
                vert_idx = fvi[idx + i]
                
                # Bounds check
                if vert_idx >= len(points):
                    continue
                    
                # Normal
                if normals is not None and len(normals) > 0 and vert_idx < len(normals):
                    n = normals[vert_idx]
                    glNormal3f(float(n[0]), float(n[1]), float(n[2]))
                else:
                    # Calculate normal on the fly if missing
                    glNormal3f(0.0, 1.0, 0.0)  # Default up normal
                    
                # Vertex
                v = points[vert_idx]
                glVertex3f(float(v[0]), float(v[1]), float(v[2]))
                
            glEnd()
            idx += count
            
        glPopMatrix()
    
    def draw_gizmo(self):
        """Draw transform gizmo for selected prim"""
        # Get selected prim from viewer window
        if not hasattr(self, 'parent') or not self.parent():
            return
        
        viewer_window = self.parent()
        while viewer_window and not isinstance(viewer_window, USDViewerWindow):
            viewer_window = viewer_window.parent()
        
        if not viewer_window or not hasattr(viewer_window, 'prim_selection_manager'):
            return
        
        selection_manager = viewer_window.prim_selection_manager
        if not selection_manager:
            return
        
        selected_prims = selection_manager.get_selected_prims()
        if not selected_prims:
            return
        
        # Use first selected prim
        selected_prim = selected_prims[0]
        
        # Get prim transform
        if not USD_AVAILABLE:
            return
        
        try:
            from pxr import UsdGeom
            if selected_prim.IsA(UsdGeom.Xformable):
                xformable = UsdGeom.Xformable(selected_prim)
                transform = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
                position = transform.ExtractTranslation()
                
                # Set gizmo position and size
                self.gizmo.set_position(np.array([position[0], position[1], position[2]]))
                self.gizmo.set_size(self.camera_distance * 0.1)  # Scale with camera distance
                self.gizmo.set_mode(self.gizmo_mode)
                
                # Draw gizmo using direct OpenGL calls
                self._draw_gizmo_opengl()
        except Exception as e:
            print(f"Error drawing gizmo: {e}")
    
    def _draw_gizmo_opengl(self):
        """Draw gizmo using OpenGL (simplified direct implementation)"""
        if self.gizmo_mode.value == "translate":
            self._draw_translate_gizmo()
        elif self.gizmo_mode.value == "rotate":
            self._draw_rotate_gizmo()
        elif self.gizmo_mode.value == "scale":
            self._draw_scale_gizmo()
    
    def _draw_translate_gizmo(self):
        """Draw translation gizmo (arrows)"""
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        glPushMatrix()
        glTranslatef(self.gizmo.position[0], self.gizmo.position[1], self.gizmo.position[2])
        
        arrow_length = self.gizmo.size
        arrow_shaft = arrow_length * 0.7
        arrow_head = arrow_length * 0.3
        head_width = self.gizmo.size * 0.1
        
        # X axis (Red)
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.X else self.gizmo.colors[self.GizmoAxis.X]
        glColor3f(*color)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(arrow_shaft, 0, 0)
        glEnd()
        
        # Y axis (Green)
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.Y else self.gizmo.colors[self.GizmoAxis.Y]
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, arrow_shaft, 0)
        glEnd()
        
        # Z axis (Blue)
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.Z else self.gizmo.colors[self.GizmoAxis.Z]
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, arrow_shaft)
        glEnd()
        
        glLineWidth(1.0)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
    
    def _draw_rotate_gizmo(self):
        """Draw rotation gizmo (circles)"""
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        glPushMatrix()
        glTranslatef(self.gizmo.position[0], self.gizmo.position[1], self.gizmo.position[2])
        
        radius = self.gizmo.size
        segments = 64
        
        # X axis circle (Red) - in YZ plane
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.X else self.gizmo.colors[self.GizmoAxis.X]
        glColor3f(*color)
        glLineWidth(3.0)
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2.0 * np.pi * i / segments
            glVertex3f(0, radius * np.cos(angle), radius * np.sin(angle))
        glEnd()
        
        # Y axis circle (Green) - in XZ plane
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.Y else self.gizmo.colors[self.GizmoAxis.Y]
        glColor3f(*color)
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2.0 * np.pi * i / segments
            glVertex3f(radius * np.cos(angle), 0, radius * np.sin(angle))
        glEnd()
        
        # Z axis circle (Blue) - in XY plane
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.Z else self.gizmo.colors[self.GizmoAxis.Z]
        glColor3f(*color)
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2.0 * np.pi * i / segments
            glVertex3f(radius * np.cos(angle), radius * np.sin(angle), 0)
        glEnd()
        
        glLineWidth(1.0)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
    
    def _draw_scale_gizmo(self):
        """Draw scale gizmo (boxes)"""
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        glPushMatrix()
        glTranslatef(self.gizmo.position[0], self.gizmo.position[1], self.gizmo.position[2])
        
        box_size = self.gizmo.size * 0.15
        
        # X axis (Red)
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.X else self.gizmo.colors[self.GizmoAxis.X]
        glColor3f(*color)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(self.gizmo.size, 0, 0)
        glEnd()
        
        # Y axis (Green)
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.Y else self.gizmo.colors[self.GizmoAxis.Y]
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, self.gizmo.size, 0)
        glEnd()
        
        # Z axis (Blue)
        color = self.gizmo.highlight_color if self.gizmo.selected_axis == self.gizmo.hover_axis == self.GizmoAxis.Z else self.gizmo.colors[self.GizmoAxis.Z]
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, self.gizmo.size)
        glEnd()
        
        glLineWidth(1.0)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
    def mousePressEvent(self, event):
        """Handle mouse press"""
        self.last_mouse_pos = event.position()
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_rotating = True
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.is_gizmo_dragging:
            self.gizmo.end_drag()
            self.is_gizmo_dragging = False
        
        self.is_rotating = False
        self.is_panning = False
        
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        if not self.last_mouse_pos:
            return
            
        pos = event.position()
        mouse_pos = (pos.x(), pos.y())
        dx = pos.x() - self.last_mouse_pos.x()
        dy = pos.y() - self.last_mouse_pos.y()
        
        if self.is_gizmo_dragging:
            # Update gizmo drag
            camera_pos = self._get_camera_position()
            camera_target = self.camera_target
            view_direction = self._get_view_direction()
            
            # Get transform delta from gizmo
            transform_delta = self.gizmo.update_drag(
                mouse_pos, camera_pos, camera_target, view_direction,
                None, None, (self.width(), self.height())
            )
            
            if transform_delta is not None:
                # Apply transform to selected prim
                if hasattr(self, 'parent'):
                    viewer_window = self.parent()
                    while viewer_window and not isinstance(viewer_window, USDViewerWindow):
                        viewer_window = viewer_window.parent()
                    
                    if viewer_window and hasattr(viewer_window, 'prim_selection_manager'):
                        selection_manager = viewer_window.prim_selection_manager
                        if selection_manager:
                            selected_prims = selection_manager.get_selected_prims()
                            if selected_prims:
                                selected_prim = selected_prims[0]
                                
                                if self.gizmo_mode.value == "translate":
                                    # Apply translation
                                    current_pos = self.gizmo.position
                                    new_pos = current_pos + transform_delta
                                    selection_manager.translate_prim(
                                        selected_prim,
                                        Gf.Vec3d(new_pos[0], new_pos[1], new_pos[2])
                                    )
                                    self.gizmo.set_position(new_pos)
                                elif self.gizmo_mode.value == "scale":
                                    # Apply scale (would need current scale to multiply)
                                    pass  # TODO: Implement scale
                                
                                self.update()
            
        elif self.is_rotating:
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
    
    def _get_camera_position(self) -> np.ndarray:
        """Get current camera position"""
        cam_x = self.camera_distance * np.cos(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        cam_y = self.camera_distance * np.sin(np.radians(self.camera_rotation_x))
        cam_z = self.camera_distance * np.sin(np.radians(self.camera_rotation_y)) * np.cos(np.radians(self.camera_rotation_x))
        return self.camera_target + np.array([cam_x, cam_y, cam_z])
    
    def _get_view_direction(self) -> np.ndarray:
        """Get view direction vector"""
        camera_pos = self._get_camera_position()
        view_dir = self.camera_target - camera_pos
        return view_dir / np.linalg.norm(view_dir)
    
    def _world_to_screen(self, world_pos: np.ndarray, camera_pos: np.ndarray) -> Tuple[float, float]:
        """Convert world position to screen coordinates (simplified)"""
        # This is a simplified version - proper implementation would use projection matrix
        to_point = world_pos - camera_pos
        distance = np.linalg.norm(to_point)
        
        # Simple approximation
        screen_x = self.width() / 2
        screen_y = self.height() / 2
        
        return (screen_x, screen_y)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for viewport navigation"""
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
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        key = event.key()
        
        # F key: Frame selected/all
        if key == Qt.Key.Key_F:
            self.frame_selected()
            event.accept()
            return
        
        # H key: Go home (reset camera)
        elif key == Qt.Key.Key_H:
            self.go_home()
            event.accept()
            return
        
        # Let parent handle other keys
        super().keyPressEvent(event)


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
        self.use_hydra = False
        
        # Feature widgets
        self.layer_composition_widget = None
        self.animation_editor_widget = None
        self.material_editor_widget = None
        self.scene_search_widget = None
        self.camera_manager_widget = None
        self.light_manager_widget = None
        self.prim_properties_widget = None
        self.collection_editor_widget = None
        self.primvar_editor_widget = None
        self.render_settings_editor_widget = None
        self.stage_variables_widget = None
        self.multi_viewport_widget = None
        self.scene_comparison_widget = None
        self.openexec_widget = None
        self.annotations_widget = None
        self.aov_widget = None
        self.texture_preview_widget = None
        self.selection_sets_widget = None
        self.prim_selection_manager = None
        self.undo_redo_manager = None
        self.help_system = None
        self.viewport_overlay = None
        
        # Initialize managers
        from ..utils.help_system import HelpSystem
        from ..utils.recent_files import RecentFilesManager
        from ..utils.bookmarks import BookmarkManager
        from ..utils.theme_manager import ThemeManager
        from ..utils.cache_manager import CacheManager
        from ..utils.ocio_manager import OCIOManager
        from ..managers.selection_sets import SelectionSetManager
        from ..managers.lod_manager import LODManager
        from ..managers.instancing_manager import InstancingManager
        
        self.help_system = HelpSystem()
        self.recent_files_manager = RecentFilesManager()
        self.bookmark_manager = BookmarkManager()
        self.theme_manager = ThemeManager(self)
        self.cache_manager = CacheManager()
        self.selection_set_manager = SelectionSetManager()
        
        # Initialize OCIO manager for color-accurate asset review
        # Load OCIO config path from preferences
        from PySide6.QtCore import QSettings
        settings = QSettings("xStage", "xStage")
        ocio_config_path = settings.value("ocio/config_path", "", type=str) or None
        
        self.ocio_manager = OCIOManager(config_path=ocio_config_path)
        self.current_color_space = None
        self.display_color_space = None
        if self.ocio_manager.is_available():
            self.display_color_space = self.ocio_manager.get_display_color_space()
        
        # Initialize QuiltiX manager for MaterialX editing
        from ..managers.quiltix_manager import QuiltiXManager
        self.quiltix_manager = QuiltiXManager()
        
        # Initialize light linking manager
        from ..managers.light_linking_manager import LightLinkingManager
        self.light_linking_manager = None
        self.lod_manager = LODManager()
        self.instancing_manager = InstancingManager()
        
        # Apply theme
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        self.on_theme_changed(self.theme_manager.current_theme_name)
        
        self._add_tooltips()
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("xStage")
        self.setGeometry(100, 100, 1600, 900)
        
        # Enable drag and drop for USD files
        self.setAcceptDrops(True)
        
        # Create viewport container with header
        from PySide6.QtWidgets import QVBoxLayout, QWidget
        viewport_container = QWidget()
        viewport_layout = QVBoxLayout()
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        viewport_layout.setSpacing(0)
        
        # Create viewport header (Omniverse-style)
        from ..ui.widgets.viewport_header import ViewportHeader
        self.viewport_header = ViewportHeader()
        self.viewport_header.camera_changed.connect(self.on_viewport_camera_changed)
        self.viewport_header.view_changed.connect(self.on_viewport_view_changed)
        self.viewport_header.overlay_toggled.connect(self.on_viewport_overlay_toggled)
        viewport_layout.addWidget(self.viewport_header)
        
        # Create central widget with viewport
        # Try to use Hydra viewport if available, fallback to OpenGL
        self.hydra_viewport = None
        self.viewport = ViewportWidget()
        self.viewport.set_stage_manager(self.stage_manager)
        
        try:
            from ..rendering.hydra_viewport import HydraViewportWidget
            # Check if UsdImagingGL is actually available
            try:
                from pxr import UsdImagingGL
                # UsdImagingGL is available, create Hydra viewport
                self.hydra_viewport = HydraViewportWidget()
                self.hydra_viewport.set_stage_manager(self.stage_manager)
                # Add Hydra viewport to container
                viewport_layout.addWidget(self.hydra_viewport)
                self.use_hydra = True
                self.statusBar().showMessage("Using Hydra 2.0 rendering", 3000)
            except (ImportError, Exception) as e:
                # UsdImagingGL not available or failed to initialize, use OpenGL fallback
                print(f"Hydra 2.0 viewport is not available: {e}")
                print("Using OpenGL fallback")
                self.hydra_viewport = None
                viewport_layout.addWidget(self.viewport)
                self.use_hydra = False
        except (ImportError, Exception) as e:
            # Hydra viewport class not available or failed to create
            print(f"Hydra 2.0 viewport is not available: {e}")
            print("Using OpenGL fallback")
            self.hydra_viewport = None
            viewport_layout.addWidget(self.viewport)
            self.use_hydra = False
        
        viewport_container.setLayout(viewport_layout)
        self.setCentralWidget(viewport_container)
        
        # Add viewport overlay (will be shown after viewport is visible)
        from ..utils.viewport_overlay import ViewportOverlay
        # Use the active viewport (Hydra if available, otherwise OpenGL)
        active_viewport = self.hydra_viewport if (hasattr(self, 'hydra_viewport') and self.hydra_viewport) else self.viewport
        self.viewport_overlay = ViewportOverlay(active_viewport)
        self.viewport_overlay.setParent(active_viewport)
        self.viewport_overlay.raise_()
        self.viewport_overlay.show()
        
        # Store overlay reference in viewport for resize handling
        active_viewport.overlay = self.viewport_overlay
        
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
        # #region agent log
        import json
        # Detect project root dynamically
        script_dir = Path(__file__).parent.parent.parent.parent
        log_path = script_dir / ".cursor" / "debug.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(str(log_path), "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "viewer.py:1011", "message": "create_menus called", "data": {"log_path": str(log_path)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except Exception as e:
            # Fallback: try to write to current directory
            try:
                with open(".cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "viewer.py:1011", "message": "create_menus called (fallback)", "data": {"error": str(e)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
        # #endregion
        
        menubar = self.menuBar()
        
        # #region agent log
        try:
            with open(str(log_path), "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "viewer.py:1030", "message": "menubar obtained", "data": {"menubar_valid": menubar is not None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
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
        
        # Recent Files submenu (moved from View menu)
        self.recent_files_menu = file_menu.addMenu("&Recent Files")
        self.recent_files_actions = []
        QTimer.singleShot(0, self.update_recent_files_menu)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        # #region agent log
        try:
            with open(str(log_path), "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "viewer.py:1059", "message": "before view_menu creation", "data": {"menubar_valid": menubar is not None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        self.view_menu = menubar.addMenu("&View")
        view_menu = self.view_menu  # Keep local reference for compatibility
        
        # #region agent log
        try:
            with open(str(log_path), "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "viewer.py:1067", "message": "view_menu created", "data": {"view_menu_valid": view_menu is not None, "view_menu_ptr": str(id(view_menu)) if view_menu else None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        # Recent Files submenu
        # #region agent log
        try:
            with open(str(log_path), "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "viewer.py:1077", "message": "before recent_files_menu creation", "data": {"view_menu_valid": view_menu is not None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        # Bookmarks submenu (Recent Files moved to File menu)
        # #region agent log
        try:
            with open(str(log_path), "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "viewer.py:1095", "message": "before bookmarks_menu creation", "data": {"view_menu_valid": view_menu is not None, "view_menu_ptr": str(id(view_menu)) if view_menu else None, "recent_files_menu_valid": self.recent_files_menu is not None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        # Check if view_menu is still valid before adding submenu
        try:
            # Test if view_menu is still accessible
            test_title = view_menu.title()
            # #region agent log
            try:
                with open(str(log_path), "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "viewer.py:1106", "message": "view_menu accessibility test passed", "data": {"title": test_title}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open(str(log_path), "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "viewer.py:1113", "message": "view_menu accessibility test failed", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            # #endregion
            # Recreate view_menu if it was deleted
            self.view_menu = menubar.addMenu("&View")
            view_menu = self.view_menu
        
        try:
            self.bookmarks_menu = view_menu.addMenu("&Bookmarks")
            self.bookmarks_actions = []
            # #region agent log
            try:
                with open(str(log_path), "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "viewer.py:1125", "message": "bookmarks_menu created successfully", "data": {"bookmarks_menu_valid": self.bookmarks_menu is not None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open(str(log_path), "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "viewer.py:1133", "message": "bookmarks_menu creation failed", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            # #endregion
            raise
        
        # Update menus after all menus are created
        # (Delay to avoid Qt object lifecycle issues)
        QTimer.singleShot(0, self.update_bookmarks_menu)
        
        view_menu.addSeparator()
        
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
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        layer_comp_action = QAction("&Layer Composition...", self)
        layer_comp_action.triggered.connect(self.show_layer_composition)
        tools_menu.addAction(layer_comp_action)
        
        animation_editor_action = QAction("&Animation Curve Editor...", self)
        animation_editor_action.triggered.connect(self.show_animation_editor)
        tools_menu.addAction(animation_editor_action)
        
        material_editor_action = QAction("&Material Editor...", self)
        material_editor_action.triggered.connect(self.show_material_editor)
        tools_menu.addAction(material_editor_action)
        
        scene_search_action = QAction("&Scene Search & Filter...", self)
        scene_search_action.triggered.connect(self.show_scene_search)
        tools_menu.addAction(scene_search_action)
        
        tools_menu.addSeparator()
        
        hydra_toggle_action = QAction("Use &Hydra 2.0 Rendering", self, checkable=True)
        hydra_toggle_action.setChecked(False)
        hydra_toggle_action.triggered.connect(self.toggle_hydra_rendering)
        tools_menu.addAction(hydra_toggle_action)
        
        tools_menu.addSeparator()
        
        # Medium priority features
        camera_mgr_action = QAction("&Camera Management...", self)
        camera_mgr_action.triggered.connect(self.show_camera_manager)
        tools_menu.addAction(camera_mgr_action)
        
        prim_props_action = QAction("&Prim Properties...", self)
        prim_props_action.triggered.connect(self.show_prim_properties)
        tools_menu.addAction(prim_props_action)
        
        collection_editor_action = QAction("&Collection Editor...", self)
        collection_editor_action.triggered.connect(self.show_collection_editor)
        tools_menu.addAction(collection_editor_action)
        
        primvar_editor_action = QAction("&Primvar Editor...", self)
        primvar_editor_action.triggered.connect(self.show_primvar_editor)
        tools_menu.addAction(primvar_editor_action)
        
        render_settings_editor_action = QAction("&Render Settings Editor...", self)
        render_settings_editor_action.triggered.connect(self.show_render_settings_editor)
        tools_menu.addAction(render_settings_editor_action)
        
        tools_menu.addSeparator()
        
        # Additional features
        stage_variables_action = QAction("&Stage Variables...", self)
        stage_variables_action.triggered.connect(self.show_stage_variables)
        tools_menu.addAction(stage_variables_action)
        
        openexec_action = QAction("&OpenExec (Computed Attributes)...", self)
        openexec_action.triggered.connect(self.show_openexec)
        tools_menu.addAction(openexec_action)
        
        tools_menu.addSeparator()
        
        annotations_action = QAction("&Annotations...", self)
        annotations_action.triggered.connect(self.show_annotations)
        tools_menu.addAction(annotations_action)
        
        tools_menu.addSeparator()
        
        # Visual features
        aov_action = QAction("&AOV Visualization...", self)
        aov_action.triggered.connect(self.show_aov_visualization)
        tools_menu.addAction(aov_action)
        
        texture_preview_action = QAction("&Texture/Material Preview...", self)
        texture_preview_action.triggered.connect(self.show_texture_preview)
        tools_menu.addAction(texture_preview_action)
        
        tools_menu.addSeparator()
        
        # Selection sets
        selection_sets_action = QAction("&Selection Sets...", self)
        selection_sets_action.triggered.connect(self.show_selection_sets)
        tools_menu.addAction(selection_sets_action)
        
        tools_menu.addSeparator()
        
        # Advanced features
        multi_viewport_action = QAction("&Multi-Viewport...", self)
        multi_viewport_action.triggered.connect(self.show_multi_viewport)
        tools_menu.addAction(multi_viewport_action)
        
        scene_comparison_action = QAction("&Scene Comparison...", self)
        scene_comparison_action.triggered.connect(self.show_scene_comparison)
        tools_menu.addAction(scene_comparison_action)
        
        batch_operations_action = QAction("&Batch Operations...", self)
        batch_operations_action.triggered.connect(self.show_batch_operations)
        tools_menu.addAction(batch_operations_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut(QKeySequence("Ctrl+,"))
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)
        
        settings_menu.addSeparator()
        
        ocio_settings_action = QAction("&OCIO Color Management...", self)
        ocio_settings_action.triggered.connect(self.show_ocio_settings)
        settings_menu.addAction(ocio_settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        help_action = QAction("&Help...", self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("&About xStage", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
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
        self.hierarchy_tree.itemChanged.connect(self.on_hierarchy_item_changed)
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
        
        # OCIO Color Space Info
        ocio_group = QGroupBox("Color Management (OCIO)")
        ocio_layout = QFormLayout()
        
        self.ocio_status_label = QLabel("Not Available")
        ocio_layout.addRow("Status:", self.ocio_status_label)
        
        self.ocio_asset_cs_label = QLabel("-")
        ocio_layout.addRow("Asset Color Space:", self.ocio_asset_cs_label)
        
        self.ocio_display_cs_label = QLabel("-")
        ocio_layout.addRow("Display Color Space:", self.ocio_display_cs_label)
        
        self.ocio_config_label = QLabel("-")
        ocio_layout.addRow("OCIO Config:", self.ocio_config_label)
        
        ocio_settings_btn = QPushButton("Configure OCIO...")
        ocio_settings_btn.clicked.connect(self.show_ocio_settings)
        ocio_layout.addRow("", ocio_settings_btn)
        
        ocio_group.setLayout(ocio_layout)
        layout.addWidget(ocio_group)
        
        # Validation button
        validate_btn = QPushButton("Validate USD")
        validate_btn.clicked.connect(self.validate_stage)
        layout.addWidget(validate_btn)
        
        layout.addStretch()
        info_widget.setLayout(layout)
        dock.setWidget(info_widget)
        dock.setPalette(self.palette())
        if dock.widget():
            dock.widget().setPalette(self.palette())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        
    def create_playback_dock(self):
        """Create playback controls dock with improved UI (Xstudio-style)"""
        dock = QDockWidget(self)  # No title
        dock.setTitleBarWidget(QWidget())  # Hide title bar
        playback_widget = QWidget()
        layout = QHBoxLayout()  # Single horizontal line
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align
        
        # Playback buttons - styled to match UI theme
        button_style = """
            QPushButton {
                background-color: palette(button);
                color: palette(button-text);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: palette(button);
                border: 1px solid palette(highlight);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
        """
        
        first_frame_btn = QPushButton("⏮")
        first_frame_btn.setToolTip("First Frame")
        first_frame_btn.setFixedSize(32, 32)
        first_frame_btn.clicked.connect(self.goto_first_frame)
        first_frame_btn.setStyleSheet(button_style + "QPushButton { font-size: 14pt; }")
        layout.addWidget(first_frame_btn)
        
        prev_frame_btn = QPushButton("◀")
        prev_frame_btn.setToolTip("Previous Frame")
        prev_frame_btn.setFixedSize(32, 32)
        prev_frame_btn.clicked.connect(self.prev_frame)
        prev_frame_btn.setStyleSheet(button_style + "QPushButton { font-size: 14pt; }")
        layout.addWidget(prev_frame_btn)
        
        self.play_button = QPushButton("▶")
        self.play_button.setToolTip("Play/Pause")
        self.play_button.setFixedSize(40, 32)
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setStyleSheet(button_style + "QPushButton { font-size: 16pt; font-weight: bold; }")
        layout.addWidget(self.play_button)
        
        next_frame_btn = QPushButton("▶")
        next_frame_btn.setToolTip("Next Frame")
        next_frame_btn.setFixedSize(32, 32)
        next_frame_btn.clicked.connect(self.next_frame)
        next_frame_btn.setStyleSheet(button_style + "QPushButton { font-size: 14pt; }")
        layout.addWidget(next_frame_btn)
        
        last_frame_btn = QPushButton("⏭")
        last_frame_btn.setToolTip("Last Frame")
        last_frame_btn.setFixedSize(32, 32)
        last_frame_btn.clicked.connect(self.goto_last_frame)
        last_frame_btn.setStyleSheet(button_style + "QPushButton { font-size: 14pt; }")
        layout.addWidget(last_frame_btn)
        
        layout.addSpacing(20)  # Spacer between buttons and timeline
        
        # Timeline slider
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.valueChanged.connect(self.on_timeline_changed)
        self.timeline_slider.setMinimumWidth(200)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 6px;
                background: #333;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #2E7D32;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #66BB6A;
            }
        """)
        layout.addWidget(self.timeline_slider)
        
        layout.addSpacing(20)  # Spacer between timeline and info
        
        # Frame and time display - bright text
        self.frame_label = QLabel("Frame: 0")
        self.frame_label.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 4px; color: palette(window-text);")
        layout.addWidget(self.frame_label)
        
        self.time_label = QLabel("Time: 0.00s")
        self.time_label.setStyleSheet("font-weight: bold; font-size: 10pt; padding: 4px; color: palette(window-text);")
        layout.addWidget(self.time_label)
        
        layout.addSpacing(20)  # Spacer between info and FPS
        
        # FPS control
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet("color: #888; font-size: 10pt;")
        layout.addWidget(fps_label)
        
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 120)
        self.fps_spinbox.setValue(24)
        self.fps_spinbox.setFixedWidth(60)
        self.fps_spinbox.valueChanged.connect(self.on_fps_changed)
        layout.addWidget(self.fps_spinbox)
        
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
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event for file drops"""
        if event.mimeData().hasUrls():
            # Check if any of the dropped files are USD files
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if filepath:
                    file_ext = Path(filepath).suffix.lower()
                    if file_ext in ['.usd', '.usda', '.usdc', '.usdz']:
                        event.acceptProposedAction()
                        return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event for file drops"""
        if event.mimeData().hasUrls():
            # Get the first USD file from the dropped files
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if filepath:
                    file_ext = Path(filepath).suffix.lower()
                    if file_ext in ['.usd', '.usda', '.usdc', '.usdz']:
                        # Load the USD file
                        self.load_usd_file(filepath)
                        event.acceptProposedAction()
                        return
        event.ignore()
            
    def load_usd_file(self, filepath: str):
        """Load and display USD file"""
        self.statusBar().showMessage(f"Loading {filepath}...")
        
        if self.stage_manager.load_stage(filepath):
            self.current_file = filepath
            
            # Initialize payload manager
            if USD_AVAILABLE:
                from ..managers.payloads import PayloadManager
                self.payload_manager = PayloadManager(self.stage_manager.stage)
            
            # Update UI
            info = self.stage_manager.get_stage_info()
            for key, label in self.info_labels.items():
                if key in info:
                    label.setText(str(info[key]))
            
            # Update viewport header with stage cameras
            if hasattr(self, 'viewport_header'):
                self.viewport_header.set_stage(self.stage_manager.stage)
            
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
            print(f"DEBUG: Loading USD file. use_hydra={self.use_hydra}, has_hydra_viewport={bool(self.hydra_viewport)}")
            print(f"DEBUG: Stage loaded: {self.stage_manager.stage is not None}")
            print(f"DEBUG: Current time: {self.stage_manager.current_time}")
            
            # Ensure viewport has stage_manager set
            if not self.viewport.stage_manager:
                print("DEBUG: Setting stage_manager on viewport")
                self.viewport.set_stage_manager(self.stage_manager)
            
            if self.use_hydra and self.hydra_viewport:
                print("DEBUG: Using Hydra viewport")
                if not self.hydra_viewport.stage_manager:
                    self.hydra_viewport.set_stage_manager(self.stage_manager)
                self.hydra_viewport.set_stage(self.stage_manager.stage)
                self.hydra_viewport.update_geometry(float(start))
            else:
                print("DEBUG: Using OpenGL viewport")
                print(f"DEBUG: Viewport stage_manager: {self.viewport.stage_manager is not None}")
                self.viewport.update_geometry(float(start))
                # Force a repaint
                self.viewport.update()
                QApplication.processEvents()  # Process events to ensure update happens
            
            # Update hierarchy
            self.update_hierarchy()
            
            # Update feature widgets
            if self.layer_composition_widget:
                self.layer_composition_widget.set_stage(self.stage_manager.stage)
            if self.animation_editor_widget:
                self.animation_editor_widget.set_stage(self.stage_manager.stage)
            if self.material_editor_widget:
                self.material_editor_widget.set_stage(self.stage_manager.stage)
            if self.scene_search_widget:
                self.scene_search_widget.set_stage(self.stage_manager.stage)
            if self.camera_manager_widget:
                self.camera_manager_widget.set_stage(self.stage_manager.stage)
            if self.prim_properties_widget and self.prim_selection_manager:
                self.prim_properties_widget.set_selection_manager(self.prim_selection_manager)
            if self.collection_editor_widget:
                self.collection_editor_widget.set_stage(self.stage_manager.stage)
            if self.primvar_editor_widget:
                self.primvar_editor_widget.set_stage(self.stage_manager.stage)
            if self.render_settings_editor_widget:
                self.render_settings_editor_widget.set_stage(self.stage_manager.stage)
            if self.stage_variables_widget:
                self.stage_variables_widget.set_stage(self.stage_manager.stage)
            if self.openexec_widget:
                self.openexec_widget.set_stage(self.stage_manager.stage)
            if self.annotations_widget:
                self.annotations_widget.set_stage(self.stage_manager.stage)
            if self.multi_viewport_widget:
                self.multi_viewport_widget.set_stage_manager(self.stage_manager)
            
            # Update recent files
            if filepath:
                self.recent_files_manager.add_file(filepath, "usd")
                self.update_recent_files_menu()
            
            # Initialize managers
            if USD_AVAILABLE:
                from ..managers.undo_redo import UndoRedoManager
                self.undo_redo_manager = UndoRedoManager()
                
                if self.stage_manager.stage:
                    from ..managers.prim_selection import PrimSelectionManager
                    self.prim_selection_manager = PrimSelectionManager(self.stage_manager.stage)
                    
                            # Initialize LOD and instancing managers
                    self.lod_manager.stage = self.stage_manager.stage
                    # Detect LODs for all prims
                    for prim in self.stage_manager.stage.Traverse():
                        self.lod_manager.detect_lod_levels(str(prim.GetPath()))
                    
                    self.instancing_manager.stage = self.stage_manager.stage
                    self.instancing_manager.detect_instances()
                    
                    # Update selection set manager
                    self.selection_set_manager.stage = self.stage_manager.stage
                    
                    # Initialize light linking manager
                    if self.light_linking_manager is None:
                        from ..managers.light_linking_manager import LightLinkingManager
                        self.light_linking_manager = LightLinkingManager(self.stage_manager.stage)
                    else:
                        self.light_linking_manager.stage = self.stage_manager.stage
            
            # Detect color space from USD using OCIO
            if self.ocio_manager.is_available() and self.stage_manager.stage:
                color_space_info = self.ocio_manager.get_color_space_info(self.stage_manager.stage)
                self.current_color_space = color_space_info.get('asset_color_space')
                
                # Update viewport overlay with color space info
                if self.viewport_overlay:
                    self.viewport_overlay.set_color_space_info(color_space_info)
                
                # Update info dock with OCIO info
                if hasattr(self, 'ocio_status_label'):
                    self.ocio_status_label.setText("✓ Available")
                    self.ocio_status_label.setStyleSheet("color: green;")
                    self.ocio_asset_cs_label.setText(color_space_info.get('asset_color_space', 'Unknown'))
                    self.ocio_display_cs_label.setText(color_space_info.get('display_color_space', 'Unknown'))
                    self.ocio_config_label.setText(color_space_info.get('config_name', 'Unknown'))
            else:
                # Update info dock to show OCIO not available
                if hasattr(self, 'ocio_status_label'):
                    if self.ocio_manager.ocio_available:
                        self.ocio_status_label.setText("✗ Config Not Loaded")
                        self.ocio_status_label.setStyleSheet("color: orange;")
                    else:
                        self.ocio_status_label.setText("✗ Not Available")
                        self.ocio_status_label.setStyleSheet("color: red;")
                    self.ocio_asset_cs_label.setText("-")
                    self.ocio_display_cs_label.setText("-")
                    self.ocio_config_label.setText("-")
            
            # Calculate and display scene metrics
            from ..utils.scene_metrics import SceneMetricsCalculator
            scene_metrics = SceneMetricsCalculator.calculate_all_metrics(
                self.stage_manager.stage,
                geometry_data,
                filepath
            )
            
            # Update viewport overlay with scene metrics
            if self.viewport_overlay:
                self.viewport_overlay.set_scene_metrics(scene_metrics)
            
            # Update viewport overlay with stats
            if hasattr(self, 'viewport_overlay') and self.viewport_overlay:
                # Get active viewport (Hydra or OpenGL)
                active_viewport = self.hydra_viewport if (self.use_hydra and self.hydra_viewport) else self.viewport
                
                stats = {
                    'meshes': len(geometry_data.get('meshes', [])),
                    'cameras': len(geometry_data.get('cameras', [])),
                    'lights': len(geometry_data.get('lights', [])),
                    'materials': len(geometry_data.get('materials', [])),
                    'grid_enabled': active_viewport.settings.grid_enabled if hasattr(active_viewport, 'settings') else True,
                    'axis_enabled': active_viewport.settings.axis_enabled if hasattr(active_viewport, 'settings') else True,
                }
                self.viewport_overlay.set_stats(stats)
                self.viewport_overlay.update()  # Force update
                
                # Update camera info if available
                if geometry_data.get('cameras'):
                    cam = geometry_data['cameras'][0]
                    self.viewport_overlay.set_camera_info({
                        'name': cam.get('name', 'Camera'),
                        'fov': cam.get('focal_length', 50.0)
                    })
            
            # Clear cache for new file
            self.cache_manager.clear_cache_for_file(filepath)
            
            self.statusBar().showMessage(f"Loaded: {filepath}", 5000)
            self.setWindowTitle(f"xStage - {Path(filepath).name}")
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
            elif _is_light_prim(prim):
                type_indicators.append("💡")
            elif USD_AVAILABLE and prim.IsA(UsdShade.Material):
                type_indicators.append("🎨")
            elif USD_AVAILABLE and prim.IsA(UsdSkel.Root):
                type_indicators.append("🦴")
            elif USD_AVAILABLE and USDRENDER_RENDERSETTINGS_AVAILABLE and prim.IsA(UsdRender.RenderSettings):
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
            
            # Check visibility and set checkbox
            if USD_AVAILABLE:
                imageable = UsdGeom.Imageable(prim)
                if imageable:
                    visibility_attr = imageable.GetVisibilityAttr()
                    if visibility_attr:
                        visibility = visibility_attr.Get()
                        # Set checkbox state: checked = visible, unchecked = invisible
                        item.setCheckState(0, Qt.CheckState.Checked if visibility != UsdGeom.Tokens.invisible else Qt.CheckState.Unchecked)
                    else:
                        item.setCheckState(0, Qt.CheckState.Checked)  # Default to visible
                else:
                    item.setCheckState(0, Qt.CheckState.Checked)  # Default to visible
            
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
        from ..converters.converter_ui import ConverterDialog
        dialog = ConverterDialog(self)
        if dialog.exec():
            output_path = dialog.output_path_edit.text()
            if output_path and os.path.exists(output_path):
                self.load_usd_file(output_path)
                
    def toggle_playback(self):
        """Toggle playback on/off"""
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_button.setText("⏸")
            self.play_button.setToolTip("Pause")
            fps = self.fps_spinbox.value()
            interval = int(1000.0 / fps)
            self.playback_timer.start(interval)
        else:
            self.play_button.setText("▶")
            self.play_button.setToolTip("Play")
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
        
        # Update time label if it exists
        if hasattr(self, 'time_label'):
            fps = self.stage_manager.fps if self.stage_manager.fps > 0 else 24.0
            time_seconds = value / fps
            self.time_label.setText(f"Time: {time_seconds:.2f}s")
        
        if self.use_hydra and self.hydra_viewport:
            try:
                self.hydra_viewport.update_geometry(float(value))
            except RuntimeError:
                pass
        else:
            if self.viewport:
                try:
                    self.viewport.update_geometry(float(value))
                    self.viewport.update()
                except RuntimeError:
                    pass
        
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
        if not self.viewport:
            return
        try:
            if self.viewport.geometry_data and 'bounds' in self.viewport.geometry_data:
                self.viewport.frame_bounds(self.viewport.geometry_data['bounds'])
                self.viewport.update()
        except RuntimeError:
            # Widget was deleted, ignore
            pass
    
    def validate_stage(self):
        """Validate the current USD stage"""
        if not USD_AVAILABLE:
            QMessageBox.warning(self, "USD Not Available", 
                              "USD Python bindings not installed.")
            return
        
        try:
            from ..utils.validation import ValidationManager as USDValidator
            
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
    
    def show_layer_composition(self):
        """Show layer composition dock"""
        if not self.layer_composition_widget:
            from ..ui.editors.layer_composition_ui import LayerCompositionWidget
            self.layer_composition_widget = LayerCompositionWidget()
            dock = QDockWidget("Layer Composition", self)
            dock.setWidget(self.layer_composition_widget)
            # Apply theme to dock widget for color consistency
            dock.setPalette(self.palette())
            if dock.widget():
                dock.widget().setPalette(self.palette())
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.layer_composition_widget.set_stage(self.stage_manager.stage)
        else:
            # Find and show existing dock
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.layer_composition_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_animation_editor(self):
        """Show animation curve editor dock"""
        if not self.animation_editor_widget:
            from ..ui.editors.animation_curve_ui import AnimationCurveEditorWidget
            self.animation_editor_widget = AnimationCurveEditorWidget()
            dock = QDockWidget("Animation Curve Editor", self)
            dock.setWidget(self.animation_editor_widget)
            dock.setPalette(self.palette())
            if dock.widget():
                dock.widget().setPalette(self.palette())
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.animation_editor_widget.set_stage(self.stage_manager.stage)
        else:
            # Find and show existing dock
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.animation_editor_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_material_editor(self):
        """Show material editor dock"""
        if not self.material_editor_widget:
            from ..ui.editors.material_editor_ui import MaterialEditorWidget
            self.material_editor_widget = MaterialEditorWidget()
            dock = QDockWidget("Material Editor", self)
            dock.setWidget(self.material_editor_widget)
            dock.setPalette(self.palette())
            if dock.widget():
                dock.widget().setPalette(self.palette())
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.material_editor_widget.set_stage(self.stage_manager.stage)
        else:
            # Find and show existing dock
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.material_editor_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_scene_search(self):
        """Show scene search dock"""
        if not self.scene_search_widget:
            from ..ui.editors.scene_search_ui import SceneSearchWidget
            self.scene_search_widget = SceneSearchWidget()
            self.scene_search_widget.selection_changed.connect(self.on_search_selection_changed)
            dock = QDockWidget("Scene Search & Filter", self)
            dock.setWidget(self.scene_search_widget)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.scene_search_widget.set_stage(self.stage_manager.stage)
        else:
            # Find and show existing dock
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.scene_search_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def on_search_selection_changed(self, prim_path: str):
        """Handle search selection change"""
        # Select prim in hierarchy tree
        items = self.hierarchy_tree.findItems(prim_path, Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchRecursive, 0)
        if items:
            self.hierarchy_tree.setCurrentItem(items[0])
            self.hierarchy_tree.scrollToItem(items[0])
    
    def toggle_hydra_rendering(self, checked: bool):
        """Toggle between Hydra and OpenGL rendering"""
        if not self.hydra_viewport:
            QMessageBox.warning(self, "Hydra Not Available", 
                              "Hydra 2.0 viewport is not available. Using OpenGL fallback.")
            return
        
        self.use_hydra = checked
        
        if checked:
            # Switch to Hydra
            if not self.hydra_viewport:
                QMessageBox.warning(self, "Hydra Not Available", "Hydra viewport is not available.")
                return
            try:
                self.hydra_viewport.set_stage(self.stage_manager.stage)
                if self.stage_manager.stage:
                    self.hydra_viewport.update_geometry(self.stage_manager.current_time)
                self.setCentralWidget(self.hydra_viewport)
                self.statusBar().showMessage("Using Hydra 2.0 rendering", 3000)
            except RuntimeError:
                QMessageBox.warning(self, "Error", "Failed to switch to Hydra viewport.")
        else:
            # Switch to OpenGL
            if not self.viewport:
                return
            try:
                self.setCentralWidget(self.viewport)
                if self.stage_manager.stage:
                    self.viewport.update_geometry(self.stage_manager.current_time)
                self.statusBar().showMessage("Using OpenGL rendering", 3000)
            except RuntimeError:
                QMessageBox.warning(self, "Error", "Failed to switch to OpenGL viewport.")
    
    def show_camera_manager(self):
        """Show camera manager dock"""
        if not self.camera_manager_widget:
            from ..ui.editors.camera_manager_ui import CameraManagerWidget
            self.camera_manager_widget = CameraManagerWidget()
            self.camera_manager_widget.camera_selected.connect(self.on_camera_selected)
            dock = QDockWidget("Camera Management", self)
            dock.setWidget(self.camera_manager_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.camera_manager_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.camera_manager_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_light_manager(self):
        """Show light manager dock"""
        if not self.light_manager_widget:
            from ..ui.editors.light_manager_ui import LightManagerWidget
            self.light_manager_widget = LightManagerWidget()
            self.light_manager_widget.look_through_light.connect(self.look_through_light)
            self.light_manager_widget.light_changed.connect(self.on_light_changed)
            dock = QDockWidget("Light Management", self)
            dock.setWidget(self.light_manager_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.light_manager_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.light_manager_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def on_light_changed(self, light_path: str):
        """Handle light property change"""
        # Update viewport if needed
        if self.viewport:
            self.viewport.update()
        self.statusBar().showMessage(f"Light updated: {light_path}", 2000)
    
    def show_prim_properties(self):
        """Show prim properties dock"""
        if not self.prim_properties_widget:
            from ..ui.editors.prim_selection_ui import PrimPropertiesWidget
            self.prim_properties_widget = PrimPropertiesWidget()
            dock = QDockWidget("Prim Properties", self)
            dock.setWidget(self.prim_properties_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.prim_selection_manager:
                self.prim_properties_widget.set_selection_manager(self.prim_selection_manager)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.prim_properties_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_collection_editor(self):
        """Show collection editor dock"""
        if not self.collection_editor_widget:
            from ..ui.editors.collection_editor_ui import CollectionEditorWidget
            self.collection_editor_widget = CollectionEditorWidget()
            dock = QDockWidget("Collection Editor", self)
            dock.setWidget(self.collection_editor_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.collection_editor_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.collection_editor_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_primvar_editor(self):
        """Show primvar editor dock"""
        if not self.primvar_editor_widget:
            from ..ui.editors.primvar_editor_ui import PrimvarEditorWidget
            self.primvar_editor_widget = PrimvarEditorWidget()
            dock = QDockWidget("Primvar Editor", self)
            dock.setWidget(self.primvar_editor_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.primvar_editor_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.primvar_editor_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_render_settings_editor(self):
        """Show render settings editor dock"""
        if not self.render_settings_editor_widget:
            from ..ui.editors.render_settings_editor_ui import RenderSettingsEditorWidget
            self.render_settings_editor_widget = RenderSettingsEditorWidget()
            dock = QDockWidget("Render Settings Editor", self)
            dock.setWidget(self.render_settings_editor_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.render_settings_editor_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.render_settings_editor_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def launch_quiltix(self):
        """Launch QuiltiX MaterialX editor"""
        if not self.quiltix_manager.is_available():
            QMessageBox.warning(
                self, 
                "QuiltiX Not Available",
                "QuiltiX is not installed or not found in PATH.\n\n"
                "Install with: pip install quiltix\n"
                "Or ensure 'quiltix' command is available."
            )
            return
        
        if not self.current_file or not self.stage_manager.stage:
            QMessageBox.warning(
                self,
                "No USD File",
                "Please open a USD file first before launching QuiltiX."
            )
            return
        
        # Launch QuiltiX with current USD file
        success = self.quiltix_manager.launch_quiltix(self.current_file)
        
        if success:
            self.statusBar().showMessage(
                f"QuiltiX launched with {self.current_file}", 
                3000
            )
        else:
            QMessageBox.warning(
                self,
                "Launch Failed",
                "Failed to launch QuiltiX. Check console for errors."
            )
    
    def look_through_light(self, light_prim_path: str):
        """
        Look through a light (view scene from light's perspective)
        
        Args:
            light_prim_path: Path to light prim
        """
        if not USD_AVAILABLE or not self.stage_manager.stage:
            return
        
        try:
            from pxr import UsdLux, UsdGeom, Gf
            import numpy as np
            
            light_prim = self.stage_manager.stage.GetPrimAtPath(light_prim_path)
            if not light_prim:
                QMessageBox.warning(
                    self,
                    "Invalid Light",
                    f"Light not found: {light_prim_path}"
                )
                return
            
            # Check if it's a light
            if not _is_light_prim(light_prim):
                QMessageBox.warning(
                    self,
                    "Invalid Light",
                    f"Prim is not a light: {light_prim_path}"
                )
                return
            
            # Get light transform
            xformable = UsdGeom.Xformable(light_prim)
            transform = xformable.ComputeLocalToWorldTransform(self.stage_manager.current_time)
            
            # Extract position and orientation
            position = transform.ExtractTranslation()
            rotation = transform.ExtractRotation()
            
            # Calculate forward direction (light direction)
            # For directional lights, use the -Z axis
            # For point lights, we'll look at the scene center
            forward = Gf.Vec3d(0, 0, -1)
            rotation_matrix = rotation.GetMatrix()
            forward = rotation_matrix.TransformDir(forward)
            
            # Set viewport camera to light's position and orientation
            if hasattr(self.viewport, 'camera_target'):
                self.viewport.camera_target = np.array([position[0], position[1], position[2]])
            
            # Calculate camera distance (use current distance or default)
            if hasattr(self.viewport, 'camera_distance'):
                current_distance = self.viewport.camera_distance
            
            # Calculate rotation angles from forward direction
            # This is a simplified approach - could be improved
            forward_np = np.array([forward[0], forward[1], forward[2]])
            forward_np = forward_np / np.linalg.norm(forward_np)
            
            # Calculate rotation angles
            if hasattr(self.viewport, 'camera_rotation_y'):
                self.viewport.camera_rotation_y = np.degrees(np.arctan2(forward_np[0], forward_np[2]))
            if hasattr(self.viewport, 'camera_rotation_x'):
                self.viewport.camera_rotation_x = np.degrees(np.arcsin(-forward_np[1]))
            
            # Update viewport
            self.viewport.update()
            
            self.statusBar().showMessage(
                f"Looking through light: {light_prim.GetName()}", 
                3000
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Look-Through Failed",
                f"Error looking through light:\n{e}"
            )
    
    def on_camera_selected(self, camera_path: str):
        """Handle camera selection"""
        # Could switch viewport to use this camera
        self.statusBar().showMessage(f"Selected camera: {camera_path}", 2000)
    
    def on_viewport_camera_changed(self, camera_path: str):
        """Handle viewport camera change from header"""
        active_viewport = self.hydra_viewport if (self.use_hydra and self.hydra_viewport) else self.viewport
        
        if camera_path == "Perspective":
            # Use free camera
            active_viewport.current_usd_camera = None
            if hasattr(active_viewport, 'view_mode'):
                active_viewport.view_mode = "Perspective"
        else:
            # Use USD camera
            if USD_AVAILABLE and self.stage_manager.stage:
                prim = self.stage_manager.stage.GetPrimAtPath(camera_path)
                if prim and prim.IsA(UsdGeom.Camera):
                    active_viewport.current_usd_camera = prim
                    if hasattr(active_viewport, 'view_mode'):
                        active_viewport.view_mode = "Perspective"  # USD cameras are perspective
                    # TODO: Extract camera transform and apply to viewport
                    self.statusBar().showMessage(f"Using camera: {prim.GetName()}", 2000)
        
        active_viewport.update()
    
    def on_viewport_view_changed(self, view_name: str):
        """Handle viewport view change from header (Top, Front, etc.)"""
        active_viewport = self.hydra_viewport if (self.use_hydra and self.hydra_viewport) else self.viewport
        
        if hasattr(active_viewport, 'view_mode'):
            active_viewport.view_mode = view_name
            active_viewport.current_usd_camera = None  # Ortho views don't use USD cameras
            active_viewport.update()
    
    def on_viewport_overlay_toggled(self, visible: bool):
        """Handle viewport overlay visibility toggle from header"""
        if hasattr(self, 'viewport_overlay') and self.viewport_overlay:
            self.viewport_overlay.setVisible(visible)
            if visible:
                self.viewport_overlay.update()  # Force update when shown
    
    def show_multi_viewport(self):
        """Show multi-viewport widget"""
        if not self.multi_viewport_widget:
            from ..multi_viewport import MultiViewportWidget
            self.multi_viewport_widget = MultiViewportWidget()
            self.multi_viewport_widget.set_stage_manager(self.stage_manager)
            # Replace central widget
            self.setCentralWidget(self.multi_viewport_widget)
        else:
            self.setCentralWidget(self.multi_viewport_widget)
    
    def show_scene_comparison(self):
        """Show scene comparison dock"""
        if not self.scene_comparison_widget:
            from ..ui.editors.scene_comparison_ui import SceneComparisonWidget
            self.scene_comparison_widget = SceneComparisonWidget()
            dock = QDockWidget("Scene Comparison", self)
            dock.setWidget(self.scene_comparison_widget)
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.scene_comparison_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_batch_operations(self):
        """Show batch operations dialog"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Batch Operations")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Batch Operations"))
        layout.addWidget(QLabel("Select prims from hierarchy, then choose operation:"))
        
        # Operation buttons
        from ..managers.batch_operations import BatchOperationManager
        if self.stage_manager and self.stage_manager.stage:
            batch_mgr = BatchOperationManager(self.stage_manager.stage)
            # Add batch operation buttons here
            pass
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_help(self):
        """Show help dialog"""
        from ..utils.help_system import HelpDialog
        help_dialog = HelpDialog(self)
        help_dialog.exec()
    
    def show_openexec(self):
        """Show OpenExec dock"""
        if not self.openexec_widget:
            from ..ui.editors.openexec_ui import OpenExecWidget
            self.openexec_widget = OpenExecWidget()
            dock = QDockWidget("OpenExec - Computed Attributes", self)
            dock.setWidget(self.openexec_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.openexec_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.openexec_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_annotations(self):
        """Show annotations dock"""
        if not self.annotations_widget:
            from ..ui.editors.annotations_ui import AnnotationsWidget
            self.annotations_widget = AnnotationsWidget()
            dock = QDockWidget("Annotations", self)
            dock.setWidget(self.annotations_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.annotations_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.annotations_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def update_recent_files_menu(self):
        """Update recent files menu"""
        # Clear existing actions
        for action in self.recent_files_actions:
            if action:
                action.deleteLater()
        self.recent_files_actions.clear()
        
        # Use stored menu reference
        if not hasattr(self, 'recent_files_menu') or not self.recent_files_menu:
            return
        
        self.recent_files_menu.clear()
        
        # Add recent files
        recent_files = self.recent_files_manager.get_recent_files(limit=10)
        for recent_file in recent_files:
            file_path = Path(recent_file.path)
            display_name = file_path.name
            if recent_file.stage_name:
                display_name = f"{recent_file.stage_name} - {display_name}"
            
            action = QAction(display_name, self)
            action.setData(recent_file.path)
            action.triggered.connect(lambda checked, path=recent_file.path: self.load_recent_file(path))
            self.recent_files_menu.addAction(action)
            self.recent_files_actions.append(action)
        
        if not recent_files:
            no_files_action = QAction("No recent files", self)
            no_files_action.setEnabled(False)
            self.recent_files_menu.addAction(no_files_action)
    
    def load_recent_file(self, filepath: str):
        """Load a recent file"""
        if Path(filepath).exists():
            self.load_usd_file(filepath)
        else:
            QMessageBox.warning(self, "File Not Found", f"File not found: {filepath}")
            self.recent_files_manager.remove_file(filepath)
            self.update_recent_files_menu()
    
    def update_bookmarks_menu(self):
        """Update bookmarks menu"""
        # Clear existing actions
        for action in self.bookmarks_actions:
            if action:
                action.deleteLater()
        self.bookmarks_actions.clear()
        
        # Use stored menu reference
        if not hasattr(self, 'bookmarks_menu') or not self.bookmarks_menu:
            return
        
        self.bookmarks_menu.clear()
        
        # Add bookmarks for current stage
        if self.stage_manager and self.stage_manager.stage:
            stage_path = self.stage_manager.stage.GetRootLayer().identifier
            bookmarks = self.bookmark_manager.get_bookmarks_for_stage(stage_path)
            
            for bookmark in bookmarks:
                action = QAction(bookmark.name, self)
                action.setData(bookmark.id)
                action.triggered.connect(lambda checked, bm_id=bookmark.id: self.load_bookmark(bm_id))
                self.bookmarks_menu.addAction(action)
                self.bookmarks_actions.append(action)
        
        if not self.bookmarks_actions:
            no_bookmarks_action = QAction("No bookmarks", self)
            no_bookmarks_action.setEnabled(False)
            self.bookmarks_menu.addAction(no_bookmarks_action)
    
    def load_bookmark(self, bookmark_id: str):
        """Load a bookmark"""
        bookmark = next((bm for bm in self.bookmark_manager.bookmarks if bm.id == bookmark_id), None)
        if not bookmark:
            return
        
        # Load stage if different
        if bookmark.stage_path and self.stage_manager.stage:
            current_path = self.stage_manager.stage.GetRootLayer().identifier
            if bookmark.stage_path != current_path:
                self.load_usd_file(bookmark.stage_path)
        
        # Navigate to bookmark
        if bookmark.prim_path and self.stage_manager.stage:
            prim = self.stage_manager.stage.GetPrimAtPath(bookmark.prim_path)
            if prim:
                # Select prim in hierarchy
                # Could also frame camera if it's a camera bookmark
                pass
    
    def on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        palette = self.palette()
        self.theme_manager.apply_theme_to_palette(palette)
        self.setPalette(palette)
        
        # Update viewport background color
        if hasattr(self, 'viewport'):
            theme_colors = self.theme_manager.get_theme()
            bg_color = QColor(theme_colors.viewport_bg)
            self.viewport.settings.background_color = (
                bg_color.redF(), bg_color.greenF(), bg_color.blueF(), 1.0
            )
        
        # Apply theme to all dock widgets to fix color consistency
        self.apply_theme_to_docks()
        
        # Apply theme to menu bar
        menubar = self.menuBar()
        if menubar:
            menubar.setPalette(palette)
            # Apply to all menus
            for menu in menubar.findChildren(QMenu):
                menu.setPalette(palette)
    
    def apply_theme_to_docks(self):
        """Apply current theme to all dock widgets for color consistency"""
        palette = self.palette()
        for dock in self.findChildren(QDockWidget):
            dock.setPalette(palette)
            # Also apply to the widget inside the dock and all child widgets
            if dock.widget():
                dock.widget().setPalette(palette)
                # Recursively apply to all child widgets
                for child in dock.widget().findChildren(QWidget):
                    child.setPalette(palette)
    
    def _create_dock_with_theme(self, title: str, widget: QWidget, area: Qt.DockWidgetArea) -> QDockWidget:
        """Helper to create dock widget with theme applied"""
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setPalette(self.palette())
        if widget:
            widget.setPalette(self.palette())
        self.addDockWidget(area, dock)
        return dock
    
    def toggle_viewport_overlay(self, checked: bool):
        """Toggle viewport overlay visibility"""
        if hasattr(self, 'viewport_overlay'):
            self.viewport_overlay.setVisible(checked)
    
    def show_aov_visualization(self):
        """Show AOV visualization dock"""
        if not hasattr(self, 'aov_widget') or not self.aov_widget:
            from ..ui.editors.aov_visualization_ui import AOVVisualizationWidget
            self.aov_widget = AOVVisualizationWidget()
            dock = QDockWidget("AOV Visualization", self)
            dock.setWidget(self.aov_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.aov_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.aov_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_texture_preview(self):
        """Show texture/material preview dock"""
        if not hasattr(self, 'texture_preview_widget') or not self.texture_preview_widget:
            from ..ui.widgets.texture_preview import TexturePreviewWidget
            from ..ui.widgets.material_preview import MaterialPreviewWidget
            
            # Create tab widget with both texture and material preview
            preview_tabs = QTabWidget()
            
            texture_widget = TexturePreviewWidget()
            preview_tabs.addTab(texture_widget, "Texture")
            
            material_widget = MaterialPreviewWidget()
            preview_tabs.addTab(material_widget, "Material")
            
            self.texture_preview_widget = preview_tabs
            
            dock = QDockWidget("Texture/Material Preview", self)
            dock.setWidget(preview_tabs)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.texture_preview_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def show_selection_sets(self):
        """Show selection sets dock"""
        if not hasattr(self, 'selection_sets_widget') or not self.selection_sets_widget:
            from PySide6.QtWidgets import QListWidget
            
            # Create selection sets widget
            widget = QWidget()
            layout = QVBoxLayout()
            
            title = QLabel("<b>Selection Sets</b>")
            layout.addWidget(title)
            
            # Selection sets list
            self.selection_sets_list = QListWidget()
            self.selection_sets_list.itemDoubleClicked.connect(self.on_selection_set_double_clicked)
            layout.addWidget(self.selection_sets_list)
            
            # Buttons
            buttons_layout = QHBoxLayout()
            
            save_btn = QPushButton("Save Current Selection...")
            save_btn.clicked.connect(self.save_current_selection)
            buttons_layout.addWidget(save_btn)
            
            apply_btn = QPushButton("Apply Selected")
            apply_btn.clicked.connect(self.apply_selection_set)
            buttons_layout.addWidget(apply_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(self.delete_selection_set)
            buttons_layout.addWidget(delete_btn)
            
            layout.addLayout(buttons_layout)
            
            widget.setLayout(layout)
            
            self.selection_sets_widget = widget
            
            dock = QDockWidget("Selection Sets", self)
            dock.setWidget(widget)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
            
            self.refresh_selection_sets()
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.selection_sets_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def refresh_selection_sets(self):
        """Refresh selection sets list"""
        if hasattr(self, 'selection_sets_list') and self.selection_sets_list:
            self.selection_sets_list.clear()
            if self.stage_manager and self.stage_manager.stage:
                stage_path = self.stage_manager.stage.GetRootLayer().identifier
                selection_sets = self.selection_set_manager.get_selection_sets_for_stage(stage_path)
                for s in selection_sets:
                    item_text = f"{s.name} ({len(s.prim_paths)} prims)"
                    if s.description:
                        item_text += f" - {s.description}"
                    self.selection_sets_list.addItem(item_text)
    
    def save_current_selection(self):
        """Save current selection as selection set"""
        name, ok = QInputDialog.getText(self, "Save Selection Set", "Name:")
        if ok and name:
            # Get current selection from hierarchy
            selected_items = self.hierarchy_tree.selectedItems()
            prim_paths = []
            for item in selected_items:
                prim_path = item.data(0, Qt.ItemDataRole.UserRole)
                if prim_path:
                    prim_paths.append(prim_path)
            
            if prim_paths:
                self.selection_set_manager.set_current_selection(prim_paths)
                self.selection_set_manager.save_current_selection(name)
                self.refresh_selection_sets()
            else:
                QMessageBox.warning(self, "No Selection", "Please select prims in the hierarchy first.")
    
    def apply_selection_set(self):
        """Apply selected selection set"""
        if not hasattr(self, 'selection_sets_list') or not self.selection_sets_list:
            return
        
        selected = self.selection_sets_list.currentItem()
        if selected:
            # Get selection set name from item text
            item_text = selected.text()
            name = item_text.split(" (")[0]
            
            from ..managers.selection_sets import SelectionSetOperation
            prim_paths = self.selection_set_manager.apply_selection_set(name, SelectionSetOperation.REPLACE)
            # Select prims in hierarchy
            self.hierarchy_tree.clearSelection()
            for prim_path in prim_paths:
                items = self.hierarchy_tree.findItems(prim_path, Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchRecursive, 0)
                if items:
                    items[0].setSelected(True)
                    self.hierarchy_tree.scrollToItem(items[0])
    
    def delete_selection_set(self):
        """Delete selected selection set"""
        if not hasattr(self, 'selection_sets_list') or not self.selection_sets_list:
            return
        
        selected = self.selection_sets_list.currentItem()
        if selected:
            item_text = selected.text()
            name = item_text.split(" (")[0]
            
            reply = QMessageBox.question(
                self, "Delete Selection Set", f"Delete '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.selection_set_manager.delete_selection_set(name)
                self.refresh_selection_sets()
    
    def on_selection_set_double_clicked(self, item):
        """Handle double-click on selection set"""
        self.apply_selection_set()
    
    def show_preferences(self):
        """Show preferences dialog"""
        from ..ui.editors.preferences_ui import PreferencesDialog
        
        dialog = PreferencesDialog(self)
        if dialog.exec():
            # Reload OCIO manager with new settings
            self.reload_ocio_manager()
            self.statusBar().showMessage("Preferences saved", 3000)
    
    def reload_ocio_manager(self):
        """Reload OCIO manager with preferences"""
        from PySide6.QtCore import QSettings
        from ..utils.ocio_manager import OCIOManager
        
        settings = QSettings("xStage", "xStage")
        config_path = settings.value("ocio/config_path", "", type=str) or None
        
        # Reinitialize OCIO manager with new config
        self.ocio_manager = OCIOManager(config_path=config_path)
        
        # Update UI if stage is loaded
        if self.stage_manager.stage and self.ocio_manager.is_available():
            color_space_info = self.ocio_manager.get_color_space_info(self.stage_manager.stage)
            if hasattr(self, 'ocio_status_label'):
                self.ocio_status_label.setText("✓ Available")
                self.ocio_status_label.setStyleSheet("color: green;")
                self.ocio_asset_cs_label.setText(color_space_info.get('asset_color_space', 'Unknown'))
                self.ocio_display_cs_label.setText(color_space_info.get('display_color_space', 'Unknown'))
                self.ocio_config_label.setText(color_space_info.get('config_name', 'Unknown'))
                if self.viewport_overlay:
                    self.viewport_overlay.set_color_space_info(color_space_info)
    
    def show_ocio_settings(self):
        """Show OCIO color management settings dialog"""
        from ..ui.editors.ocio_settings_ui import OCIOSettingsDialog
        
        dialog = OCIOSettingsDialog(self, self.ocio_manager)
        if dialog.exec():
            # Config was reloaded, update color space info if stage is loaded
            if self.stage_manager.stage and self.ocio_manager.is_available():
                color_space_info = self.ocio_manager.get_color_space_info(self.stage_manager.stage)
                self.current_color_space = color_space_info.get('asset_color_space')
                
                if self.viewport_overlay:
                    self.viewport_overlay.set_color_space_info(color_space_info)
                
                self.statusBar().showMessage(
                    f"OCIO config updated: {self.ocio_manager.get_config_name()}", 
                    3000
                )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About xStage",
            "<h2>xStage USD Viewer</h2>"
            "<p>Professional USD viewer and converter for VFX pipelines</p>"
            "<p>Version 0.1.0</p>"
            "<p>Built with OpenUSD 25.11</p>"
            "<p>© NOX VFX & Contributors</p>"
        )
    
    def _add_tooltips(self):
        """Add tooltips to UI elements"""
        if not self.help_system:
            return
        
        # Add tooltips to common widgets
        if hasattr(self, 'hierarchy_tree'):
            self.help_system.set_tooltip(self.hierarchy_tree, 'hierarchy')
        if hasattr(self, 'viewport'):
            self.help_system.set_tooltip(self.viewport, 'viewport')
        if hasattr(self, 'timeline_slider'):
            self.help_system.set_tooltip(self.timeline_slider, 'timeline')
    
    def show_stage_variables(self):
        """Show stage variables dock"""
        if not self.stage_variables_widget:
            from ..ui.editors.stage_variables_ui import StageVariablesWidget
            self.stage_variables_widget = StageVariablesWidget()
            dock = QDockWidget("Stage Variables", self)
            dock.setWidget(self.stage_variables_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            if self.stage_manager.stage:
                self.stage_variables_widget.set_stage(self.stage_manager.stage)
        else:
            for dock in self.findChildren(QDockWidget):
                if dock.widget() == self.stage_variables_widget:
                    dock.show()
                    dock.raise_()
                    break
    
    def on_hierarchy_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle hierarchy item checkbox change (visibility toggle)"""
        if not USD_AVAILABLE or not self.stage_manager.stage:
            return
        
        prim_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not prim_path or "::" in prim_path:
            # Skip variant sets and collections
            return
        
        try:
            prim = self.stage_manager.stage.GetPrimAtPath(prim_path)
            if not prim:
                return
            
            imageable = UsdGeom.Imageable(prim)
            if not imageable:
                return
            
            # Get new visibility state
            is_checked = item.checkState(0) == Qt.CheckState.Checked
            visibility = UsdGeom.Tokens.inherited if is_checked else UsdGeom.Tokens.invisible
            
            # Set visibility
            imageable.MakeVisible() if is_checked else imageable.MakeInvisible()
            
            # Update viewport
            if self.viewport:
                try:
                    self.viewport.update_geometry(self.stage_manager.current_time)
                    self.viewport.update()
                except RuntimeError:
                    pass
        except Exception as e:
            print(f"Error toggling visibility: {e}")
    
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
            from ..managers.variants import VariantManager
            
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
    # CRITICAL: Set platform BEFORE importing QApplication
    # Force xcb (X11) platform plugin - EGL is failing on this system
    # Must be set before any Qt imports or QApplication creation
    import os
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ['QT_OPENGL'] = 'desktop'
    
    # Disable EGL explicitly
    os.environ['QT_XCB_GL_INTEGRATION'] = 'xcb_glx'
    
    # Debug: Print what we're setting
    print(f"Setting QT_QPA_PLATFORM={os.environ.get('QT_QPA_PLATFORM')}", file=sys.stderr)
    print(f"Setting QT_OPENGL={os.environ.get('QT_OPENGL')}", file=sys.stderr)
    print(f"DISPLAY={os.environ.get('DISPLAY', 'NOT SET')}", file=sys.stderr)
    
    app = QApplication(sys.argv)
    app.setApplicationName("xStage")
    app.setOrganizationName("xStage")
    
    # Verify platform after QApplication creation
    platform_name = app.platformName()
    print(f"Qt is using platform: {platform_name}", file=sys.stderr)
    
    if platform_name != 'xcb':
        print(f"WARNING: Qt is using {platform_name} instead of xcb!", file=sys.stderr)
        print("This may cause OpenGL context creation failures.", file=sys.stderr)
    
    try:
        window = USDViewerWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting application: {e}", file=sys.stderr)
        print("\nTroubleshooting tips:", file=sys.stderr)
        print("1. Ensure you have proper graphics drivers installed", file=sys.stderr)
        print("2. Check that X11 is running: echo $DISPLAY", file=sys.stderr)
        print("3. Install OpenGL libraries: sudo dnf install mesa-libGL mesa-libGLU mesa-libEGL", file=sys.stderr)
        print("4. Install xcb libraries: sudo dnf install libxcb libxcb-devel", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()