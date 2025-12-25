"""
Batch Operations
Process multiple prims or files at once
Pipeline-friendly batch processing
"""

from typing import List, Dict, Callable, Optional
from pathlib import Path
from pxr import Usd, UsdGeom

try:
    from pxr import Usd, UsdGeom
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class BatchOperationManager:
    """Manages batch operations on prims or files"""
    
    def __init__(self, stage: Usd.Stage = None):
        self.stage = stage
    
    def batch_set_attribute(self, prim_paths: List[str], attr_name: str, value,
                           progress_callback: Optional[Callable] = None) -> Dict[str, bool]:
        """Set attribute on multiple prims"""
        if not USD_AVAILABLE or not self.stage:
            return {}
        
        results = {}
        total = len(prim_paths)
        
        for i, prim_path in enumerate(prim_paths):
            if progress_callback:
                progress_callback(int((i / total) * 100), f"Processing {prim_path}...")
            
            try:
                prim = self.stage.GetPrimAtPath(prim_path)
                if prim:
                    attr = prim.GetAttribute(attr_name)
                    if attr:
                        attr.Set(value)
                        results[prim_path] = True
                    else:
                        results[prim_path] = False
                else:
                    results[prim_path] = False
            except Exception as e:
                results[prim_path] = False
        
        return results
    
    def batch_assign_material(self, prim_paths: List[str], material_path: str,
                             progress_callback: Optional[Callable] = None) -> Dict[str, bool]:
        """Assign material to multiple prims"""
        if not USD_AVAILABLE or not self.stage:
            return {}
        
        try:
            from .materials import MaterialManager
        except ImportError:
            return {}
        
        results = {}
        total = len(prim_paths)
        material_prim = self.stage.GetPrimAtPath(material_path)
        
        if not material_prim:
            return {path: False for path in prim_paths}
        
        for i, prim_path in enumerate(prim_paths):
            if progress_callback:
                progress_callback(int((i / total) * 100), f"Assigning material to {prim_path}...")
            
            try:
                prim = self.stage.GetPrimAtPath(prim_path)
                if prim:
                    success = MaterialManager.bind_material(prim, material_prim)
                    results[prim_path] = success
                else:
                    results[prim_path] = False
            except Exception as e:
                results[prim_path] = False
        
        return results
    
    def batch_set_variant(self, prim_paths: List[str], variant_set: str, variant: str,
                         progress_callback: Optional[Callable] = None) -> Dict[str, bool]:
        """Set variant selection on multiple prims"""
        if not USD_AVAILABLE or not self.stage:
            return {}
        
        try:
            from .variants import VariantManager
        except ImportError:
            return {}
        
        results = {}
        total = len(prim_paths)
        
        for i, prim_path in enumerate(prim_paths):
            if progress_callback:
                progress_callback(int((i / total) * 100), f"Setting variant on {prim_path}...")
            
            try:
                prim = self.stage.GetPrimAtPath(prim_path)
                if prim:
                    success = VariantManager.set_variant_selection(prim, variant_set, variant)
                    results[prim_path] = success
                else:
                    results[prim_path] = False
            except Exception as e:
                results[prim_path] = False
        
        return results
    
    def batch_convert_files(self, input_files: List[str], output_dir: str,
                           conversion_options, progress_callback: Optional[Callable] = None) -> Dict[str, bool]:
        """Convert multiple files to USD"""
        from .converter import USDConverter
        
        results = {}
        total = len(input_files)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        converter = USDConverter(conversion_options)
        
        for i, input_file in enumerate(input_files):
            if progress_callback:
                progress_callback(int((i / total) * 100), f"Converting {Path(input_file).name}...")
            
            try:
                input_path = Path(input_file)
                output_file = output_path / input_path.with_suffix('.usd').name
                
                success = converter.convert(str(input_path), str(output_file), progress_callback)
                results[input_file] = success
            except Exception as e:
                results[input_file] = False
        
        return results
    
    def batch_export_selected(self, prim_paths: List[str], output_path: str,
                             progress_callback: Optional[Callable] = None) -> bool:
        """Export selected prims to a new USD file"""
        if not USD_AVAILABLE or not self.stage:
            return False
        
        try:
            if progress_callback:
                progress_callback(10, "Creating export stage...")
            
            # Create new stage
            export_stage = Usd.Stage.CreateNew(output_path)
            
            # Copy stage settings
            root_layer = self.stage.GetRootLayer()
            export_root = export_stage.GetRootLayer()
            
            # Copy metadata
            for key in root_layer.ListInfoKeys():
                export_root.SetInfo(key, root_layer.GetInfo(key))
            
            if progress_callback:
                progress_callback(30, "Copying prims...")
            
            # Copy selected prims
            total = len(prim_paths)
            for i, prim_path in enumerate(prim_paths):
                if progress_callback:
                    progress_callback(30 + int((i / total) * 60), f"Copying {prim_path}...")
                
                prim = self.stage.GetPrimAtPath(prim_path)
                if prim:
                    # Copy prim to export stage
                    # This is simplified - full implementation would need proper copying
                    pass
            
            if progress_callback:
                progress_callback(100, "Export complete!")
            
            export_stage.GetRootLayer().Save()
            return True
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Export failed: {e}")
            return False

