"""
USD Layer Composition Visualization
Displays and manages layer stack, references, subLayers, and payloads
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd, Sdf

try:
    from pxr import Usd, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class LayerCompositionManager:
    """Manages USD layer composition"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
    
    def get_layer_stack(self) -> List[Dict]:
        """Get the complete layer stack"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        layer_stack = []
        root_layer = self.stage.GetRootLayer()
        
        # Get all layers in the stack
        layers = self.stage.GetLayerStack(includeSessionLayers=False)
        
        for layer in layers:
            layer_info = {
                'identifier': layer.identifier,
                'display_name': layer.displayName,
                'real_path': layer.realPath if hasattr(layer, 'realPath') else None,
                'anonymous': layer.anonymous,
                'dirty': layer.dirty,
                'has_owner': layer.HasOwner(),
                'sub_layers': [],
                'references': [],
                'payloads': [],
                'offset': None,
            }
            
            # Get subLayers
            if layer.subLayerPaths:
                for sublayer_path in layer.subLayerPaths:
                    sublayer_offset = layer.GetSubLayerOffset(sublayer_path)
                    layer_info['sub_layers'].append({
                        'path': sublayer_path,
                        'offset': {
                            'offset': sublayer_offset.GetOffset() if sublayer_offset else 0.0,
                            'scale': sublayer_offset.GetScale() if sublayer_offset else 1.0,
                        } if sublayer_offset else None,
                    })
            
            # Get references (from root layer prims)
            if layer == root_layer:
                layer_info['references'] = self._get_references_from_stage()
            
            # Get payloads (from root layer prims)
            if layer == root_layer:
                layer_info['payloads'] = self._get_payloads_from_stage()
            
            layer_stack.append(layer_info)
        
        return layer_stack
    
    def _get_references_from_stage(self) -> List[Dict]:
        """Get all references in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        references = []
        
        def collect_references(prim):
            """Recursively collect references"""
            if prim.HasAuthoredReferences():
                refs = prim.GetReferences()
                for ref in refs.GetAddedOrExplicitItems():
                    ref_info = {
                        'prim_path': prim.GetPath().pathString,
                        'asset_path': str(ref.assetPath) if ref.assetPath else None,
                        'prim_path_in_layer': str(ref.primPath) if ref.primPath else None,
                        'layer_offset': {
                            'offset': ref.layerOffset.GetOffset() if ref.layerOffset else 0.0,
                            'scale': ref.layerOffset.GetScale() if ref.layerOffset else 1.0,
                        } if ref.layerOffset else None,
                    }
                    references.append(ref_info)
            
            for child in prim.GetChildren():
                collect_references(child)
        
        root = self.stage.GetPseudoRoot()
        for child in root.GetChildren():
            collect_references(child)
        
        return references
    
    def _get_payloads_from_stage(self) -> List[Dict]:
        """Get all payloads in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        payloads = []
        
        def collect_payloads(prim):
            """Recursively collect payloads"""
            if prim.HasAuthoredPayloads():
                payload_list = prim.GetPayloads()
                for payload in payload_list.GetAddedOrExplicitItems():
                    payload_info = {
                        'prim_path': prim.GetPath().pathString,
                        'asset_path': str(payload.assetPath) if payload.assetPath else None,
                        'prim_path_in_layer': str(payload.primPath) if payload.primPath else None,
                    }
                    payloads.append(payload_info)
            
            for child in prim.GetChildren():
                collect_payloads(child)
        
        root = self.stage.GetPseudoRoot()
        for child in root.GetChildren():
            collect_payloads(child)
        
        return payloads
    
    def add_sublayer(self, layer: Sdf.Layer, sublayer_path: str, offset: float = 0.0, scale: float = 1.0) -> bool:
        """Add a subLayer to a layer"""
        if not USD_AVAILABLE:
            return False
        
        try:
            layer.subLayerPaths.append(sublayer_path)
            if offset != 0.0 or scale != 1.0:
                layer.SetSubLayerOffset(Sdf.LayerOffset(offset, scale), len(layer.subLayerPaths) - 1)
            return True
        except Exception as e:
            print(f"Error adding subLayer: {e}")
            return False
    
    def remove_sublayer(self, layer: Sdf.Layer, sublayer_path: str) -> bool:
        """Remove a subLayer from a layer"""
        if not USD_AVAILABLE:
            return False
        
        try:
            if sublayer_path in layer.subLayerPaths:
                index = layer.subLayerPaths.index(sublayer_path)
                layer.subLayerPaths.pop(index)
                return True
        except Exception as e:
            print(f"Error removing subLayer: {e}")
            return False
    
    def add_reference(self, prim: Usd.Prim, asset_path: str, prim_path: Sdf.Path = None, 
                     offset: float = 0.0, scale: float = 1.0) -> bool:
        """Add a reference to a prim"""
        if not USD_AVAILABLE:
            return False
        
        try:
            refs = prim.GetReferences()
            if prim_path:
                refs.AddReference(asset_path, prim_path, Sdf.LayerOffset(offset, scale))
            else:
                refs.AddReference(asset_path, Sdf.LayerOffset(offset, scale))
            return True
        except Exception as e:
            print(f"Error adding reference: {e}")
            return False
    
    def remove_reference(self, prim: Usd.Prim, asset_path: str, prim_path: Sdf.Path = None) -> bool:
        """Remove a reference from a prim"""
        if not USD_AVAILABLE:
            return False
        
        try:
            refs = prim.GetReferences()
            if prim_path:
                refs.RemoveReference(asset_path, prim_path)
            else:
                refs.RemoveReference(asset_path)
            return True
        except Exception as e:
            print(f"Error removing reference: {e}")
            return False
    
    def get_layer_hierarchy(self) -> Dict:
        """Get layer hierarchy tree"""
        if not USD_AVAILABLE or not self.stage:
            return {}
        
        root_layer = self.stage.GetRootLayer()
        hierarchy = {
            'layer': {
                'identifier': root_layer.identifier,
                'display_name': root_layer.displayName,
            },
            'children': [],
        }
        
        # Build hierarchy from subLayers
        def build_hierarchy(layer, parent_node):
            """Recursively build layer hierarchy"""
            if layer.subLayerPaths:
                for sublayer_path in layer.subLayerPaths:
                    try:
                        sublayer = Sdf.Layer.FindOrOpen(sublayer_path)
                        if sublayer:
                            child_node = {
                                'layer': {
                                    'identifier': sublayer.identifier,
                                    'display_name': sublayer.displayName,
                                },
                                'children': [],
                            }
                            parent_node['children'].append(child_node)
                            build_hierarchy(sublayer, child_node)
                    except Exception as e:
                        print(f"Error loading subLayer {sublayer_path}: {e}")
        
        build_hierarchy(root_layer, hierarchy)
        return hierarchy
    
    def get_composition_arcs(self, prim: Usd.Prim) -> Dict:
        """Get all composition arcs for a prim"""
        if not USD_AVAILABLE or not prim:
            return {}
        
        arcs = {
            'references': [],
            'payloads': [],
            'inherits': [],
            'specializes': [],
            'variant_sets': [],
        }
        
        # Get references
        if prim.HasAuthoredReferences():
            refs = prim.GetReferences()
            for ref in refs.GetAddedOrExplicitItems():
                arcs['references'].append({
                    'asset_path': str(ref.assetPath) if ref.assetPath else None,
                    'prim_path': str(ref.primPath) if ref.primPath else None,
                })
        
        # Get payloads
        if prim.HasAuthoredPayloads():
            payloads = prim.GetPayloads()
            for payload in payloads.GetAddedOrExplicitItems():
                arcs['payloads'].append({
                    'asset_path': str(payload.assetPath) if payload.assetPath else None,
                    'prim_path': str(payload.primPath) if payload.primPath else None,
                })
        
        # Get inherits
        if prim.HasAuthoredInherits():
            inherits = prim.GetInherits()
            for inherit in inherits.GetAddedOrExplicitItems():
                arcs['inherits'].append({
                    'prim_path': str(inherit) if inherit else None,
                })
        
        # Get specializes
        if prim.HasAuthoredSpecializes():
            specializes = prim.GetSpecializes()
            for specialize in specializes.GetAddedOrExplicitItems():
                arcs['specializes'].append({
                    'prim_path': str(specialize) if specialize else None,
                })
        
        # Get variant sets
        variant_sets = prim.GetVariantSets()
        for variant_set_name in variant_sets.GetNames():
            variant_set = variant_sets.GetVariantSet(variant_set_name)
            arcs['variant_sets'].append({
                'name': variant_set_name,
                'selection': variant_set.GetVariantSelection(),
            })
        
        return arcs

