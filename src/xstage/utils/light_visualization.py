"""
Light Visualization in Viewport
Draws light icons, cones, and direction indicators
"""

from typing import Optional, Dict, List
from pxr import Usd, UsdLux, UsdGeom, Gf
import numpy as np

try:
    from pxr import Usd, UsdLux, UsdGeom, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class LightVisualization:
    """Manages light visualization in viewport"""
    
    @staticmethod
    def get_light_visualization_data(light_prim: Usd.Prim, time_code: float = 0.0) -> Optional[Dict]:
        """Get visualization data for a light"""
        if not USD_AVAILABLE or not light_prim or not light_prim.IsA(UsdLux.Light):
            return None
        
        try:
            xformable = UsdGeom.Xformable(light_prim)
            transform = xformable.ComputeLocalToWorldTransform(time_code)
            
            # Extract position and direction
            position = transform.ExtractTranslation()
            # Default direction is -Z in local space
            direction = Gf.Vec3d(0, 0, -1)
            direction = transform.TransformDir(direction)
            
            viz_data = {
                'name': light_prim.GetName(),
                'path': light_prim.GetPath().pathString,
                'position': np.array([position[0], position[1], position[2]]),
                'direction': np.array([direction[0], direction[1], direction[2]]),
                'transform': transform,
                'type': light_prim.GetTypeName(),
                'intensity': 1.0,
                'color': (1.0, 1.0, 1.0),
                'cone_angle': None,
                'radius': None,
                'width': None,
                'height': None,
            }
            
            # Get light-specific properties
            if light_prim.IsA(UsdLux.SphereLight):
                light = UsdLux.SphereLight(light_prim)
                if light.GetRadiusAttr():
                    viz_data['radius'] = light.GetRadiusAttr().Get(time_code)
            
            elif light_prim.IsA(UsdLux.RectLight):
                light = UsdLux.RectLight(light_prim)
                if light.GetWidthAttr():
                    viz_data['width'] = light.GetWidthAttr().Get(time_code)
                if light.GetHeightAttr():
                    viz_data['height'] = light.GetHeightAttr().Get(time_code)
            
            elif light_prim.IsA(UsdLux.DiskLight):
                light = UsdLux.DiskLight(light_prim)
                if light.GetRadiusAttr():
                    viz_data['radius'] = light.GetRadiusAttr().Get(time_code)
            
            elif light_prim.IsA(UsdLux.CylinderLight):
                light = UsdLux.CylinderLight(light_prim)
                if light.GetRadiusAttr():
                    viz_data['radius'] = light.GetRadiusAttr().Get(time_code)
            
            # Get shaping (for spot lights)
            shaping_api = UsdLux.ShapingAPI(light_prim)
            if shaping_api:
                if shaping_api.GetShapingConeAngleAttr():
                    viz_data['cone_angle'] = shaping_api.GetShapingConeAngleAttr().Get(time_code)
            
            # Get intensity and color
            light_api = UsdLux.LightAPI(light_prim)
            if light_api:
                if light_api.GetIntensityAttr():
                    viz_data['intensity'] = light_api.GetIntensityAttr().Get(time_code) or 1.0
                if light_api.GetColorAttr():
                    color = light_api.GetColorAttr().Get(time_code)
                    if color:
                        viz_data['color'] = (color[0], color[1], color[2])
            
            return viz_data
        except Exception as e:
            print(f"Error getting light visualization: {e}")
            return None
    
    @staticmethod
    def get_all_lights_visualization(stage: Usd.Stage, time_code: float = 0.0) -> List[Dict]:
        """Get visualization data for all lights"""
        if not USD_AVAILABLE or not stage:
            return []
        
        lights = []
        for prim in stage.Traverse():
            if prim.IsA(UsdLux.Light):
                viz_data = LightVisualization.get_light_visualization_data(prim, time_code)
                if viz_data:
                    lights.append(viz_data)
        
        return lights

