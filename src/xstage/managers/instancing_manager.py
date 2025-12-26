"""
Instancing Optimization Manager
Instance visualization, management, and optimization
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

try:
    from pxr import Usd, UsdGeom, Gf, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class InstanceMode(Enum):
    """Instance visualization modes"""
    FULL = "full"  # Show all instances
    BOUNDING_BOX = "bounding_box"  # Show only bounding boxes
    HIDDEN = "hidden"  # Hide instances
    FIRST_ONLY = "first_only"  # Show only first instance


@dataclass
class InstanceInfo:
    """Information about an instance"""
    master_path: str
    instance_paths: List[str]
    instance_count: int
    memory_savings_mb: float = 0.0
    enabled: bool = True


class InstancingManager:
    """Manages USD instancing for performance optimization"""
    
    def __init__(self, stage: Optional[Usd.Stage] = None):
        self.stage = stage
        self.instance_mode = InstanceMode.FULL
        self.instance_info: Dict[str, InstanceInfo] = {}
        self.hidden_instances: Set[str] = set()
    
    def detect_instances(self) -> Dict[str, InstanceInfo]:
        """Detect all instances in the stage"""
        if not self.stage or not USD_AVAILABLE:
            return {}
        
        self.instance_info.clear()
        
        # Traverse stage and find instanceable prims
        for prim in self.stage.Traverse():
            if prim.IsInstanceable():
                master = prim.GetMaster()
                if master:
                    master_path = str(master.GetPath())
                    
                    if master_path not in self.instance_info:
                        # Find all instances of this master
                        instance_paths = []
                        for instance_prim in self.stage.Traverse():
                            if instance_prim.IsInstance() and instance_prim.GetMaster() == master:
                                instance_paths.append(str(instance_prim.GetPath()))
                        
                        instance_info = InstanceInfo(
                            master_path=master_path,
                            instance_paths=instance_paths,
                            instance_count=len(instance_paths)
                        )
                        
                        # Estimate memory savings
                        instance_info.memory_savings_mb = self._estimate_memory_savings(master, len(instance_paths))
                        
                        self.instance_info[master_path] = instance_info
        
        return self.instance_info
    
    def _estimate_memory_savings(self, master: Usd.Prim, instance_count: int) -> float:
        """Estimate memory savings from instancing"""
        if instance_count <= 1:
            return 0.0
        
        # Rough estimate: assume each instance would take ~1MB if not instanced
        # With instancing, only master is stored
        estimated_savings = (instance_count - 1) * 1.0  # MB
        return estimated_savings
    
    def get_instance_statistics(self) -> Dict[str, any]:
        """Get instancing statistics"""
        total_instances = sum(info.instance_count for info in self.instance_info.values())
        total_masters = len(self.instance_info)
        total_savings = sum(info.memory_savings_mb for info in self.instance_info.values())
        
        return {
            'total_masters': total_masters,
            'total_instances': total_instances,
            'estimated_memory_savings_mb': total_savings,
            'average_instances_per_master': total_instances / max(total_masters, 1),
            'mode': self.instance_mode.value,
        }
    
    def convert_to_instances(self, prim_paths: List[str]) -> bool:
        """Convert prims to instances (optimization)"""
        if not self.stage or not USD_AVAILABLE:
            return False
        
        # Group prims by similarity (same type, similar structure)
        # This is a simplified version - real implementation would be more sophisticated
        prim_groups: Dict[str, List[str]] = {}
        
        for prim_path in prim_paths:
            prim = self.stage.GetPrimAtPath(prim_path)
            if not prim:
                continue
            
            # Use type name as grouping key (simplified)
            type_name = prim.GetTypeName()
            if type_name not in prim_groups:
                prim_groups[type_name] = []
            prim_groups[type_name].append(prim_path)
        
        # For each group with multiple prims, create instance
        for type_name, paths in prim_groups.items():
            if len(paths) > 1:
                # Create master prim
                master_path = f"/Masters/{type_name}_Master"
                master_prim = self.stage.DefinePrim(master_path)
                
                # Copy first prim to master
                source_prim = self.stage.GetPrimAtPath(paths[0])
                # This would require copying prim structure - simplified here
                
                # Make other prims instance the master
                for path in paths[1:]:
                    instance_prim = self.stage.GetPrimAtPath(path)
                    if instance_prim:
                        instance_prim.SetInstanceable(True)
        
        return True
    
    def convert_from_instances(self, master_path: str) -> bool:
        """Convert instances back to regular prims"""
        if not self.stage or not USD_AVAILABLE:
            return False
        
        if master_path not in self.instance_info:
            return False
        
        instance_info = self.instance_info[master_path]
        master = self.stage.GetPrimAtPath(master_path)
        
        if not master:
            return False
        
        # For each instance, copy master content
        for instance_path in instance_info.instance_paths:
            instance_prim = self.stage.GetPrimAtPath(instance_path)
            if instance_prim and instance_prim.IsInstance():
                # This would require copying master content - simplified here
                instance_prim.SetInstanceable(False)
        
        return True
    
    def set_instance_mode(self, mode: InstanceMode):
        """Set instance visualization mode"""
        self.instance_mode = mode
    
    def hide_instance(self, instance_path: str):
        """Hide an instance"""
        self.hidden_instances.add(instance_path)
    
    def show_instance(self, instance_path: str):
        """Show a hidden instance"""
        self.hidden_instances.discard(instance_path)
    
    def is_instance_visible(self, instance_path: str) -> bool:
        """Check if instance should be visible"""
        if instance_path in self.hidden_instances:
            return False
        
        if self.instance_mode == InstanceMode.HIDDEN:
            return False
        
        return True

