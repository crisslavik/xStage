"""
AOV (Render Var) Manager
AOV visualization and management
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from pxr import Usd, UsdRender, Gf, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class AOVDisplayMode(Enum):
    """AOV display modes"""
    RGB = "rgb"
    GRAYSCALE = "grayscale"
    HEATMAP = "heatmap"
    FALSE_COLOR = "false_color"


@dataclass
class AOVInfo:
    """AOV (Render Var) information"""
    name: str
    data_type: str
    source_name: str
    source_type: str
    prim_path: str
    enabled: bool = True


class AOVManager:
    """Manages AOV (Render Var) extraction and visualization"""
    
    def __init__(self, stage: Optional[Usd.Stage] = None):
        self.stage = stage
        self.aovs: List[AOVInfo] = []
        self.display_mode = AOVDisplayMode.RGB
    
    def extract_aovs(self) -> List[AOVInfo]:
        """Extract AOVs from render settings"""
        if not self.stage or not USD_AVAILABLE:
            return []
        
        self.aovs.clear()
        
        # Find render settings prims
        for prim in self.stage.Traverse():
            if prim.IsA(UsdRender.RenderSettings):
                render_settings = UsdRender.RenderSettings(prim)
                
                # Get products (which contain render vars/AOVs)
                products_rel = render_settings.GetProductsRel()
                if products_rel:
                    product_targets = products_rel.GetTargets()
                    
                    for product_path in product_targets:
                        product_prim = self.stage.GetPrimAtPath(product_path)
                        if product_prim and product_prim.IsA(UsdRender.Product):
                            product = UsdRender.Product(product_prim)
                            
                            # Get render vars (AOVs)
                            render_vars_rel = product.GetRenderVarsRel()
                            if render_vars_rel:
                                render_var_targets = render_vars_rel.GetTargets()
                                
                                for render_var_path in render_var_targets:
                                    render_var_prim = self.stage.GetPrimAtPath(render_var_path)
                                    if render_var_prim and render_var_prim.IsA(UsdRender.RenderVar):
                                        render_var = UsdRender.RenderVar(render_var_prim)
                                        
                                        # Get AOV information
                                        data_type_attr = render_var.GetDataTypeAttr()
                                        source_name_attr = render_var.GetSourceNameAttr()
                                        source_type_attr = render_var.GetSourceTypeAttr()
                                        
                                        aov_info = AOVInfo(
                                            name=render_var_prim.GetName(),
                                            data_type=str(data_type_attr.Get()) if data_type_attr else "unknown",
                                            source_name=str(source_name_attr.Get()) if source_name_attr else "",
                                            source_type=str(source_type_attr.Get()) if source_type_attr else "",
                                            prim_path=str(render_var_path)
                                        )
                                        
                                        self.aovs.append(aov_info)
        
        return self.aovs
    
    def get_aov_list(self) -> List[AOVInfo]:
        """Get list of all AOVs"""
        return self.aovs
    
    def get_aov_by_name(self, name: str) -> Optional[AOVInfo]:
        """Get AOV by name"""
        for aov in self.aovs:
            if aov.name == name:
                return aov
        return None
    
    def enable_aov(self, name: str, enabled: bool = True):
        """Enable/disable an AOV"""
        aov = self.get_aov_by_name(name)
        if aov:
            aov.enabled = enabled
    
    def set_display_mode(self, mode: AOVDisplayMode):
        """Set AOV display mode"""
        self.display_mode = mode
    
    def get_aov_statistics(self) -> Dict[str, any]:
        """Get AOV statistics"""
        enabled_count = sum(1 for aov in self.aovs if aov.enabled)
        
        return {
            'total_aovs': len(self.aovs),
            'enabled_aovs': enabled_count,
            'disabled_aovs': len(self.aovs) - enabled_count,
            'display_mode': self.display_mode.value,
        }

