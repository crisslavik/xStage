"""
UsdLux Lighting Support for xStage
Implements modern USD lighting system using UsdLux schemas
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
import numpy as np

try:
    from pxr import Usd, UsdGeom, Gf, UsdLux, UsdShade
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class UsdLuxExtractor:
    """Extract lighting data from USD stage using UsdLux schemas"""
    
    @staticmethod
    def extract_light(prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """
        Extract light data from a UsdLux prim
        
        Supports all UsdLux light types:
        - DistantLight, SphereLight, RectLight, DiskLight
        - CylinderLight, DomeLight, PortalLight
        - GeometryLight, PluginLight
        """
        if not USD_AVAILABLE:
            return None
            
        if not prim.IsA(UsdLux.Light):
            return None
            
        # Get common light properties
        xformable = UsdGeom.Xformable(prim)
        transform = xformable.ComputeLocalToWorldTransform(time_code)
        
        # Base light API
        light_api = UsdLux.LightAPI(prim)
        
        light_data = {
            'name': prim.GetPath().pathString,
            'type': prim.GetTypeName(),
            'transform': np.array(transform, dtype=np.float32).reshape(4, 4),
            'intensity': 1.0,
            'color': (1.0, 1.0, 1.0),
            'exposure': 0.0,
            'enable_color_temperature': False,
            'color_temperature': 6500.0,
            'diffuse': 1.0,
            'specular': 1.0,
            'normalize': False,
            'light_type': None,
            'specific_properties': {}
        }
        
        # Get common attributes
        if light_api.GetIntensityAttr():
            light_data['intensity'] = light_api.GetIntensityAttr().Get(time_code) or 1.0
            
        if light_api.GetColorAttr():
            color = light_api.GetColorAttr().Get(time_code)
            if color:
                light_data['color'] = (color[0], color[1], color[2])
                
        if light_api.GetExposureAttr():
            light_data['exposure'] = light_api.GetExposureAttr().Get(time_code) or 0.0
            
        if light_api.GetEnableColorTemperatureAttr():
            light_data['enable_color_temperature'] = (
                light_api.GetEnableColorTemperatureAttr().Get(time_code) or False
            )
            
        if light_api.GetColorTemperatureAttr():
            light_data['color_temperature'] = (
                light_api.GetColorTemperatureAttr().Get(time_code) or 6500.0
            )
            
        if light_api.GetDiffuseAttr():
            light_data['diffuse'] = light_api.GetDiffuseAttr().Get(time_code) or 1.0
            
        if light_api.GetSpecularAttr():
            light_data['specular'] = light_api.GetSpecularAttr().Get(time_code) or 1.0
            
        if light_api.GetNormalizeAttr():
            light_data['normalize'] = light_api.GetNormalizeAttr().Get(time_code) or False
        
        # Extract type-specific properties
        if prim.IsA(UsdLux.DistantLight):
            light_data['light_type'] = 'distant'
            light_data['specific_properties'] = UsdLuxExtractor._extract_distant_light(
                prim, time_code
            )
            
        elif prim.IsA(UsdLux.SphereLight):
            light_data['light_type'] = 'sphere'
            light_data['specific_properties'] = UsdLuxExtractor._extract_sphere_light(
                prim, time_code
            )
            
        elif prim.IsA(UsdLux.RectLight):
            light_data['light_type'] = 'rect'
            light_data['specific_properties'] = UsdLuxExtractor._extract_rect_light(
                prim, time_code
            )
            
        elif prim.IsA(UsdLux.DiskLight):
            light_data['light_type'] = 'disk'
            light_data['specific_properties'] = UsdLuxExtractor._extract_disk_light(
                prim, time_code
            )
            
        elif prim.IsA(UsdLux.CylinderLight):
            light_data['light_type'] = 'cylinder'
            light_data['specific_properties'] = UsdLuxExtractor._extract_cylinder_light(
                prim, time_code
            )
            
        elif prim.IsA(UsdLux.DomeLight):
            light_data['light_type'] = 'dome'
            light_data['specific_properties'] = UsdLuxExtractor._extract_dome_light(
                prim, time_code
            )
            
        elif prim.IsA(UsdLux.PortalLight):
            light_data['light_type'] = 'portal'
            light_data['specific_properties'] = UsdLuxExtractor._extract_portal_light(
                prim, time_code
            )
            
        elif prim.IsA(UsdLux.GeometryLight):
            light_data['light_type'] = 'geometry'
            light_data['specific_properties'] = UsdLuxExtractor._extract_geometry_light(
                prim, time_code
            )
            
        # Extract shadow properties
        shadow_api = UsdLux.ShadowAPI(prim)
        if shadow_api:
            light_data['shadow'] = {
                'enabled': shadow_api.GetShadowEnableAttr().Get(time_code) if shadow_api.GetShadowEnableAttr() else True,
                'color': shadow_api.GetShadowColorAttr().Get(time_code) if shadow_api.GetShadowColorAttr() else (0.0, 0.0, 0.0),
                'distance': shadow_api.GetShadowDistanceAttr().Get(time_code) if shadow_api.GetShadowDistanceAttr() else -1.0,
                'falloff': shadow_api.GetShadowFalloffAttr().Get(time_code) if shadow_api.GetShadowFalloffAttr() else -1.0,
            }
        else:
            light_data['shadow'] = None
            
        # Extract shaping properties (for spot/rect lights)
        shaping_api = UsdLux.ShapingAPI(prim)
        if shaping_api:
            light_data['shaping'] = {
                'shaping_focus': shaping_api.GetShapingFocusAttr().Get(time_code) if shaping_api.GetShapingFocusAttr() else 0.0,
                'shaping_focus_tint': shaping_api.GetShapingFocusTintAttr().Get(time_code) if shaping_api.GetShapingFocusTintAttr() else (0.0, 0.0, 0.0),
                'shaping_cone_angle': shaping_api.GetShapingConeAngleAttr().Get(time_code) if shaping_api.GetShapingConeAngleAttr() else 90.0,
                'shaping_cone_softness': shaping_api.GetShapingConeSoftnessAttr().Get(time_code) if shaping_api.GetShapingConeSoftnessAttr() else 0.0,
                'shaping_ies_angle_scale': shaping_api.GetShapingIesAngleScaleAttr().Get(time_code) if shaping_api.GetShapingIesAngleScaleAttr() else 0.0,
                'shaping_ies_file': shaping_api.GetShapingIesFileAttr().Get(time_code) if shaping_api.GetShapingIesFileAttr() else None,
                'shaping_ies_normalize': shaping_api.GetShapingIesNormalizeAttr().Get(time_code) if shaping_api.GetShapingIesNormalizeAttr() else False,
            }
        else:
            light_data['shaping'] = None
            
        # Extract light-linking
        light_list_api = UsdLux.LightListAPI(prim)
        if light_list_api:
            light_data['light_linking'] = {
                'light_filter_link': light_list_api.GetLightFilterLinkRel().GetTargets() if light_list_api.GetLightFilterLinkRel() else [],
            }
        else:
            light_data['light_linking'] = None
            
        return light_data
    
    @staticmethod
    def _extract_distant_light(prim: Usd.Prim, time_code: float) -> Dict:
        """Extract DistantLight specific properties"""
        light = UsdLux.DistantLight(prim)
        return {
            'angle': light.GetAngleAttr().Get(time_code) if light.GetAngleAttr() else 0.53,
        }
    
    @staticmethod
    def _extract_sphere_light(prim: Usd.Prim, time_code: float) -> Dict:
        """Extract SphereLight specific properties"""
        light = UsdLux.SphereLight(prim)
        return {
            'radius': light.GetRadiusAttr().Get(time_code) if light.GetRadiusAttr() else 0.5,
            'treat_as_point': light.GetTreatAsPointAttr().Get(time_code) if light.GetTreatAsPointAttr() else False,
        }
    
    @staticmethod
    def _extract_rect_light(prim: Usd.Prim, time_code: float) -> Dict:
        """Extract RectLight specific properties"""
        light = UsdLux.RectLight(prim)
        return {
            'width': light.GetWidthAttr().Get(time_code) if light.GetWidthAttr() else 1.0,
            'height': light.GetHeightAttr().Get(time_code) if light.GetHeightAttr() else 1.0,
            'texture_file': light.GetTextureFileAttr().Get(time_code) if light.GetTextureFileAttr() else None,
        }
    
    @staticmethod
    def _extract_disk_light(prim: Usd.Prim, time_code: float) -> Dict:
        """Extract DiskLight specific properties"""
        light = UsdLux.DiskLight(prim)
        return {
            'radius': light.GetRadiusAttr().Get(time_code) if light.GetRadiusAttr() else 0.5,
        }
    
    @staticmethod
    def _extract_cylinder_light(prim: Usd.Prim, time_code: float) -> Dict:
        """Extract CylinderLight specific properties"""
        light = UsdLux.CylinderLight(prim)
        return {
            'length': light.GetLengthAttr().Get(time_code) if light.GetLengthAttr() else 1.0,
            'radius': light.GetRadiusAttr().Get(time_code) if light.GetRadiusAttr() else 0.5,
            'treat_as_line': light.GetTreatAsLineAttr().Get(time_code) if light.GetTreatAsLineAttr() else False,
        }
    
    @staticmethod
    def _extract_dome_light(prim: Usd.Prim, time_code: float) -> Dict:
        """Extract DomeLight specific properties"""
        light = UsdLux.DomeLight(prim)
        return {
            'texture_file': light.GetTextureFileAttr().Get(time_code) if light.GetTextureFileAttr() else None,
            'texture_format': light.GetTextureFormatAttr().Get(time_code) if light.GetTextureFormatAttr() else 'automatic',
            'portals': light.GetPortalsRel().GetTargets() if light.GetPortalsRel() else [],
        }
    
    @staticmethod
    def _extract_portal_light(prim: Usd.Prim, time_code: float) -> Dict:
        """Extract PortalLight specific properties"""
        light = UsdLux.PortalLight(prim)
        return {
            'width': light.GetWidthAttr().Get(time_code) if light.GetWidthAttr() else 1.0,
            'height': light.GetHeightAttr().Get(time_code) if light.GetHeightAttr() else 1.0,
        }
    
    @staticmethod
    def _extract_geometry_light(prim: Usd.Prim, time_code: float) -> Dict:
        """Extract GeometryLight specific properties"""
        light = UsdLux.GeometryLight(prim)
        return {
            'geometry_rel': light.GetGeometryRel().GetTargets() if light.GetGeometryRel() else [],
        }
    
    @staticmethod
    def find_all_lights(stage: Usd.Stage) -> List[Usd.Prim]:
        """Find all UsdLux lights in the stage"""
        if not USD_AVAILABLE:
            return []
            
        lights = []
        for prim in stage.Traverse():
            if prim.IsA(UsdLux.Light):
                lights.append(prim)
        return lights


def update_stage_manager_for_usd_lux(stage_manager):
    """
    Example function to update USDStageManager to use UsdLux
    
    Usage:
        # In USDStageManager._extract_light():
        # Replace:
        # elif prim.IsA(UsdGeom.Light):
        # With:
        elif prim.IsA(UsdLux.Light):
            light_data = UsdLuxExtractor.extract_light(prim, time_code)
            if light_data:
                geometry_data['lights'].append(light_data)
    """
    pass

