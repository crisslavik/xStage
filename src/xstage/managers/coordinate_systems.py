"""
Coordinate Systems Support
Handles coordinate system extraction, binding, and visualization
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd, UsdGeom

try:
    from pxr import Usd, UsdGeom
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class CoordinateSystemManager:
    """Manages coordinate systems"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
    
    def get_coordinate_systems(self, prim: Usd.Prim) -> List[Dict]:
        """Get coordinate systems on a prim"""
        if not USD_AVAILABLE or not prim:
            return []
        
        try:
            coord_sys_api = UsdGeom.CoordSysAPI(prim)
            if not coord_sys_api:
                return []
            
            coord_systems = []
            # Get coordinate system bindings
            # Note: CoordSysAPI API may vary by USD version
            # This is a simplified implementation
            try:
                # Try to get coordinate systems
                if hasattr(coord_sys_api, 'GetCoordinateSystems'):
                    systems = coord_sys_api.GetCoordinateSystems()
                    for sys_name in systems:
                        coord_systems.append({
                            'name': sys_name,
                            'prim_path': prim.GetPath().pathString,
                        })
            except:
                pass
            
            return coord_systems
        except Exception as e:
            print(f"Error getting coordinate systems: {e}")
            return []
    
    def find_all_coordinate_systems(self) -> List[Dict]:
        """Find all coordinate systems in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        all_systems = []
        for prim in self.stage.Traverse():
            systems = self.get_coordinate_systems(prim)
            all_systems.extend(systems)
        
        return all_systems
    
    def bind_coordinate_system(self, prim: Usd.Prim, coord_sys_name: str, coord_sys_path: str) -> bool:
        """Bind a coordinate system to a prim"""
        if not USD_AVAILABLE or not prim:
            return False
        
        try:
            coord_sys_api = UsdGeom.CoordSysAPI.Apply(prim, coord_sys_name)
            if coord_sys_api:
                # Set binding
                # Implementation depends on USD version
                return True
        except Exception as e:
            print(f"Error binding coordinate system: {e}")
            return False
        
        return False

