"""
Pipeline Integration
Easy integration with VFX pipelines (ShotGrid, Nuke, Houdini, etc.)
"""

from typing import Optional, Dict, List
from pathlib import Path
import json

try:
    from pxr import Usd, UsdGeom
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    UsdGeom = None


class PipelineIntegration:
    """Manages pipeline integration"""
    
    def __init__(self):
        self.pipeline_config = {}
    
    def load_config(self, config_path: str) -> bool:
        """Load pipeline configuration"""
        try:
            with open(config_path, 'r') as f:
                self.pipeline_config = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading pipeline config: {e}")
            return False
    
    def get_asset_path(self, asset_name: str, asset_type: str = "model") -> Optional[str]:
        """Get asset path from pipeline"""
        if 'asset_paths' in self.pipeline_config:
            asset_paths = self.pipeline_config['asset_paths']
            if asset_type in asset_paths:
                base_path = asset_paths[asset_type]
                return str(Path(base_path) / asset_name)
        return None
    
    def get_render_output_path(self, shot_name: str, render_name: str) -> Optional[str]:
        """Get render output path from pipeline"""
        if 'render_outputs' in self.pipeline_config:
            render_outputs = self.pipeline_config['render_outputs']
            base_path = render_outputs.get('base_path', '')
            return str(Path(base_path) / shot_name / render_name)
        return None
    
    def create_shot_stage(self, shot_name: str, output_path: str) -> Optional[Usd.Stage]:
        """Create a standard shot stage structure"""
        if not USD_AVAILABLE:
            return None
        
        try:
            stage = Usd.Stage.CreateNew(output_path)
            
            # Create standard shot structure
            root = UsdGeom.Xform.Define(stage, '/World')
            stage.SetDefaultPrim(root.GetPrim())
            
            # Create standard prims
            UsdGeom.Xform.Define(stage, '/World/geo')
            UsdGeom.Xform.Define(stage, '/World/lights')
            UsdGeom.Xform.Define(stage, '/World/cameras')
            UsdGeom.Xform.Define(stage, '/World/props')
            
            # Set metadata
            root_layer = stage.GetRootLayer()
            root_layer.comment = f"Shot: {shot_name}"
            
            stage.GetRootLayer().Save()
            return stage
        except Exception as e:
            print(f"Error creating shot stage: {e}")
            return None
    
    def export_for_nuke(self, stage: Usd.Stage, output_path: str) -> bool:
        """Export stage optimized for Nuke"""
        if not USD_AVAILABLE:
            return False
        
        try:
            # Export as USDZ or flattened USD for Nuke
            stage.Export(output_path)
            return True
        except Exception as e:
            print(f"Error exporting for Nuke: {e}")
            return False
    
    def export_for_houdini(self, stage: Usd.Stage, output_path: str) -> bool:
        """Export stage optimized for Houdini"""
        if not USD_AVAILABLE:
            return False
        
        try:
            # Houdini works well with standard USD
            stage.GetRootLayer().Save()
            return True
        except Exception as e:
            print(f"Error exporting for Houdini: {e}")
            return False

