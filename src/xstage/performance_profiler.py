"""
Performance Profiling
Track performance metrics for optimization
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
try:
    from pxr import Usd, UsdGeom, UsdLux, UsdShade
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    UsdGeom = None
    UsdLux = None
    UsdShade = None


@dataclass
class PerformanceMetric:
    """Single performance metric"""
    name: str
    value: float
    unit: str = "ms"
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceReport:
    """Performance report with multiple metrics"""
    stage_load_time: float = 0.0
    geometry_extraction_time: float = 0.0
    render_time: float = 0.0
    memory_usage: float = 0.0
    prim_count: int = 0
    mesh_count: int = 0
    metrics: List[PerformanceMetric] = field(default_factory=list)


class PerformanceProfiler:
    """Profiles USD operations for performance analysis"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.start_times: Dict[str, float] = {}
    
    def start_timer(self, operation_name: str):
        """Start timing an operation"""
        self.start_times[operation_name] = time.time()
    
    def end_timer(self, operation_name: str) -> float:
        """End timing and return elapsed time"""
        if operation_name in self.start_times:
            elapsed = (time.time() - self.start_times[operation_name]) * 1000  # Convert to ms
            del self.start_times[operation_name]
            
            metric = PerformanceMetric(operation_name, elapsed)
            self.metrics.append(metric)
            return elapsed
        return 0.0
    
    def profile_stage_load(self, filepath: str) -> float:
        """Profile stage loading"""
        self.start_timer("stage_load")
        
        if USD_AVAILABLE:
            try:
                stage = Usd.Stage.Open(filepath)
                elapsed = self.end_timer("stage_load")
                return elapsed
            except:
                self.end_timer("stage_load")
                return 0.0
        return 0.0
    
    def profile_geometry_extraction(self, stage: Usd.Stage, time_code: float) -> float:
        """Profile geometry extraction"""
        if not USD_AVAILABLE:
            return 0.0
        
        self.start_timer("geometry_extraction")
        
        try:
            # Count prims
            prim_count = sum(1 for _ in stage.Traverse())
            
            # Count meshes
            if UsdGeom:
                mesh_count = sum(1 for prim in stage.Traverse() 
                               if prim.IsA(UsdGeom.Mesh))
            
            elapsed = self.end_timer("geometry_extraction")
            return elapsed
        except:
            self.end_timer("geometry_extraction")
            return 0.0
    
    def get_stage_statistics(self, stage: Usd.Stage) -> Dict:
        """Get statistics about a stage"""
        if not USD_AVAILABLE or not stage:
            return {}
        
        stats = {
            'prim_count': 0,
            'mesh_count': 0,
            'camera_count': 0,
            'light_count': 0,
            'material_count': 0,
        }
        
        for prim in stage.Traverse():
            stats['prim_count'] += 1
            
            if UsdGeom and prim.IsA(UsdGeom.Mesh):
                stats['mesh_count'] += 1
            elif UsdGeom and prim.IsA(UsdGeom.Camera):
                stats['camera_count'] += 1
            elif UsdLux and prim.IsA(UsdLux.Light):
                stats['light_count'] += 1
            elif UsdShade and prim.IsA(UsdShade.Material):
                stats['material_count'] += 1
        
        return stats
    
    def generate_report(self, stage: Usd.Stage = None) -> PerformanceReport:
        """Generate performance report"""
        report = PerformanceReport()
        
        # Get metrics
        for metric in self.metrics:
            if 'load' in metric.name.lower():
                report.stage_load_time = metric.value
            elif 'extraction' in metric.name.lower():
                report.geometry_extraction_time = metric.value
            elif 'render' in metric.name.lower():
                report.render_time = metric.value
        
        report.metrics = self.metrics
        
        # Get stage statistics
        if stage:
            stats = self.get_stage_statistics(stage)
            report.prim_count = stats.get('prim_count', 0)
            report.mesh_count = stats.get('mesh_count', 0)
        
        return report
    
    def clear(self):
        """Clear all metrics"""
        self.metrics.clear()
        self.start_times.clear()

