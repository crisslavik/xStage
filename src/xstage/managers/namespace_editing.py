"""
Namespace Editing
Handles prim renaming, moving, and relocates
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List
from pxr import Usd, UsdNamespaceEditor, Sdf

try:
    from pxr import Usd, UsdNamespaceEditor, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class NamespaceEditor:
    """Manages namespace editing operations"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
        self.editor = UsdNamespaceEditor(stage) if USD_AVAILABLE else None
    
    def can_rename(self, old_path: str, new_name: str) -> bool:
        """Check if a prim can be renamed"""
        if not USD_AVAILABLE or not self.editor:
            return False
        
        try:
            old_sdf_path = Sdf.Path(old_path)
            parent_path = old_sdf_path.GetParentPath()
            new_path = parent_path.AppendChild(new_name)
            return self.editor.CanEditNamespace(old_sdf_path, new_path)
        except Exception as e:
            print(f"Error checking rename: {e}")
            return False
    
    def rename_prim(self, old_path: str, new_name: str) -> bool:
        """Rename a prim"""
        if not USD_AVAILABLE or not self.editor:
            return False
        
        try:
            old_sdf_path = Sdf.Path(old_path)
            parent_path = old_sdf_path.GetParentPath()
            new_path = parent_path.AppendChild(new_name)
            
            if self.editor.CanEditNamespace(old_sdf_path, new_path):
                return self.editor.EditNamespace(old_sdf_path, new_path)
        except Exception as e:
            print(f"Error renaming prim: {e}")
            return False
        
        return False
    
    def can_move(self, old_path: str, new_path: str) -> bool:
        """Check if a prim can be moved"""
        if not USD_AVAILABLE or not self.editor:
            return False
        
        try:
            old_sdf_path = Sdf.Path(old_path)
            new_sdf_path = Sdf.Path(new_path)
            return self.editor.CanEditNamespace(old_sdf_path, new_sdf_path)
        except Exception as e:
            print(f"Error checking move: {e}")
            return False
    
    def move_prim(self, old_path: str, new_path: str) -> bool:
        """Move a prim to a new location"""
        if not USD_AVAILABLE or not self.editor:
            return False
        
        try:
            old_sdf_path = Sdf.Path(old_path)
            new_sdf_path = Sdf.Path(new_path)
            
            if self.editor.CanEditNamespace(old_sdf_path, new_sdf_path):
                return self.editor.EditNamespace(old_sdf_path, new_sdf_path)
        except Exception as e:
            print(f"Error moving prim: {e}")
            return False
        
        return False
    
    def get_relocates(self) -> List[Dict]:
        """Get all relocates in the stage"""
        if not USD_AVAILABLE or not self.stage:
            return []
        
        relocates = []
        root_layer = self.stage.GetRootLayer()
        
        # Get relocates from root layer
        if hasattr(root_layer, 'relocates'):
            for old_path, new_path in root_layer.relocates.items():
                relocates.append({
                    'old_path': str(old_path),
                    'new_path': str(new_path),
                })
        
        return relocates
    
    def can_apply_edits(self) -> tuple:
        """Check if edits can be applied"""
        if not USD_AVAILABLE or not self.editor:
            return (False, ["Editor not available"])
        
        try:
            can_apply, errors = self.editor.CanApplyEdits()
            return (can_apply, [str(e) for e in errors] if errors else [])
        except Exception as e:
            return (False, [str(e)])
    
    def apply_edits(self) -> bool:
        """Apply all pending edits"""
        if not USD_AVAILABLE or not self.editor:
            return False
        
        try:
            can_apply, errors = self.editor.CanApplyEdits()
            if can_apply:
                return self.editor.ApplyEdits()
            else:
                print(f"Cannot apply edits: {errors}")
                return False
        except Exception as e:
            print(f"Error applying edits: {e}")
            return False

