"""
USD Variants Support
Handles variant sets and variant selection
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd

try:
    from pxr import Usd
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class VariantManager:
    """Manages USD variant sets"""
    
    @staticmethod
    def get_variant_sets(prim: Usd.Prim) -> Dict[str, Dict]:
        """Get all variant sets on a prim"""
        if not USD_AVAILABLE:
            return {}
            
        variant_sets = prim.GetVariantSets()
        variant_set_names = variant_sets.GetNames()
        
        result = {}
        for variant_set_name in variant_set_names:
            variant_set = variant_sets.GetVariantSet(variant_set_name)
            current_selection = variant_set.GetVariantSelection()
            available_variants = variant_set.GetVariantNames()
            
            result[variant_set_name] = {
                'current_selection': current_selection,
                'available_variants': available_variants,
            }
        
        return result
    
    @staticmethod
    def set_variant_selection(prim: Usd.Prim, variant_set_name: str, variant_name: str) -> bool:
        """Set the selected variant for a variant set"""
        if not USD_AVAILABLE:
            return False
            
        try:
            variant_sets = prim.GetVariantSets()
            variant_set = variant_sets.GetVariantSet(variant_set_name)
            
            if variant_name in variant_set.GetVariantNames():
                variant_set.SetVariantSelection(variant_name)
                return True
            else:
                print(f"Variant '{variant_name}' not found in variant set '{variant_set_name}'")
                return False
        except Exception as e:
            print(f"Error setting variant selection: {e}")
            return False
    
    @staticmethod
    def get_variant_selection(prim: Usd.Prim, variant_set_name: str) -> Optional[str]:
        """Get the current variant selection for a variant set"""
        if not USD_AVAILABLE:
            return None
            
        try:
            variant_sets = prim.GetVariantSets()
            variant_set = variant_sets.GetVariantSet(variant_set_name)
            return variant_set.GetVariantSelection()
        except Exception as e:
            print(f"Error getting variant selection: {e}")
            return None
    
    @staticmethod
    def create_variant_set(prim: Usd.Prim, variant_set_name: str) -> bool:
        """Create a new variant set on a prim"""
        if not USD_AVAILABLE:
            return False
            
        try:
            variant_sets = prim.GetVariantSets()
            variant_set = variant_sets.AddVariantSet(variant_set_name)
            return variant_set is not None
        except Exception as e:
            print(f"Error creating variant set: {e}")
            return False
    
    @staticmethod
    def add_variant(prim: Usd.Prim, variant_set_name: str, variant_name: str) -> bool:
        """Add a variant to a variant set"""
        if not USD_AVAILABLE:
            return False
            
        try:
            variant_sets = prim.GetVariantSets()
            variant_set = variant_sets.GetVariantSet(variant_set_name)
            variant_set.AddVariant(variant_name)
            return True
        except Exception as e:
            print(f"Error adding variant: {e}")
            return False

