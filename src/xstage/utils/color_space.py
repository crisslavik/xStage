"""
USD Color Space Support
Handles color space schemas and color space inheritance
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict
from pxr import Usd, UsdLux

try:
    from pxr import Usd, UsdLux
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class ColorSpaceManager:
    """Manages USD color spaces"""
    
    @staticmethod
    def get_color_space(prim: Usd.Prim) -> Optional[Dict]:
        """Get color space information for a prim"""
        if not USD_AVAILABLE:
            return None
        
        try:
            color_space_api = UsdLux.ColorSpaceAPI(prim)
            if not color_space_api:
                return None
            
            color_space_data = {
                'prim_path': prim.GetPath().pathString,
                'color_space': None,
                'inherited_color_space': None,
            }
            
            # Get explicit color space
            if color_space_api.GetColorSpaceAttr():
                color_space_data['color_space'] = color_space_api.GetColorSpaceAttr().Get()
            
            # Get inherited color space
            if color_space_api.GetInheritedColorSpaceAttr():
                color_space_data['inherited_color_space'] = color_space_api.GetInheritedColorSpaceAttr().Get()
            
            return color_space_data if color_space_data['color_space'] or color_space_data['inherited_color_space'] else None
        except Exception as e:
            print(f"Error getting color space: {e}")
            return None
    
    @staticmethod
    def set_color_space(prim: Usd.Prim, color_space: str) -> bool:
        """Set color space for a prim"""
        if not USD_AVAILABLE:
            return False
        
        try:
            color_space_api = UsdLux.ColorSpaceAPI.Apply(prim)
            if color_space_api:
                color_space_api.CreateColorSpaceAttr().Set(color_space)
                return True
        except Exception as e:
            print(f"Error setting color space: {e}")
            return False
        
        return False
    
    @staticmethod
    def get_default_color_space(stage: Usd.Stage) -> Optional[str]:
        """Get the default color space for a stage"""
        if not USD_AVAILABLE:
            return None
        
        try:
            root_prim = stage.GetPseudoRoot()
            color_space_api = UsdLux.ColorSpaceAPI(root_prim)
            if color_space_api and color_space_api.GetColorSpaceAttr():
                return color_space_api.GetColorSpaceAttr().Get()
        except Exception as e:
            print(f"Error getting default color space: {e}")
        
        return None

