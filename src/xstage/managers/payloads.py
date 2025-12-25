"""
USD Payload Management
Handles payload loading and unloading for performance optimization
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, List, Dict
from pxr import Usd

try:
    from pxr import Usd
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class PayloadManager:
    """Manages USD payloads for performance optimization"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
        self.loaded_payloads = set()
    
    def load_payload(self, prim: Usd.Prim) -> bool:
        """Load a payload on a prim"""
        if not USD_AVAILABLE or not prim:
            return False
        
        try:
            if prim.HasPayload():
                prim.Load()
                self.loaded_payloads.add(prim.GetPath().pathString)
                return True
        except Exception as e:
            print(f"Error loading payload: {e}")
            return False
        
        return False
    
    def unload_payload(self, prim: Usd.Prim) -> bool:
        """Unload a payload on a prim"""
        if not USD_AVAILABLE or not prim:
            return False
        
        try:
            if prim.HasPayload():
                prim.Unload()
                self.loaded_payloads.discard(prim.GetPath().pathString)
                return True
        except Exception as e:
            print(f"Error unloading payload: {e}")
            return False
        
        return False
    
    def load_all_payloads(self) -> int:
        """Load all payloads in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return 0
        
        count = 0
        for prim in self.stage.Traverse():
            if prim.HasPayload() and prim.GetPath().pathString not in self.loaded_payloads:
                if self.load_payload(prim):
                    count += 1
        
        return count
    
    def unload_all_payloads(self) -> int:
        """Unload all payloads in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return 0
        
        count = 0
        for prim in self.stage.Traverse():
            if prim.HasPayload() and prim.GetPath().pathString in self.loaded_payloads:
                if self.unload_payload(prim):
                    count += 1
        
        return count
    
    def get_payload_info(self, prim: Usd.Prim) -> Optional[Dict]:
        """Get information about a prim's payload"""
        if not USD_AVAILABLE or not prim or not prim.HasPayload():
            return None
        
        try:
            payloads = prim.GetPayloads()
            if not payloads:
                return None
            
            payload_info = {
                'prim_path': prim.GetPath().pathString,
                'payloads': [],
                'is_loaded': prim.GetPath().pathString in self.loaded_payloads,
            }
            
            for payload in payloads:
                payload_data = {
                    'asset_path': str(payload.assetPath) if payload.assetPath else None,
                    'prim_path': str(payload.primPath) if payload.primPath else None,
                }
                payload_info['payloads'].append(payload_data)
            
            return payload_info
        except Exception as e:
            print(f"Error getting payload info: {e}")
            return None
    
    def find_all_payloads(self) -> List[Usd.Prim]:
        """Find all prims with payloads"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        payload_prims = []
        for prim in self.stage.Traverse():
            if prim.HasPayload():
                payload_prims.append(prim)
        
        return payload_prims

