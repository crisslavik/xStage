"""
USD Collections Support
Handles pattern-based and relationship-mode collections
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd, UsdCollectionAPI, Sdf

try:
    from pxr import Usd, UsdCollectionAPI, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class CollectionManager:
    """Manages USD collections"""
    
    @staticmethod
    def get_collections(prim: Usd.Prim) -> List[Dict]:
        """Get all collections on a prim"""
        if not USD_AVAILABLE:
            return []
            
        collection_apis = UsdCollectionAPI.GetAllCollectionAPIs(prim)
        collections = []
        
        for collection_api in collection_apis:
            collection = collection_api.GetCollection()
            collection_data = {
                'name': collection.GetName(),
                'prim_path': prim.GetPath().pathString,
                'expansion_rule': str(collection.GetExpansionRule()),
                'includes_paths': [str(p) for p in collection.GetIncludesRel().GetTargets()],
                'excludes_paths': [str(p) for p in collection.GetExcludesRel().GetTargets()],
            }
            
            # Determine collection mode
            if collection_api.GetCollectionName() == collection.GetName():
                collection_data['mode'] = 'relationship'
            else:
                collection_data['mode'] = 'pattern'
            
            collections.append(collection_data)
        
        return collections
    
    @staticmethod
    def create_collection(prim: Usd.Prim, collection_name: str, mode: str = 'relationship') -> Optional[UsdCollectionAPI]:
        """Create a new collection on a prim"""
        if not USD_AVAILABLE:
            return None
            
        try:
            if mode == 'relationship':
                collection_api = UsdCollectionAPI.ApplyCollection(prim, collection_name)
            else:
                # Pattern-based collection
                collection_api = UsdCollectionAPI.ApplyCollection(prim, collection_name, expansionRule='expandPrims')
            
            return collection_api
        except Exception as e:
            print(f"Error creating collection: {e}")
            return None
    
    @staticmethod
    def add_to_collection(collection_api: UsdCollectionAPI, prim_path: Sdf.Path) -> bool:
        """Add a prim to a collection"""
        if not USD_AVAILABLE:
            return False
            
        collection = collection_api.GetCollection()
        includes_rel = collection.GetIncludesRel()
        
        # Add to includes
        includes_rel.AddTarget(prim_path)
        return True
    
    @staticmethod
    def remove_from_collection(collection_api: UsdCollectionAPI, prim_path: Sdf.Path) -> bool:
        """Remove a prim from a collection"""
        if not USD_AVAILABLE:
            return False
            
        collection = collection_api.GetCollection()
        includes_rel = collection.GetIncludesRel()
        
        # Remove from includes
        includes_rel.RemoveTarget(prim_path)
        return True
    
    @staticmethod
    def get_collection_members(stage: Usd.Stage, collection_api: UsdCollectionAPI) -> List[Usd.Prim]:
        """Get all prims that are members of a collection"""
        if not USD_AVAILABLE:
            return []
            
        collection = collection_api.GetCollection()
        includes_paths = collection.GetIncludesRel().GetTargets()
        excludes_paths = collection.GetExcludesRel().GetTargets()
        
        members = []
        for path in includes_paths:
            prim = stage.GetPrimAtPath(path)
            if prim and prim.IsValid():
                # Check if not excluded
                if path not in excludes_paths:
                    members.append(prim)
        
        return members

