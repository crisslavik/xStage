"""
Material Validator
Validates materials for Houdini Karma and Nuke 17 compatibility
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from pxr import Usd, UsdShade, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


@dataclass
class MaterialIssue:
    """Material validation issue"""
    severity: str  # "error", "warning", "info"
    message: str
    prim_path: str
    property_name: Optional[str] = None


class MaterialValidator:
    """Validates USD materials for compatibility"""
    
    def __init__(self, target: str = "auto"):
        """
        Initialize validator
        
        Args:
            target: Target application ("karma", "nuke", "auto")
        """
        self.target = target
    
    def validate_material(self, material: UsdShade.Material) -> List[MaterialIssue]:
        """
        Validate a material for compatibility
        
        Args:
            material: UsdShade.Material to validate
        
        Returns:
            List of validation issues
        """
        issues = []
        
        if not USD_AVAILABLE:
            return issues
        
        try:
            prim = material.GetPrim()
            
            # Check surface output
            surface_output = material.GetSurfaceOutput()
            if not surface_output:
                issues.append(MaterialIssue(
                    severity="error",
                    message="Material missing surface output",
                    prim_path=str(prim.GetPath())
                ))
            else:
                # Check shader connection
                source = surface_output.GetConnectedSource()
                if not source:
                    issues.append(MaterialIssue(
                        severity="error",
                        message="Surface output not connected to shader",
                        prim_path=str(prim.GetPath())
                    ))
                else:
                    # Validate shader
                    shader_prim = source[0]
                    shader_issues = self._validate_shader(shader_prim)
                    issues.extend(shader_issues)
            
            # Check for MaterialX compatibility
            if self.target in ["karma", "nuke", "auto"]:
                mtlx_issues = self._validate_materialx_compatibility(material)
                issues.extend(mtlx_issues)
        
        except Exception as e:
            issues.append(MaterialIssue(
                severity="error",
                message=f"Error validating material: {e}",
                prim_path=str(material.GetPrim().GetPath())
            ))
        
        return issues
    
    def _validate_shader(self, shader_prim: Usd.Prim) -> List[MaterialIssue]:
        """Validate shader prim"""
        issues = []
        
        try:
            shader = UsdShade.Shader(shader_prim)
            shader_id = shader.GetIdAttr().Get()
            
            # Check for MaterialX shader IDs
            if self.target in ["karma", "nuke", "auto"]:
                if shader_id and "standard_surface" in shader_id:
                    # Valid MaterialX Standard Surface
                    pass
                elif shader_id and "UsdPreviewSurface" in shader_id:
                    issues.append(MaterialIssue(
                        severity="warning",
                        message="Using UsdPreviewSurface instead of MaterialX (may not render correctly in Karma/Nuke)",
                        prim_path=str(shader_prim.GetPath()),
                        property_name="id"
                    ))
            
            # Check for required inputs
            if "standard_surface" in str(shader_id):
                # MaterialX Standard Surface should have base_color
                base_color_input = shader.GetInput("base_color")
                if not base_color_input:
                    issues.append(MaterialIssue(
                        severity="warning",
                        message="MaterialX shader missing base_color input",
                        prim_path=str(shader_prim.GetPath()),
                        property_name="base_color"
                    ))
        
        except Exception as e:
            issues.append(MaterialIssue(
                severity="error",
                message=f"Error validating shader: {e}",
                prim_path=str(shader_prim.GetPath())
            ))
        
        return issues
    
    def _validate_materialx_compatibility(self, material: UsdShade.Material) -> List[MaterialIssue]:
        """Validate MaterialX compatibility for Karma/Nuke"""
        issues = []
        
        try:
            prim = material.GetPrim()
            
            # Check for MaterialX metadata
            if not prim.HasMetadata("info:mdl:sourceAsset"):
                # Not a MaterialX material, but that's okay if using standard shaders
                pass
            
            # Check for Houdini/Nuke specific metadata
            if self.target == "karma":
                if not prim.HasMetadata("houdini:material"):
                    issues.append(MaterialIssue(
                        severity="info",
                        message="Material missing Houdini metadata (optional)",
                        prim_path=str(prim.GetPath())
                    ))
            
            elif self.target == "nuke":
                if not prim.HasMetadata("nuke:material"):
                    issues.append(MaterialIssue(
                        severity="info",
                        message="Material missing Nuke metadata (optional)",
                        prim_path=str(prim.GetPath())
                    ))
        
        except Exception as e:
            issues.append(MaterialIssue(
                severity="warning",
                message=f"Error checking MaterialX compatibility: {e}",
                prim_path=str(material.GetPrim().GetPath())
            ))
        
        return issues
    
    def validate_stage(self, stage: Usd.Stage) -> Dict[str, List[MaterialIssue]]:
        """
        Validate all materials in a stage
        
        Args:
            stage: USD stage to validate
        
        Returns:
            Dictionary mapping material paths to issues
        """
        results = {}
        
        if not USD_AVAILABLE:
            return results
        
        try:
            for prim in stage.Traverse():
                if prim.IsA(UsdShade.Material):
                    material = UsdShade.Material(prim)
                    issues = self.validate_material(material)
                    if issues:
                        results[str(prim.GetPath())] = issues
        
        except Exception as e:
            print(f"Error validating stage: {e}")
        
        return results

