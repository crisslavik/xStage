"""
Recent Files Management
Track and manage recently opened files
"""

from typing import List, Optional
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from pxr import Usd
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


@dataclass
class RecentFile:
    """Recent file entry"""
    path: str
    timestamp: float
    file_type: str = "usd"  # usd, fbx, obj, etc.
    stage_name: Optional[str] = None


class RecentFilesManager:
    """Manages recent files list"""
    
    MAX_RECENT_FILES = 20
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(Path.home() / ".xstage" / "recent_files.json")
        self.recent_files: List[RecentFile] = []
        self.load()
    
    def add_file(self, filepath: str, file_type: str = "usd"):
        """Add a file to recent files"""
        filepath = str(Path(filepath).resolve())
        
        # Remove if already exists
        self.recent_files = [f for f in self.recent_files if f.path != filepath]
        
        # Get stage name if USD
        stage_name = None
        if file_type == "usd" and USD_AVAILABLE:
            try:
                stage = Usd.Stage.Open(filepath)
                if stage:
                    root_prim = stage.GetDefaultPrim()
                    if root_prim:
                        stage_name = root_prim.GetName()
            except:
                pass
        
        # Add to front
        recent_file = RecentFile(
            path=filepath,
            timestamp=datetime.now().timestamp(),
            file_type=file_type,
            stage_name=stage_name
        )
        self.recent_files.insert(0, recent_file)
        
        # Limit size
        self.recent_files = self.recent_files[:self.MAX_RECENT_FILES]
        
        self.save()
    
    def get_recent_files(self, limit: Optional[int] = None) -> List[RecentFile]:
        """Get recent files list"""
        files = self.recent_files
        if limit:
            files = files[:limit]
        return files
    
    def clear(self):
        """Clear recent files"""
        self.recent_files.clear()
        self.save()
    
    def remove_file(self, filepath: str):
        """Remove a file from recent files"""
        self.recent_files = [f for f in self.recent_files if f.path != filepath]
        self.save()
    
    def save(self):
        """Save recent files to disk"""
        try:
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                'recent_files': [asdict(f) for f in self.recent_files]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving recent files: {e}")
    
    def load(self):
        """Load recent files from disk"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                self.recent_files = [
                    RecentFile(**f_data) for f_data in data.get('recent_files', [])
                ]
                
                # Filter out non-existent files
                self.recent_files = [
                    f for f in self.recent_files if Path(f.path).exists()
                ]
        except Exception as e:
            print(f"Error loading recent files: {e}")
            self.recent_files = []

