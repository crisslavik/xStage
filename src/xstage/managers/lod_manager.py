"""
LOD (Level of Detail) Manager
Automatic LOD switching and management
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

try:
    from pxr import Usd, UsdGeom, Gf, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class LODMode(Enum):
    """LOD modes"""
    AUTO = "auto"  # Automatic based on distance
    MANUAL = "manual"  # Manual selection
    HIGH = "high"  # Always high detail
    MEDIUM = "medium"  # Always medium detail
    LOW = "low"  # Always low detail


@dataclass
class LODLevel:
    """LOD level definition"""
    name: str
    prim_path: str
    distance_threshold: float  # Distance at which to switch
    complexity: float  # 0.0 (low) to 1.0 (high)
    enabled: bool = True


class LODManager:
    """Manages LOD (Level of Detail) switching"""
    
    def __init__(self, stage: Optional[Usd.Stage] = None):
        self.stage = stage
        self.lod_mode = LODMode.AUTO
        self.lod_levels: Dict[str, List[LODLevel]] = {}  # prim_path -> LOD levels
        self.current_camera_position = Gf.Vec3d(0, 0, 0)
        self.current_lod_selections: Dict[str, str] = {}  # prim_path -> selected LOD
    
    def detect_lod_levels(self, prim_path: str) -> List[LODLevel]:
        """Detect LOD levels for a prim"""
        if not self.stage or not USD_AVAILABLE:
            return []
        
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim:
            return []
        
        lod_levels = []
        
        # Check for UsdGeom.Imageable LOD variants
        # Look for variant sets that might contain LOD
        variant_sets = prim.GetVariantSets()
        variant_set_names = variant_sets.GetNames()
        
        for variant_set_name in variant_set_names:
            if 'lod' in variant_set_name.lower() or 'detail' in variant_set_name.lower():
                variant_set = variant_sets.GetVariantSet(variant_set_name)
                variant_names = variant_set.GetVariantNames()
                
                for i, variant_name in enumerate(variant_names):
                    # Try to determine LOD level from name
                    if 'high' in variant_name.lower() or 'detail' in variant_name.lower():
                        complexity = 1.0
                        distance = 0.0
                    elif 'medium' in variant_name.lower() or 'mid' in variant_name.lower():
                        complexity = 0.5
                        distance = 50.0
                    elif 'low' in variant_name.lower() or 'proxy' in variant_name.lower():
                        complexity = 0.25
                        distance = 100.0
                    else:
                        complexity = 1.0 - (i / max(len(variant_names), 1))
                        distance = i * 50.0
                    
                    lod_level = LODLevel(
                        name=variant_name,
                        prim_path=prim_path,
                        distance_threshold=distance,
                        complexity=complexity
                    )
                    lod_levels.append(lod_level)
        
        # Check for explicit LOD prims (children with LOD in name)
        for child in prim.GetChildren():
            child_name = child.GetName().lower()
            if 'lod' in child_name or 'detail' in child_name:
                # Determine LOD level from name
                if 'high' in child_name:
                    complexity = 1.0
                    distance = 0.0
                elif 'medium' in child_name or 'mid' in child_name:
                    complexity = 0.5
                    distance = 50.0
                elif 'low' in child_name or 'proxy' in child_name:
                    complexity = 0.25
                    distance = 100.0
                else:
                    complexity = 0.5
                    distance = 50.0
                
                lod_level = LODLevel(
                    name=child.GetName(),
                    prim_path=str(child.GetPath()),
                    distance_threshold=distance,
                    complexity=complexity
                )
                lod_levels.append(lod_level)
        
        if lod_levels:
            self.lod_levels[prim_path] = lod_levels
        
        return lod_levels
    
    def set_camera_position(self, position: Gf.Vec3d):
        """Update camera position for LOD calculation"""
        self.current_camera_position = position
        if self.lod_mode == LODMode.AUTO:
            self.update_lod_selections()
    
    def calculate_distance(self, prim_path: str) -> float:
        """Calculate distance from camera to prim"""
        if not self.stage or not USD_AVAILABLE:
            return 0.0
        
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim:
            return 0.0
        
        # Get prim's world transform
        xformable = UsdGeom.Xformable(prim)
        if xformable:
            transform = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
            prim_position = Gf.Vec3d(transform.ExtractTranslation())
            
            # Calculate distance
            distance_vec = prim_position - self.current_camera_position
            return distance_vec.GetLength()
        
        return 0.0
    
    def select_lod_for_prim(self, prim_path: str, distance: Optional[float] = None) -> Optional[str]:
        """Select appropriate LOD level for prim based on distance"""
        if prim_path not in self.lod_levels:
            return None
        
        lod_levels = self.lod_levels[prim_path]
        if not lod_levels:
            return None
        
        if distance is None:
            distance = self.calculate_distance(prim_path)
        
        # Find appropriate LOD level
        selected_lod = None
        for lod_level in sorted(lod_levels, key=lambda x: x.distance_threshold, reverse=True):
            if distance >= lod_level.distance_threshold and lod_level.enabled:
                selected_lod = lod_level.name
                break
        
        # If no LOD found, use highest detail
        if not selected_lod and lod_levels:
            selected_lod = lod_levels[0].name
        
        return selected_lod
    
    def update_lod_selections(self):
        """Update LOD selections for all prims with LOD"""
        for prim_path in self.lod_levels.keys():
            selected_lod = self.select_lod_for_prim(prim_path)
            if selected_lod:
                self.current_lod_selections[prim_path] = selected_lod
    
    def apply_lod_selection(self, prim_path: str, lod_name: str) -> bool:
        """Apply LOD selection to prim"""
        if not self.stage or not USD_AVAILABLE:
            return False
        
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim:
            return False
        
        # Try to set variant selection
        variant_sets = prim.GetVariantSets()
        variant_set_names = variant_sets.GetNames()
        
        for variant_set_name in variant_set_names:
            if 'lod' in variant_set_name.lower() or 'detail' in variant_set_name.lower():
                variant_set = variant_sets.GetVariantSet(variant_set_name)
                if lod_name in variant_set.GetVariantNames():
                    variant_set.SetVariantSelection(lod_name)
                    self.current_lod_selections[prim_path] = lod_name
                    return True
        
        return False
    
    def get_lod_statistics(self) -> Dict[str, any]:
        """Get LOD statistics"""
        total_prims_with_lod = len(self.lod_levels)
        total_lod_levels = sum(len(levels) for levels in self.lod_levels.values())
        
        return {
            'prims_with_lod': total_prims_with_lod,
            'total_lod_levels': total_lod_levels,
            'current_selections': len(self.current_lod_selections),
            'mode': self.lod_mode.value,
        }

