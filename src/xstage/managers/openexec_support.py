"""
OpenExec Integration
Support for computed attributes and extent calculations
Based on OpenUSD 25.08+ OpenExec framework
"""

from typing import Optional, Dict, List, Any
from pxr import Usd, UsdGeom, Gf

try:
    from pxr import Usd, UsdGeom, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False

# Try to import OpenExec (available in USD 25.08+)
try:
    from pxr import UsdExec
    OPENEXEC_AVAILABLE = True
except ImportError:
    OPENEXEC_AVAILABLE = False
    UsdExec = None


class OpenExecManager:
    """Manages OpenExec computed attributes and extent calculations"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
        self.openexec_available = OPENEXEC_AVAILABLE and USD_AVAILABLE
    
    def is_computed_attribute(self, prim: Usd.Prim, attr_name: str) -> bool:
        """Check if an attribute is computed via OpenExec"""
        if not self.openexec_available or not prim:
            return False
        
        try:
            attr = prim.GetAttribute(attr_name)
            if not attr:
                return False
            
            # Check if attribute has OpenExec computation
            # In USD 25.08+, computed attributes are marked differently
            # We can check if the attribute has a computed value source
            
            # Method 1: Check if attribute is computed (not authored)
            if not attr.HasAuthoredValue():
                # Could be computed, but need to check if OpenExec is involved
                pass
            
            # Method 2: Check for OpenExec schema
            # OpenExec uses UsdExec schemas for computed attributes
            if UsdExec:
                # Check if prim has UsdExec schema
                exec_schema = UsdExec.ComputedAttribute(prim)
                if exec_schema:
                    # Check if this attribute is in the computed attributes
                    pass
            
            # For now, we'll use a heuristic: if extent is not authored but can be computed
            if attr_name == "extent" and prim.IsA(UsdGeom.Boundable):
                # Extent can be computed from geometry
                if not attr.HasAuthoredValue():
                    return True
            
            return False
        except Exception as e:
            print(f"Error checking computed attribute: {e}")
            return False
    
    def compute_extent(self, prim: Usd.Prim, time_code: float = 0.0) -> Optional[List]:
        """Compute extent for a boundable prim"""
        if not USD_AVAILABLE or not prim:
            return None
        
        try:
            boundable = UsdGeom.Boundable(prim)
            if not boundable:
                return None
            
            # Use UsdGeom to compute extent
            # This is the standard way to compute extent in USD
            bbox_cache = UsdGeom.BBoxCache(time_code, includedPurposes=[UsdGeom.Tokens.default_])
            bbox = bbox_cache.ComputeWorldBound(prim)
            
            if bbox:
                # Get the bounding box
                range = bbox.ComputeAlignedRange()
                min_point = range.GetMin()
                max_point = range.GetMax()
                
                return [
                    [min_point[0], min_point[1], min_point[2]],
                    [max_point[0], max_point[1], max_point[2]]
                ]
        except Exception as e:
            print(f"Error computing extent: {e}")
            return None
        
        return None
    
    def get_computed_value(self, prim: Usd.Prim, attr_name: str, time_code: float = 0.0) -> Any:
        """Get computed value for an attribute"""
        if not USD_AVAILABLE or not prim:
            return None
        
        try:
            # Special handling for extent
            if attr_name == "extent":
                return self.compute_extent(prim, time_code)
            
            # For other computed attributes, try to get the value
            # USD will evaluate computed attributes when accessed
            attr = prim.GetAttribute(attr_name)
            if attr:
                try:
                    return attr.Get(time_code)
                except:
                    # If Get fails, it might be computed
                    # Try to evaluate it
                    pass
            
            return None
        except Exception as e:
            print(f"Error getting computed value: {e}")
            return None
    
    def get_all_computed_attributes(self, prim: Usd.Prim) -> List[str]:
        """Get list of computed attributes on a prim"""
        if not USD_AVAILABLE or not prim:
            return []
        
        computed = []
        
        # Check common computed attributes
        if prim.IsA(UsdGeom.Boundable):
            extent_attr = prim.GetAttribute("extent")
            if extent_attr and not extent_attr.HasAuthoredValue():
                # Extent can be computed
                computed.append("extent")
        
        # Check for OpenExec computed attributes
        if self.openexec_available and UsdExec:
            try:
                exec_schema = UsdExec.ComputedAttribute(prim)
                if exec_schema:
                    # Get computed attribute names from OpenExec
                    # This depends on the OpenExec API
                    pass
            except:
                pass
        
        return computed
    
    def ensure_extent(self, prim: Usd.Prim, time_code: float = 0.0) -> bool:
        """Ensure extent is computed and set on a prim"""
        if not USD_AVAILABLE or not prim:
            return False
        
        try:
            boundable = UsdGeom.Boundable(prim)
            if not boundable:
                return False
            
            # Check if extent is already authored
            extent_attr = boundable.GetExtentAttr()
            if extent_attr.HasAuthoredValue():
                return True  # Already has extent
            
            # Compute extent
            extent = self.compute_extent(prim, time_code)
            if extent:
                extent_attr.Set(extent, time_code)
                return True
        except Exception as e:
            print(f"Error ensuring extent: {e}")
            return False
        
        return False
    
    def compute_all_extents(self, time_code: float = 0.0, progress_callback=None) -> Dict[str, bool]:
        """Compute extents for all boundable prims in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return {}
        
        results = {}
        boundable_prims = []
        
        # Collect all boundable prims
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Boundable):
                boundable_prims.append(prim)
        
        total = len(boundable_prims)
        
        for i, prim in enumerate(boundable_prims):
            if progress_callback:
                progress = int((i / total) * 100) if total > 0 else 0
                progress_callback(progress, f"Computing extent for {prim.GetPath()}")
            
            prim_path = prim.GetPath().pathString
            results[prim_path] = self.ensure_extent(prim, time_code)
        
        return results
    
    def get_computed_attribute_info(self, prim: Usd.Prim, attr_name: str) -> Dict:
        """Get information about a computed attribute"""
        if not USD_AVAILABLE or not prim:
            return {}
        
        info = {
            'name': attr_name,
            'is_computed': self.is_computed_attribute(prim, attr_name),
            'has_authored_value': False,
            'can_compute': False,
            'computed_value': None,
        }
        
        try:
            attr = prim.GetAttribute(attr_name)
            if attr:
                info['has_authored_value'] = attr.HasAuthoredValue()
                info['can_compute'] = not attr.HasAuthoredValue()
                
                # Try to get computed value
                if info['can_compute']:
                    info['computed_value'] = self.get_computed_value(prim, attr_name)
        except:
            pass
        
        return info

