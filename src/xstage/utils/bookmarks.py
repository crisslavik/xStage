"""
Bookmarks System
Bookmark frequently used prims, cameras, and locations
"""

from typing import List, Dict, Optional
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from pxr import Usd, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class BookmarkType(Enum):
    """Types of bookmarks"""
    PRIM = "prim"
    CAMERA = "camera"
    LOCATION = "location"
    MATERIAL = "material"
    COLLECTION = "collection"


@dataclass
class Bookmark:
    """Single bookmark"""
    id: str
    name: str
    type: BookmarkType
    prim_path: Optional[str] = None
    stage_path: Optional[str] = None  # USD file path
    position: Optional[tuple] = None  # 3D position
    camera_transform: Optional[Dict] = None
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class BookmarkManager:
    """Manages bookmarks"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(Path.home() / ".xstage" / "bookmarks.json")
        self.bookmarks: List[Bookmark] = []
        self.load()
    
    def add_bookmark(self, bookmark: Bookmark) -> str:
        """Add a bookmark"""
        self.bookmarks.append(bookmark)
        self.save()
        return bookmark.id
    
    def add_prim_bookmark(self, name: str, prim_path: str, stage_path: str,
                         description: str = "", tags: List[str] = None) -> str:
        """Add a prim bookmark"""
        import uuid
        bookmark = Bookmark(
            id=str(uuid.uuid4()),
            name=name,
            type=BookmarkType.PRIM,
            prim_path=prim_path,
            stage_path=stage_path,
            description=description,
            tags=tags or []
        )
        return self.add_bookmark(bookmark)
    
    def add_camera_bookmark(self, name: str, camera_path: str, stage_path: str,
                           camera_transform: Dict, description: str = "") -> str:
        """Add a camera bookmark"""
        import uuid
        bookmark = Bookmark(
            id=str(uuid.uuid4()),
            name=name,
            type=BookmarkType.CAMERA,
            prim_path=camera_path,
            stage_path=stage_path,
            camera_transform=camera_transform,
            description=description
        )
        return self.add_bookmark(bookmark)
    
    def add_location_bookmark(self, name: str, position: tuple, stage_path: str,
                             description: str = "") -> str:
        """Add a location bookmark"""
        import uuid
        bookmark = Bookmark(
            id=str(uuid.uuid4()),
            name=name,
            type=BookmarkType.LOCATION,
            position=position,
            stage_path=stage_path,
            description=description
        )
        return self.add_bookmark(bookmark)
    
    def remove_bookmark(self, bookmark_id: str) -> bool:
        """Remove a bookmark"""
        for i, bm in enumerate(self.bookmarks):
            if bm.id == bookmark_id:
                self.bookmarks.pop(i)
                self.save()
                return True
        return False
    
    def get_bookmarks_for_stage(self, stage_path: str) -> List[Bookmark]:
        """Get bookmarks for a specific stage"""
        return [bm for bm in self.bookmarks if bm.stage_path == stage_path]
    
    def get_bookmarks_by_type(self, bookmark_type: BookmarkType) -> List[Bookmark]:
        """Get bookmarks by type"""
        return [bm for bm in self.bookmarks if bm.type == bookmark_type]
    
    def get_bookmarks_by_tag(self, tag: str) -> List[Bookmark]:
        """Get bookmarks by tag"""
        return [bm for bm in self.bookmarks if tag in bm.tags]
    
    def save(self):
        """Save bookmarks to disk"""
        try:
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                'bookmarks': [asdict(bm) for bm in self.bookmarks]
            }
            
            # Convert enums to strings
            for bm_data in data['bookmarks']:
                bm_data['type'] = bm_data['type'].value if isinstance(bm_data['type'], BookmarkType) else bm_data['type']
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    
    def load(self):
        """Load bookmarks from disk"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                self.bookmarks = []
                for bm_data in data.get('bookmarks', []):
                    # Convert type string back to enum
                    bm_data['type'] = BookmarkType(bm_data.get('type', 'prim'))
                    bookmark = Bookmark(**bm_data)
                    self.bookmarks.append(bookmark)
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            self.bookmarks = []

