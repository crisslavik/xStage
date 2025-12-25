"""
Scene Comparison/Diff
Compare two USD stages and highlight differences
"""

from typing import Dict, List, Optional, Set
from pxr import Usd, Sdf

try:
    from pxr import Usd, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class SceneDiff:
    """Represents differences between two stages"""
    
    def __init__(self):
        self.added_prims: List[str] = []
        self.removed_prims: List[str] = []
        self.modified_prims: List[str] = []
        self.added_attributes: Dict[str, List[str]] = {}  # prim_path -> [attr_names]
        self.removed_attributes: Dict[str, List[str]] = {}
        self.modified_attributes: Dict[str, List[str]] = {}
        self.different_values: Dict[str, Dict[str, tuple]] = {}  # prim_path -> {attr_name: (old, new)}


class SceneComparator:
    """Compares two USD stages"""
    
    def __init__(self, stage1: Usd.Stage, stage2: Usd.Stage):
        self.stage1 = stage1
        self.stage2 = stage2
    
    def compare(self) -> SceneDiff:
        """Compare two stages and return differences"""
        if not USD_AVAILABLE:
            return SceneDiff()
        
        diff = SceneDiff()
        
        # Get all prim paths from both stages
        paths1 = self._get_all_prim_paths(self.stage1)
        paths2 = self._get_all_prim_paths(self.stage2)
        
        # Find added and removed prims
        diff.added_prims = list(paths2 - paths1)
        diff.removed_prims = list(paths1 - paths2)
        
        # Find common prims and compare
        common_paths = paths1 & paths2
        for prim_path in common_paths:
            prim1 = self.stage1.GetPrimAtPath(prim_path)
            prim2 = self.stage2.GetPrimAtPath(prim_path)
            
            if prim1 and prim2:
                self._compare_prim(prim1, prim2, diff)
        
        return diff
    
    def _get_all_prim_paths(self, stage: Usd.Stage) -> Set[str]:
        """Get all prim paths from a stage"""
        paths = set()
        for prim in stage.Traverse():
            paths.add(prim.GetPath().pathString)
        return paths
    
    def _compare_prim(self, prim1: Usd.Prim, prim2: Usd.Prim, diff: SceneDiff):
        """Compare two prims"""
        prim_path = prim1.GetPath().pathString
        
        # Get attributes
        attrs1 = {attr.GetName(): attr for attr in prim1.GetAttributes()}
        attrs2 = {attr.GetName(): attr for attr in prim2.GetAttributes()}
        
        # Find added/removed attributes
        added_attrs = set(attrs2.keys()) - set(attrs1.keys())
        removed_attrs = set(attrs1.keys()) - set(attrs2.keys())
        
        if added_attrs:
            if prim_path not in diff.added_attributes:
                diff.added_attributes[prim_path] = []
            diff.added_attributes[prim_path].extend(added_attrs)
        
        if removed_attrs:
            if prim_path not in diff.removed_attributes:
                diff.removed_attributes[prim_path] = []
            diff.removed_attributes[prim_path].extend(removed_attrs)
        
        # Compare common attributes
        common_attrs = set(attrs1.keys()) & set(attrs2.keys())
        for attr_name in common_attrs:
            attr1 = attrs1[attr_name]
            attr2 = attrs2[attr_name]
            
            try:
                value1 = attr1.Get()
                value2 = attr2.Get()
                
                if value1 != value2:
                    if prim_path not in diff.modified_attributes:
                        diff.modified_attributes[prim_path] = []
                    diff.modified_attributes[prim_path].append(attr_name)
                    
                    if prim_path not in diff.different_values:
                        diff.different_values[prim_path] = {}
                    diff.different_values[prim_path][attr_name] = (value1, value2)
            except:
                pass
        
        # Check if prim type changed
        if prim1.GetTypeName() != prim2.GetTypeName():
            if prim_path not in diff.modified_prims:
                diff.modified_prims.append(prim_path)
    
    def get_diff_summary(self, diff: SceneDiff) -> str:
        """Get human-readable diff summary"""
        summary = []
        summary.append("Scene Comparison Summary:")
        summary.append(f"  Added prims: {len(diff.added_prims)}")
        summary.append(f"  Removed prims: {len(diff.removed_prims)}")
        summary.append(f"  Modified prims: {len(diff.modified_prims)}")
        summary.append(f"  Modified attributes: {sum(len(v) for v in diff.modified_attributes.values())}")
        return "\n".join(summary)

