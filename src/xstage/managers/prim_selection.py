"""
Prim Selection & Manipulation
Handles prim selection, highlighting, and transform manipulation
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, List, Set
from pxr import Usd, UsdGeom, Gf

try:
    from pxr import Usd, UsdGeom, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class PrimSelectionManager:
    """Manages prim selection and manipulation"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
        self.selected_prims: Set[str] = set()
        self.highlighted_prim: Optional[str] = None
    
    def select_prim(self, prim_path: str, add_to_selection: bool = False):
        """Select a prim"""
        if not add_to_selection:
            self.selected_prims.clear()
        self.selected_prims.add(prim_path)
    
    def deselect_prim(self, prim_path: str):
        """Deselect a prim"""
        self.selected_prims.discard(prim_path)
    
    def clear_selection(self):
        """Clear all selections"""
        self.selected_prims.clear()
    
    def get_selected_prims(self) -> List[Usd.Prim]:
        """Get list of selected prims"""
        prims = []
        for path_str in self.selected_prims:
            prim = self.stage.GetPrimAtPath(path_str)
            if prim and prim.IsValid():
                prims.append(prim)
        return prims
    
    def is_selected(self, prim_path: str) -> bool:
        """Check if a prim is selected"""
        return prim_path in self.selected_prims
    
    def set_highlighted(self, prim_path: Optional[str]):
        """Set highlighted prim (for hover)"""
        self.highlighted_prim = prim_path
    
    def get_highlighted(self) -> Optional[str]:
        """Get highlighted prim"""
        return self.highlighted_prim
    
    def get_prim_bounds(self, prim: Usd.Prim, time_code: float = 0.0) -> Optional[Gf.BBox3d]:
        """Get bounding box for a prim"""
        if not USD_AVAILABLE or not prim:
            return None
        
        try:
            if prim.IsA(UsdGeom.Boundable):
                boundable = UsdGeom.Boundable(prim)
                bbox = boundable.ComputeWorldBound(time_code, Usd.TimeCode.Default())
                return bbox
        except Exception as e:
            print(f"Error getting prim bounds: {e}")
        
        return None
    
    def get_prim_transform(self, prim: Usd.Prim, time_code: float = 0.0) -> Optional[Gf.Matrix4d]:
        """Get transform matrix for a prim"""
        if not USD_AVAILABLE or not prim:
            return None
        
        try:
            if prim.IsA(UsdGeom.Xformable):
                xformable = UsdGeom.Xformable(prim)
                transform = xformable.ComputeLocalToWorldTransform(time_code)
                return transform
        except Exception as e:
            print(f"Error getting prim transform: {e}")
        
        return None
    
    def set_prim_transform(self, prim: Usd.Prim, transform: Gf.Matrix4d, time_code: float = None) -> bool:
        """Set transform for a prim"""
        if not USD_AVAILABLE or not prim or not prim.IsA(UsdGeom.Xformable):
            return False
        
        try:
            xformable = UsdGeom.Xformable(prim)
            
            # Get current transform
            current_transform = xformable.ComputeLocalToWorldTransform(time_code or 0.0)
            
            # Calculate local transform
            parent_prim = prim.GetParent()
            if parent_prim and parent_prim.IsA(UsdGeom.Xformable):
                parent_xform = UsdGeom.Xformable(parent_prim)
                parent_transform = parent_xform.ComputeLocalToWorldTransform(time_code or 0.0)
                local_transform = transform * parent_transform.GetInverse()
            else:
                local_transform = transform
            
            # Set transform
            xform_op = xformable.AddTransformOp()
            if time_code is not None:
                xform_op.Set(local_transform, time_code)
            else:
                xform_op.Set(local_transform)
            
            return True
        except Exception as e:
            print(f"Error setting prim transform: {e}")
            return False
    
    def translate_prim(self, prim: Usd.Prim, translation: Gf.Vec3d, time_code: float = None) -> bool:
        """Translate a prim"""
        if not USD_AVAILABLE or not prim or not prim.IsA(UsdGeom.Xformable):
            return False
        
        try:
            xformable = UsdGeom.Xformable(prim)
            translate_op = xformable.AddTranslateOp()
            if time_code is not None:
                translate_op.Set(translation, time_code)
            else:
                translate_op.Set(translation)
            return True
        except Exception as e:
            print(f"Error translating prim: {e}")
            return False
    
    def rotate_prim(self, prim: Usd.Prim, rotation: Gf.Vec3f, time_code: float = None) -> bool:
        """Rotate a prim (Euler angles in degrees)"""
        if not USD_AVAILABLE or not prim or not prim.IsA(UsdGeom.Xformable):
            return False
        
        try:
            xformable = UsdGeom.Xformable(prim)
            rotate_op = xformable.AddRotateXYZOp()
            if time_code is not None:
                rotate_op.Set(rotation, time_code)
            else:
                rotate_op.Set(rotation)
            return True
        except Exception as e:
            print(f"Error rotating prim: {e}")
            return False
    
    def scale_prim(self, prim: Usd.Prim, scale: Gf.Vec3f, time_code: float = None) -> bool:
        """Scale a prim"""
        if not USD_AVAILABLE or not prim or not prim.IsA(UsdGeom.Xformable):
            return False
        
        try:
            xformable = UsdGeom.Xformable(prim)
            scale_op = xformable.AddScaleOp()
            if time_code is not None:
                scale_op.Set(scale, time_code)
            else:
                scale_op.Set(scale)
            return True
        except Exception as e:
            print(f"Error scaling prim: {e}")
            return False

