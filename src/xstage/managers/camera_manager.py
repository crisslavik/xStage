"""
Camera Management
Manages USD cameras - listing, switching, editing, and creation
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd, UsdGeom, Gf

try:
    from pxr import Usd, UsdGeom, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class CameraManager:
    """Manages USD cameras"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
        self.current_camera = None
    
    def find_all_cameras(self) -> List[Usd.Prim]:
        """Find all cameras in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        cameras = []
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Camera):
                cameras.append(prim)
        return cameras
    
    def get_camera_info(self, camera_prim: Usd.Prim, time_code: float = 0.0) -> Optional[Dict]:
        """Get camera information"""
        if not USD_AVAILABLE or not camera_prim or not camera_prim.IsA(UsdGeom.Camera):
            return None
        
        try:
            camera = UsdGeom.Camera(camera_prim)
            xformable = UsdGeom.Xformable(camera_prim)
            transform = xformable.ComputeLocalToWorldTransform(time_code)
            
            # Extract camera properties
            focal_length = camera.GetFocalLengthAttr().Get(time_code) if camera.GetFocalLengthAttr() else 50.0
            h_aperture = camera.GetHorizontalApertureAttr().Get(time_code) if camera.GetHorizontalApertureAttr() else 20.955
            v_aperture = camera.GetVerticalApertureAttr().Get(time_code) if camera.GetVerticalApertureAttr() else 15.955
            near_clip = camera.GetNearClipPlaneAttr().Get(time_code) if camera.GetNearClipPlaneAttr() else 0.1
            far_clip = camera.GetFarClipPlaneAttr().Get(time_code) if camera.GetFarClipPlaneAttr() else 1000.0
            f_stop = camera.GetFStopAttr().Get(time_code) if camera.GetFStopAttr() else None
            focus_distance = camera.GetFocusDistanceAttr().Get(time_code) if camera.GetFocusDistanceAttr() else None
            
            # Get projection type
            projection = camera.GetProjectionAttr().Get(time_code) if camera.GetProjectionAttr() else 'perspective'
            
            return {
                'name': camera_prim.GetName(),
                'path': camera_prim.GetPath().pathString,
                'transform': transform,
                'focal_length': focal_length,
                'horizontal_aperture': h_aperture,
                'vertical_aperture': v_aperture,
                'near_clip': near_clip,
                'far_clip': far_clip,
                'f_stop': f_stop,
                'focus_distance': focus_distance,
                'projection': projection,
            }
        except Exception as e:
            print(f"Error getting camera info: {e}")
            return None
    
    def set_current_camera(self, camera_prim: Usd.Prim):
        """Set the current active camera"""
        if camera_prim and camera_prim.IsA(UsdGeom.Camera):
            self.current_camera = camera_prim
    
    def get_current_camera(self) -> Optional[Usd.Prim]:
        """Get the current active camera"""
        return self.current_camera
    
    def create_camera(self, path: str, name: str = "Camera") -> Optional[Usd.Prim]:
        """Create a new camera"""
        if not USD_AVAILABLE or not self.stage:
            return None
        
        try:
            camera_path = f"{path}/{name}" if not path.endswith(name) else path
            camera = UsdGeom.Camera.Define(self.stage, camera_path)
            
            # Set default properties
            camera.GetFocalLengthAttr().Set(50.0)
            camera.GetHorizontalApertureAttr().Set(20.955)
            camera.GetVerticalApertureAttr().Set(15.955)
            camera.GetNearClipPlaneAttr().Set(0.1)
            camera.GetFarClipPlaneAttr().Set(1000.0)
            camera.GetProjectionAttr().Set('perspective')
            
            return camera.GetPrim()
        except Exception as e:
            print(f"Error creating camera: {e}")
            return None
    
    def set_camera_property(self, camera_prim: Usd.Prim, property_name: str, value, time_code: float = None) -> bool:
        """Set a camera property"""
        if not USD_AVAILABLE or not camera_prim or not camera_prim.IsA(UsdGeom.Camera):
            return False
        
        try:
            camera = UsdGeom.Camera(camera_prim)
            
            property_map = {
                'focal_length': camera.GetFocalLengthAttr(),
                'horizontal_aperture': camera.GetHorizontalApertureAttr(),
                'vertical_aperture': camera.GetVerticalApertureAttr(),
                'near_clip': camera.GetNearClipPlaneAttr(),
                'far_clip': camera.GetFarClipPlaneAttr(),
                'f_stop': camera.GetFStopAttr(),
                'focus_distance': camera.GetFocusDistanceAttr(),
                'projection': camera.GetProjectionAttr(),
            }
            
            if property_name in property_map:
                attr = property_map[property_name]
                if attr:
                    if time_code is not None:
                        attr.Set(value, time_code)
                    else:
                        attr.Set(value)
                    return True
        
        except Exception as e:
            print(f"Error setting camera property: {e}")
            return False
        
        return False
    
    def get_camera_view_matrix(self, camera_prim: Usd.Prim, time_code: float = 0.0) -> Optional[Gf.Matrix4d]:
        """Get camera view matrix"""
        if not USD_AVAILABLE or not camera_prim:
            return None
        
        try:
            xformable = UsdGeom.Xformable(camera_prim)
            transform = xformable.ComputeLocalToWorldTransform(time_code)
            
            # Extract position and orientation
            position = transform.ExtractTranslation()
            rotation = transform.ExtractRotation()
            
            # Create view matrix (inverse of camera transform)
            view_matrix = Gf.Matrix4d()
            view_matrix.SetLookAt(position, position + Gf.Vec3d(0, 0, -1), Gf.Vec3d(0, 1, 0))
            view_matrix = view_matrix.GetInverse()
            
            return view_matrix
        except Exception as e:
            print(f"Error getting camera view matrix: {e}")
            return None

