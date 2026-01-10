"""
Light Linking Manager
Manages light linking relationships between lights and objects
Based on USD 25.11+ UsdLux.LightListAPI specifications
"""

from typing import Optional, List, Dict

try:
    from pxr import Usd, UsdLux
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False

# Import version detection
try:
    from ..utils.usd_version import USD_AVAILABLE as USD_VERSION_AVAILABLE, check_feature
    LIGHT_LINKING_AVAILABLE = check_feature('light_linking')
except ImportError:
    LIGHT_LINKING_AVAILABLE = False


class LightLinkingManager:
    """Manages light linking relationships"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
    
    def get_light_links(self, light_prim: Usd.Prim) -> List[str]:
        """
        Get list of prims linked to a light
        
        Args:
            light_prim: Light prim to check
        
        Returns:
            List of prim paths linked to this light
        """
        if not USD_AVAILABLE or not light_prim or not LIGHT_LINKING_AVAILABLE:
            return []
        
        try:
            light_list_api = UsdLux.LightListAPI(light_prim)
            if light_list_api:
                # Get light filter links (objects affected by light)
                filter_link_rel = light_list_api.GetLightFilterLinkRel()
                if filter_link_rel:
                    targets = filter_link_rel.GetTargets()
                    return [str(target) for target in targets]
        except Exception as e:
            print(f"Error getting light links: {e}")
        
        return []
    
    def set_light_link(self, light_prim: Usd.Prim, target_prim_path: str, enable: bool = True) -> bool:
        """
        Add or remove a light link
        
        Args:
            light_prim: Light prim
            target_prim_path: Path of prim to link/unlink
            enable: True to link, False to unlink
        
        Returns:
            True if successful
        """
        if not USD_AVAILABLE or not light_prim:
            return False
        
        try:
            light_list_api = UsdLux.LightListAPI(light_prim)
            if not light_list_api:
                return False
            
            filter_link_rel = light_list_api.GetLightFilterLinkRel()
            if not filter_link_rel:
                return False
            
            target_path = Usd.Prim.GetPath(target_prim_path) if isinstance(target_prim_path, str) else target_prim_path
            
            if enable:
                # Add link
                current_targets = filter_link_rel.GetTargets()
                if target_path not in current_targets:
                    filter_link_rel.AddTarget(target_path)
            else:
                # Remove link
                filter_link_rel.RemoveTarget(target_path)
            
            return True
        except Exception as e:
            print(f"Error setting light link: {e}")
            return False
    
    def get_all_light_links(self) -> Dict[str, List[str]]:
        """
        Get all light links in the stage
        
        Returns:
            Dictionary mapping light paths to lists of linked prim paths
        """
        if not USD_AVAILABLE or not self.stage:
            return {}
        
        light_links = {}
        
        try:
            # Find all lights
            for prim in self.stage.Traverse():
                if prim.IsA(UsdLux.Light):
                    light_path = str(prim.GetPath())
                    links = self.get_light_links(prim)
                    if links:
                        light_links[light_path] = links
        except Exception as e:
            print(f"Error getting all light links: {e}")
        
        return light_links
    
    def get_prims_affected_by_light(self, light_prim: Usd.Prim) -> List[Usd.Prim]:
        """
        Get all prims affected by a light (via light linking)
        
        Args:
            light_prim: Light prim to check
        
        Returns:
            List of prims affected by this light
        """
        if not USD_AVAILABLE or not light_prim or not self.stage:
            return []
        
        linked_paths = self.get_light_links(light_prim)
        affected_prims = []
        
        for path_str in linked_paths:
            prim = self.stage.GetPrimAtPath(path_str)
            if prim:
                affected_prims.append(prim)
        
        return affected_prims
    
    def clear_light_links(self, light_prim: Usd.Prim) -> bool:
        """
        Clear all light links for a light
        
        Args:
            light_prim: Light prim
        
        Returns:
            True if successful
        """
        if not USD_AVAILABLE or not light_prim:
            return False
        
        try:
            light_list_api = UsdLux.LightListAPI(light_prim)
            if not light_list_api:
                return False
            
            filter_link_rel = light_list_api.GetLightFilterLinkRel()
            if not filter_link_rel:
                return False
            
            # Clear all targets
            current_targets = filter_link_rel.GetTargets()
            for target in current_targets:
                filter_link_rel.RemoveTarget(target)
            
            return True
        except Exception as e:
            print(f"Error clearing light links: {e}")
            return False

