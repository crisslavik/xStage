"""
USD Stage Manager
Handles USD stage loading, playback, and geometry extraction
"""

from typing import Optional, Dict, List, Tuple
import numpy as np

try:
    from pxr import Usd, UsdGeom, UsdShade, UsdLux, UsdSkel, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    print("Warning: USD not available")


class USDStageManager:
    """Manages USD stage loading, playback, and queries"""
    
    def __init__(self):
        self.stage: Optional[Usd.Stage] = None
        self.current_time: float = 0.0
        self.time_range: tuple = (0.0, 0.0)
        self.fps: float = 24.0
        self.up_axis: str = 'Y'  # Default to Y-up
        self.meters_per_unit: float = 0.01  # Default to cm (Maya/Max default)
        
    def load_stage(self, filepath: str) -> bool:
        """Load USD stage from file"""
        if not USD_AVAILABLE:
            print("Error: USD not available")
            return False
            
        try:
            self.stage = Usd.Stage.Open(filepath)
            if not self.stage:
                print(f"Error: Could not open USD file: {filepath}")
                return False
                
            # Get time range
            start_time = self.stage.GetStartTimeCode()
            end_time = self.stage.GetEndTimeCode()
            self.time_range = (float(start_time), float(end_time))
            self.current_time = float(start_time)
            
            # Get FPS
            self.fps = float(self.stage.GetTimeCodesPerSecond())
            
            # Get up-axis from stage metadata
            up_axis_token = UsdGeom.GetStageUpAxis(self.stage)
            self.up_axis = 'Z' if up_axis_token == UsdGeom.Tokens.z else 'Y'
            
            # Get meters per unit
            self.meters_per_unit = UsdGeom.GetStageMetersPerUnit(self.stage)
            
            print(f"Loaded USD stage: {filepath}")
            print(f"Time range: {self.time_range[0]} - {self.time_range[1]}")
            print(f"FPS: {self.fps}")
            print(f"Up axis: {self.up_axis}")
            print(f"Meters per unit: {self.meters_per_unit}")
            
            return True
        except Exception as e:
            print(f"Error loading USD stage: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_geometry_data(self, time_code: float) -> Dict:
        """Extract geometry data at given time code"""
        if not self.stage:
            return {'meshes': [], 'cameras': [], 'lights': [], 'bounds': None}
        
        self.current_time = time_code
        
        meshes = []
        cameras = []
        lights = []
        bounds_min = np.array([float('inf'), float('inf'), float('inf')])
        bounds_max = np.array([float('-inf'), float('-inf'), float('-inf')])
        
        # Traverse stage
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                mesh_data = self._extract_mesh(prim, time_code)
                if mesh_data:
                    meshes.append(mesh_data)
                    # Update bounds
                    if 'points' in mesh_data and len(mesh_data['points']) > 0:
                        points = np.array(mesh_data['points'])
                        bounds_min = np.minimum(bounds_min, points.min(axis=0))
                        bounds_max = np.maximum(bounds_max, points.max(axis=0))
            
            elif prim.IsA(UsdGeom.Camera):
                camera_data = self._extract_camera(prim, time_code)
                if camera_data:
                    cameras.append(camera_data)
            
            elif self._is_light(prim):
                light_data = self._extract_light(prim, time_code)
                if light_data:
                    lights.append(light_data)
        
        # Calculate bounds
        bounds = None
        if np.all(np.isfinite(bounds_min)) and np.all(np.isfinite(bounds_max)):
            center = (bounds_min + bounds_max) / 2
            size = bounds_max - bounds_min
            bounds = {
                'min': bounds_min.tolist(),
                'max': bounds_max.tolist(),
                'center': center.tolist(),
                'size': size.tolist()
            }
        
        return {
            'meshes': meshes,
            'cameras': cameras,
            'lights': lights,
            'bounds': bounds,
            'up_axis': self.up_axis,
            'meters_per_unit': self.meters_per_unit,
            'variants': self._extract_variants(),
            'collections': self._extract_collections(),
            'materials': self._extract_materials()
        }
    
    def _extract_mesh(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract mesh data from prim"""
        try:
            mesh = UsdGeom.Mesh(prim)
            
            # Get points
            points_attr = mesh.GetPointsAttr()
            if not points_attr:
                return None
            points = points_attr.Get(time_code)
            if not points:
                return None
            
            # Get face data
            face_vertex_counts = mesh.GetFaceVertexCountsAttr().Get(time_code)
            face_vertex_indices = mesh.GetFaceVertexIndicesAttr().Get(time_code)
            
            # Get normals
            normals_attr = mesh.GetNormalsAttr()
            normals = normals_attr.Get(time_code) if normals_attr else None
            
            # Get transform
            xformable = UsdGeom.Xformable(prim)
            transform_matrix = xformable.ComputeLocalToWorldTransform(time_code)
            
            return {
                'name': prim.GetName(),
                'path': prim.GetPath().pathString,
                'points': [list(p) for p in points],
                'face_vertex_counts': list(face_vertex_counts) if face_vertex_counts else [],
                'face_vertex_indices': list(face_vertex_indices) if face_vertex_indices else [],
                'normals': [list(n) for n in normals] if normals else None,
                'transform': [list(row) for row in transform_matrix]
            }
        except Exception as e:
            print(f"Error extracting mesh {prim.GetPath()}: {e}")
            return None
    
    def _extract_camera(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract camera data from prim"""
        try:
            camera = UsdGeom.Camera(prim)
            
            # Get camera properties
            focal_length = camera.GetFocalLengthAttr().Get(time_code)
            h_aperture = camera.GetHorizontalApertureAttr().Get(time_code)
            v_aperture = camera.GetVerticalApertureAttr().Get(time_code)
            
            # Calculate FOV
            fov = 2 * np.arctan(h_aperture / (2 * focal_length)) * 180 / np.pi if focal_length else 60.0
            
            # Get transform
            xformable = UsdGeom.Xformable(prim)
            transform_matrix = xformable.ComputeLocalToWorldTransform(time_code)
            
            return {
                'name': prim.GetName(),
                'path': prim.GetPath().pathString,
                'fov': float(fov),
                'focal_length': float(focal_length) if focal_length else 50.0,
                'transform': [list(row) for row in transform_matrix]
            }
        except Exception as e:
            print(f"Error extracting camera {prim.GetPath()}: {e}")
            return None
    
    def _is_light(self, prim: Usd.Prim) -> bool:
        """Check if prim is a light"""
        if not USD_AVAILABLE:
            return False
        try:
            return prim.IsA(UsdLux.Light) or prim.IsA(UsdLux.LightAPI)
        except Exception:
            return False
    
    def _extract_light(self, prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract light data from prim"""
        try:
            # Get transform
            xformable = UsdGeom.Xformable(prim)
            transform_matrix = xformable.ComputeLocalToWorldTransform(time_code)
            
            return {
                'name': prim.GetName(),
                'path': prim.GetPath().pathString,
                'type': prim.GetTypeName(),
                'transform': [list(row) for row in transform_matrix]
            }
        except Exception as e:
            print(f"Error extracting light {prim.GetPath()}: {e}")
            return None
    
    def _extract_variants(self) -> List[Dict]:
        """Extract variant sets from stage"""
        variants = []
        if not self.stage:
            return variants
        
        for prim in self.stage.Traverse():
            if prim.HasVariantSets():
                variant_sets = prim.GetVariantSets()
                variant_data = {
                    'prim_path': prim.GetPath().pathString,
                    'variant_sets': {}
                }
                for variant_set_name in variant_sets.GetNames():
                    variant_set = variant_sets.GetVariantSet(variant_set_name)
                    variant_data['variant_sets'][variant_set_name] = {
                        'current_selection': variant_set.GetVariantSelection(),
                        'variants': variant_set.GetVariantNames()
                    }
                variants.append(variant_data)
        
        return variants
    
    def _extract_collections(self) -> List[Dict]:
        """Extract collections from stage"""
        # Placeholder for collection extraction
        return []
    
    def _extract_materials(self) -> List[Dict]:
        """Extract materials from stage"""
        materials = []
        if not self.stage or not USD_AVAILABLE:
            return materials
        
        for prim in self.stage.Traverse():
            if prim.IsA(UsdShade.Material):
                materials.append({
                    'name': prim.GetName(),
                    'path': prim.GetPath().pathString
                })
        
        return materials
