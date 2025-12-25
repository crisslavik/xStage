"""
Stage Variable Expressions
Handles stage variable display, editing, and evaluation
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd, Sdf

try:
    from pxr import Usd, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class StageVariableManager:
    """Manages stage variables"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
    
    def get_stage_variables(self) -> Dict[str, str]:
        """Get all stage variables"""
        if not USD_AVAILABLE or not self.stage:
            return {}
        
        variables = {}
        root_layer = self.stage.GetRootLayer()
        
        # Get stage variables from layer metadata
        # Stage variables are typically stored in layer metadata
        if hasattr(root_layer, 'customLayerData'):
            custom_data = root_layer.customLayerData
            if custom_data and isinstance(custom_data, dict):
                # Look for stage variables
                for key, value in custom_data.items():
                    if key.startswith('stageVariables') or key == 'stageVariables':
                        if isinstance(value, dict):
                            variables.update(value)
        
        # Also check for variables in stage metadata
        try:
            stage_metadata = self.stage.GetMetadata('customLayerData')
            if stage_metadata and isinstance(stage_metadata, dict):
                for key, value in stage_metadata.items():
                    if key.startswith('stageVariables') or key == 'stageVariables':
                        if isinstance(value, dict):
                            variables.update(value)
        except:
            pass
        
        return variables
    
    def set_stage_variable(self, name: str, value: str) -> bool:
        """Set a stage variable"""
        if not USD_AVAILABLE or not self.stage:
            return False
        
        try:
            root_layer = self.stage.GetRootLayer()
            
            # Get existing custom layer data
            custom_data = {}
            if hasattr(root_layer, 'customLayerData'):
                existing = root_layer.customLayerData
                if existing and isinstance(existing, dict):
                    custom_data = existing.copy()
            
            # Add/update stage variable
            if 'stageVariables' not in custom_data:
                custom_data['stageVariables'] = {}
            
            if not isinstance(custom_data['stageVariables'], dict):
                custom_data['stageVariables'] = {}
            
            custom_data['stageVariables'][name] = value
            
            # Set custom layer data
            root_layer.customLayerData = custom_data
            
            return True
        except Exception as e:
            print(f"Error setting stage variable: {e}")
            return False
    
    def evaluate_variable(self, variable_name: str) -> Optional[str]:
        """Evaluate a stage variable"""
        variables = self.get_stage_variables()
        return variables.get(variable_name)
    
    def find_variable_references(self, variable_name: str) -> List[str]:
        """Find all references to a stage variable in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        references = []
        variable_ref = f"${variable_name}"
        
        # Search in paths and asset paths
        for prim in self.stage.Traverse():
            # Check references
            if prim.HasAuthoredReferences():
                refs = prim.GetReferences()
                for ref in refs.GetAddedOrExplicitItems():
                    if variable_ref in str(ref.assetPath):
                        references.append(prim.GetPath().pathString)
            
            # Check payloads
            if prim.HasAuthoredPayloads():
                payloads = prim.GetPayloads()
                for payload in payloads.GetAddedOrExplicitItems():
                    if variable_ref in str(payload.assetPath):
                        references.append(prim.GetPath().pathString)
        
        return references

