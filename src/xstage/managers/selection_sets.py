"""
Selection Sets Manager
Save, load, and manage named selection sets
"""

from typing import List, Dict, Optional, Set
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from pxr import Usd, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class SelectionSetOperation(Enum):
    """Selection set operations"""
    UNION = "union"
    INTERSECT = "intersect"
    SUBTRACT = "subtract"
    REPLACE = "replace"


@dataclass
class SelectionSet:
    """Named selection set"""
    name: str
    prim_paths: List[str]
    stage_path: Optional[str] = None  # USD file path
    description: str = ""
    tags: List[str] = None
    created_at: float = 0.0
    updated_at: float = 0.0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at == 0.0:
            import time
            self.created_at = time.time()
            self.updated_at = time.time()


class SelectionSetManager:
    """Manages selection sets"""
    
    def __init__(self, stage: Optional[Usd.Stage] = None, config_path: Optional[str] = None):
        self.stage = stage
        self.config_path = config_path or str(Path.home() / ".xstage" / "selection_sets.json")
        self.selection_sets: List[SelectionSet] = []
        self.current_selection: Set[str] = set()
        self.load()
    
    def create_selection_set(self, name: str, prim_paths: List[str], 
                            description: str = "", tags: List[str] = None) -> str:
        """Create a new selection set"""
        import time
        
        # Remove existing set with same name
        self.selection_sets = [s for s in self.selection_sets if s.name != name]
        
        stage_path = None
        if self.stage:
            stage_path = self.stage.GetRootLayer().identifier
        
        selection_set = SelectionSet(
            name=name,
            prim_paths=prim_paths,
            stage_path=stage_path,
            description=description,
            tags=tags or [],
            created_at=time.time(),
            updated_at=time.time()
        )
        
        self.selection_sets.append(selection_set)
        self.save()
        return name
    
    def get_selection_set(self, name: str) -> Optional[SelectionSet]:
        """Get a selection set by name"""
        for s in self.selection_sets:
            if s.name == name:
                return s
        return None
    
    def delete_selection_set(self, name: str) -> bool:
        """Delete a selection set"""
        for i, s in enumerate(self.selection_sets):
            if s.name == name:
                self.selection_sets.pop(i)
                self.save()
                return True
        return False
    
    def update_selection_set(self, name: str, prim_paths: List[str] = None,
                           description: str = None, tags: List[str] = None) -> bool:
        """Update a selection set"""
        import time
        
        for s in self.selection_sets:
            if s.name == name:
                if prim_paths is not None:
                    s.prim_paths = prim_paths
                if description is not None:
                    s.description = description
                if tags is not None:
                    s.tags = tags
                s.updated_at = time.time()
                self.save()
                return True
        return False
    
    def get_selection_sets_for_stage(self, stage_path: str) -> List[SelectionSet]:
        """Get selection sets for a specific stage"""
        return [s for s in self.selection_sets if s.stage_path == stage_path]
    
    def get_selection_sets_by_tag(self, tag: str) -> List[SelectionSet]:
        """Get selection sets by tag"""
        return [s for s in self.selection_sets if tag in s.tags]
    
    def apply_selection_set(self, name: str, operation: SelectionSetOperation = SelectionSetOperation.REPLACE) -> List[str]:
        """Apply a selection set to current selection"""
        selection_set = self.get_selection_set(name)
        if not selection_set:
            return []
        
        current_set = set(self.current_selection)
        new_set = set(selection_set.prim_paths)
        
        if operation == SelectionSetOperation.REPLACE:
            result = new_set
        elif operation == SelectionSetOperation.UNION:
            result = current_set | new_set
        elif operation == SelectionSetOperation.INTERSECT:
            result = current_set & new_set
        elif operation == SelectionSetOperation.SUBTRACT:
            result = current_set - new_set
        else:
            result = new_set
        
        self.current_selection = result
        return list(result)
    
    def save_current_selection(self, name: str, description: str = "") -> str:
        """Save current selection as a selection set"""
        return self.create_selection_set(name, list(self.current_selection), description)
    
    def set_current_selection(self, prim_paths: List[str]):
        """Set current selection"""
        self.current_selection = set(prim_paths)
    
    def get_current_selection(self) -> List[str]:
        """Get current selection"""
        return list(self.current_selection)
    
    def save(self):
        """Save selection sets to disk"""
        try:
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                'selection_sets': [asdict(s) for s in self.selection_sets]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving selection sets: {e}")
    
    def load(self):
        """Load selection sets from disk"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                self.selection_sets = [
                    SelectionSet(**s_data) for s_data in data.get('selection_sets', [])
                ]
        except Exception as e:
            print(f"Error loading selection sets: {e}")
            self.selection_sets = []
    
    def export_selection_set(self, name: str, filepath: str) -> bool:
        """Export a selection set to file"""
        selection_set = self.get_selection_set(name)
        if not selection_set:
            return False
        
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(selection_set), f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting selection set: {e}")
            return False
    
    def import_selection_set(self, filepath: str) -> bool:
        """Import a selection set from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            selection_set = SelectionSet(**data)
            # Remove existing if same name
            self.selection_sets = [s for s in self.selection_sets if s.name != selection_set.name]
            self.selection_sets.append(selection_set)
            self.save()
            return True
        except Exception as e:
            print(f"Error importing selection set: {e}")
            return False

