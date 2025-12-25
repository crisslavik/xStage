"""
Scene Graph Search & Filter
Search and filter prims by name, type, path, metadata, etc.
"""

from typing import Optional, List, Dict, Callable
from pxr import Usd, UsdGeom

try:
    from pxr import Usd, UsdGeom
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class SceneSearchManager:
    """Manages scene graph search and filtering"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
    
    def search_prims(self, query: str, search_type: str = "name") -> List[Usd.Prim]:
        """
        Search for prims
        
        Args:
            query: Search query string
            search_type: Type of search ("name", "path", "type", "all")
        """
        if not USD_AVAILABLE or not self.stage:
            return []
        
        results = []
        query_lower = query.lower()
        
        for prim in self.stage.Traverse():
            match = False
            
            if search_type in ("name", "all"):
                if query_lower in prim.GetName().lower():
                    match = True
            
            if search_type in ("path", "all") and not match:
                if query_lower in prim.GetPath().pathString.lower():
                    match = True
            
            if search_type in ("type", "all") and not match:
                if query_lower in prim.GetTypeName().lower():
                    match = True
            
            if match:
                results.append(prim)
        
        return results
    
    def filter_by_type(self, prim_type: str) -> List[Usd.Prim]:
        """Filter prims by type"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        results = []
        for prim in self.stage.Traverse():
            if prim.GetTypeName() == prim_type:
                results.append(prim)
        return results
    
    def filter_by_metadata(self, key: str, value: str = None) -> List[Usd.Prim]:
        """Filter prims by metadata"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        results = []
        for prim in self.stage.Traverse():
            if prim.HasMetadata(key):
                if value is None:
                    results.append(prim)
                else:
                    metadata_value = prim.GetMetadata(key)
                    if str(metadata_value).lower() == value.lower():
                        results.append(prim)
        return results
    
    def filter_by_variant(self, variant_set: str, variant: str) -> List[Usd.Prim]:
        """Filter prims by variant selection"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        results = []
        for prim in self.stage.Traverse():
            variant_sets = prim.GetVariantSets()
            if variant_sets.HasVariantSet(variant_set):
                variant_set_obj = variant_sets.GetVariantSet(variant_set)
                if variant_set_obj.GetVariantSelection() == variant:
                    results.append(prim)
        return results
    
    def filter_by_custom(self, filter_func: Callable[[Usd.Prim], bool]) -> List[Usd.Prim]:
        """Filter prims using a custom function"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        results = []
        for prim in self.stage.Traverse():
            if filter_func(prim):
                results.append(prim)
        return results
    
    def get_prim_types(self) -> List[str]:
        """Get all unique prim types in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        types = set()
        for prim in self.stage.Traverse():
            types.add(prim.GetTypeName())
        return sorted(list(types))
    
    def get_metadata_keys(self) -> List[str]:
        """Get all unique metadata keys in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        keys = set()
        for prim in self.stage.Traverse():
            for key in prim.GetAllMetadata():
                keys.add(key)
        return sorted(list(keys))

