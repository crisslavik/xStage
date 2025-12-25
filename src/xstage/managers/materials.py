"""
USD Materials Support
Handles material extraction, visualization, and MaterialX integration
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd, UsdShade, Sdf

try:
    from pxr import Usd, UsdShade, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class MaterialManager:
    """Manages USD materials and shaders"""
    
    @staticmethod
    def extract_material(prim: Usd.Prim, time_code: float) -> Optional[Dict]:
        """Extract material data from a prim"""
        if not USD_AVAILABLE or not prim.IsA(UsdShade.Material):
            return None
            
        try:
            material = UsdShade.Material(prim)
            material_data = {
                'name': prim.GetPath().pathString,
                'path': prim.GetPath(),
                'surface_output': None,
                'displacement_output': None,
                'volume_output': None,
                'inputs': {},
                'surface_shader': None,
                'shader_network': [],
            }
            
            # Get surface output
            surface_output = material.GetSurfaceOutput()
            if surface_output:
                material_data['surface_output'] = {
                    'path': surface_output.GetPath(),
                    'type': str(surface_output.GetTypeName()),
                }
                # Get connected source
                source = surface_output.GetConnectedSource()
                if source:
                    material_data['surface_shader'] = {
                        'path': source[0].GetPath().pathString,
                        'output_name': source[1],
                    }
                    # Extract shader network
                    material_data['shader_network'] = MaterialManager._extract_shader_network(
                        source[0], time_code
                    )
            
            # Get displacement output
            displacement_output = material.GetDisplacementOutput()
            if displacement_output:
                material_data['displacement_output'] = {
                    'path': displacement_output.GetPath(),
                    'type': str(displacement_output.GetTypeName()),
                }
            
            # Get volume output
            volume_output = material.GetVolumeOutput()
            if volume_output:
                material_data['volume_output'] = {
                    'path': volume_output.GetPath(),
                    'type': str(volume_output.GetTypeName()),
                }
            
            # Extract material inputs
            for input_attr in material.GetInputs():
                input_name = input_attr.GetBaseName()
                input_value = input_attr.Get(time_code)
                material_data['inputs'][input_name] = {
                    'value': input_value,
                    'type': str(input_attr.GetTypeName()),
                }
            
            return material_data
        except Exception as e:
            print(f"Error extracting material {prim.GetPath()}: {e}")
            return None
    
    @staticmethod
    def _extract_shader_network(shader_prim: Usd.Prim, time_code: float) -> List[Dict]:
        """Extract shader network from a shader prim"""
        if not USD_AVAILABLE:
            return []
            
        network = []
        try:
            shader = UsdShade.Shader(shader_prim)
            
            shader_data = {
                'name': shader_prim.GetPath().pathString,
                'id': shader.GetIdAttr().Get(time_code) if shader.GetIdAttr() else None,
                'inputs': {},
                'outputs': {},
            }
            
            # Extract inputs
            for input_attr in shader.GetInputs():
                input_name = input_attr.GetBaseName()
                input_value = input_attr.Get(time_code)
                
                # Check if connected
                source = input_attr.GetConnectedSource()
                if source:
                    shader_data['inputs'][input_name] = {
                        'connected': True,
                        'source': source[0].GetPath().pathString,
                        'source_output': source[1],
                    }
                else:
                    shader_data['inputs'][input_name] = {
                        'connected': False,
                        'value': input_value,
                        'type': str(input_attr.GetTypeName()),
                    }
            
            # Extract outputs
            for output_attr in shader.GetOutputs():
                output_name = output_attr.GetBaseName()
                shader_data['outputs'][output_name] = {
                    'type': str(output_attr.GetTypeName()),
                }
            
            network.append(shader_data)
            
            # Recursively extract connected shaders
            for input_attr in shader.GetInputs():
                source = input_attr.GetConnectedSource()
                if source:
                    connected_network = MaterialManager._extract_shader_network(source[0], time_code)
                    network.extend(connected_network)
            
        except Exception as e:
            print(f"Error extracting shader network: {e}")
        
        return network
    
    @staticmethod
    def get_material_binding(prim: Usd.Prim, purpose: str = 'preview') -> Optional[Usd.Prim]:
        """Get the material bound to a prim"""
        if not USD_AVAILABLE:
            return None
            
        try:
            binding_api = UsdShade.MaterialBindingAPI(prim)
            if not binding_api:
                return None
            
            # Get material binding for specific purpose
            if purpose == 'preview':
                material = binding_api.GetPreviewMaterial()
            elif purpose == 'full':
                material = binding_api.GetFullMaterial()
            else:
                material = binding_api.GetDirectBinding().GetMaterial()
            
            return material.GetPrim() if material else None
        except Exception as e:
            print(f"Error getting material binding: {e}")
            return None
    
    @staticmethod
    def bind_material(prim: Usd.Prim, material_prim: Usd.Prim, purpose: str = 'preview') -> bool:
        """Bind a material to a prim"""
        if not USD_AVAILABLE:
            return False
            
        try:
            binding_api = UsdShade.MaterialBindingAPI.Apply(prim)
            material = UsdShade.Material(material_prim)
            
            if purpose == 'preview':
                binding_api.Bind(material, bindingStrength='strongerThanDescendants')
            elif purpose == 'full':
                binding_api.Bind(material, bindingStrength='strongerThanDescendants', materialPurpose='full')
            else:
                binding_api.Bind(material, bindingStrength='strongerThanDescendants')
            
            return True
        except Exception as e:
            print(f"Error binding material: {e}")
            return False
    
    @staticmethod
    def find_all_materials(stage: Usd.Stage) -> List[Usd.Prim]:
        """Find all materials in the stage"""
        if not USD_AVAILABLE:
            return []
            
        materials = []
        for prim in stage.Traverse():
            if prim.IsA(UsdShade.Material):
                materials.append(prim)
        return materials

