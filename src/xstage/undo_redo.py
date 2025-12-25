"""
Undo/Redo System
Command pattern for safe editing with undo/redo support
"""

from typing import Optional, List, Callable
from abc import ABC, abstractmethod


class Command(ABC):
    """Base command class for undo/redo"""
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo the command"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get command description"""
        pass


class UndoRedoManager:
    """Manages undo/redo stack"""
    
    def __init__(self, max_stack_size: int = 100):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_stack_size = max_stack_size
        self.current_command: Optional[Command] = None
    
    def execute_command(self, command: Command) -> bool:
        """Execute a command and add to undo stack"""
        if command.execute():
            self.undo_stack.append(command)
            self.redo_stack.clear()  # Clear redo stack
            
            # Limit stack size
            if len(self.undo_stack) > self.max_stack_size:
                self.undo_stack.pop(0)
            
            return True
        return False
    
    def undo(self) -> bool:
        """Undo last command"""
        if not self.undo_stack:
            return False
        
        command = self.undo_stack.pop()
        if command.undo():
            self.redo_stack.append(command)
            return True
        return False
    
    def redo(self) -> bool:
        """Redo last undone command"""
        if not self.redo_stack:
            return False
        
        command = self.redo_stack.pop()
        if command.execute():
            self.undo_stack.append(command)
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return len(self.redo_stack) > 0
    
    def clear(self):
        """Clear undo/redo stacks"""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of next undo"""
        if self.undo_stack:
            return self.undo_stack[-1].get_description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of next redo"""
        if self.redo_stack:
            return self.redo_stack[-1].get_description()
        return None


class PrimTransformCommand(Command):
    """Command for prim transform changes"""
    
    def __init__(self, prim_path: str, old_transform, new_transform, 
                 selection_manager, time_code: float = 0.0):
        self.prim_path = prim_path
        self.old_transform = old_transform
        self.new_transform = new_transform
        self.selection_manager = selection_manager
        self.time_code = time_code
    
    def execute(self) -> bool:
        """Apply new transform"""
        prim = self.selection_manager.stage.GetPrimAtPath(self.prim_path)
        if prim:
            return self.selection_manager.set_prim_transform(
                prim, self.new_transform, self.time_code
            )
        return False
    
    def undo(self) -> bool:
        """Restore old transform"""
        prim = self.selection_manager.stage.GetPrimAtPath(self.prim_path)
        if prim:
            return self.selection_manager.set_prim_transform(
                prim, self.old_transform, self.time_code
            )
        return False
    
    def get_description(self) -> str:
        """Get command description"""
        return f"Transform {self.prim_path}"


class AttributeChangeCommand(Command):
    """Command for attribute changes"""
    
    def __init__(self, prim_path: str, attr_name: str, old_value, new_value, stage):
        self.prim_path = prim_path
        self.attr_name = attr_name
        self.old_value = old_value
        self.new_value = new_value
        self.stage = stage
    
    def execute(self) -> bool:
        """Apply new value"""
        prim = self.stage.GetPrimAtPath(self.prim_path)
        if prim:
            attr = prim.GetAttribute(self.attr_name)
            if attr:
                attr.Set(self.new_value)
                return True
        return False
    
    def undo(self) -> bool:
        """Restore old value"""
        prim = self.stage.GetPrimAtPath(self.prim_path)
        if prim:
            attr = prim.GetAttribute(self.attr_name)
            if attr:
                attr.Set(self.old_value)
                return True
        return False
    
    def get_description(self) -> str:
        """Get command description"""
        return f"Change {self.attr_name} on {self.prim_path}"

