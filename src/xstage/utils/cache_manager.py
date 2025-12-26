"""
Smart Caching System
Geometry, texture, and scene state caching for performance
"""

from typing import Dict, Optional, Any, Callable
from pathlib import Path
import json
import hashlib
import time
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from pxr import Usd, UsdGeom, Gf, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class CacheType(Enum):
    """Cache types"""
    GEOMETRY = "geometry"
    TEXTURE = "texture"
    BOUNDS = "bounds"
    TRANSFORM = "transform"
    MATERIAL = "material"
    SCENE_STATE = "scene_state"


@dataclass
class CacheEntry:
    """Cache entry metadata"""
    cache_type: str
    key: str
    file_path: str
    file_hash: str
    created_at: float
    last_accessed: float
    size_bytes: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CacheManager:
    """Manages various caches for performance optimization"""
    
    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 1000):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".xstage" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Cache storage
        self.geometry_cache: Dict[str, Any] = {}
        self.bounds_cache: Dict[str, Any] = {}
        self.transform_cache: Dict[str, Any] = {}
        self.material_cache: Dict[str, Any] = {}
        self.scene_state_cache: Dict[str, Any] = {}
        
        # Cache metadata
        self.cache_metadata: Dict[str, CacheEntry] = {}
        self.load_metadata()
    
    def _get_file_hash(self, filepath: str) -> str:
        """Get hash of file for cache invalidation"""
        try:
            stat = Path(filepath).stat()
            # Use mtime and size for quick hash
            content = f"{filepath}:{stat.st_mtime}:{stat.st_size}"
            return hashlib.md5(content.encode()).hexdigest()
        except:
            return ""
    
    def _get_cache_key(self, cache_type: CacheType, identifier: str, 
                      filepath: Optional[str] = None, time_code: Optional[float] = None) -> str:
        """Generate cache key"""
        key_parts = [cache_type.value, identifier]
        if filepath:
            key_parts.append(self._get_file_hash(filepath))
        if time_code is not None:
            key_parts.append(str(time_code))
        return ":".join(key_parts)
    
    def get_geometry_cache(self, prim_path: str, filepath: str, time_code: float = 0.0) -> Optional[Any]:
        """Get cached geometry data"""
        key = self._get_cache_key(CacheType.GEOMETRY, prim_path, filepath, time_code)
        
        # Check if in memory cache
        if key in self.geometry_cache:
            self._update_access_time(key)
            return self.geometry_cache[key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"geometry_{hashlib.md5(key.encode()).hexdigest()}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.geometry_cache[key] = data
                    self._update_access_time(key)
                    return data
            except:
                pass
        
        return None
    
    def set_geometry_cache(self, prim_path: str, filepath: str, geometry_data: Any, time_code: float = 0.0):
        """Cache geometry data"""
        key = self._get_cache_key(CacheType.GEOMETRY, prim_path, filepath, time_code)
        self.geometry_cache[key] = geometry_data
        
        # Save to disk
        cache_file = self.cache_dir / f"geometry_{hashlib.md5(key.encode()).hexdigest()}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(geometry_data, f)
            
            # Update metadata
            self._update_cache_metadata(key, CacheType.GEOMETRY, filepath, len(str(geometry_data)))
        except Exception as e:
            print(f"Error caching geometry: {e}")
    
    def get_bounds_cache(self, prim_path: str, filepath: str) -> Optional[Gf.BBox3d]:
        """Get cached bounds"""
        key = self._get_cache_key(CacheType.BOUNDS, prim_path, filepath)
        
        if key in self.bounds_cache:
            self._update_access_time(key)
            return self.bounds_cache[key]
        
        return None
    
    def set_bounds_cache(self, prim_path: str, filepath: str, bounds: Gf.BBox3d):
        """Cache bounds"""
        key = self._get_cache_key(CacheType.BOUNDS, prim_path, filepath)
        self.bounds_cache[key] = bounds
        self._update_access_time(key)
    
    def get_transform_cache(self, prim_path: str, filepath: str, time_code: float = 0.0) -> Optional[Gf.Matrix4d]:
        """Get cached transform"""
        key = self._get_cache_key(CacheType.TRANSFORM, prim_path, filepath, time_code)
        
        if key in self.transform_cache:
            self._update_access_time(key)
            return self.transform_cache[key]
        
        return None
    
    def set_transform_cache(self, prim_path: str, filepath: str, transform: Gf.Matrix4d, time_code: float = 0.0):
        """Cache transform"""
        key = self._get_cache_key(CacheType.TRANSFORM, prim_path, filepath, time_code)
        self.transform_cache[key] = transform
        self._update_access_time(key)
    
    def get_material_cache(self, material_path: str, filepath: str) -> Optional[Dict]:
        """Get cached material data"""
        key = self._get_cache_key(CacheType.MATERIAL, material_path, filepath)
        
        if key in self.material_cache:
            self._update_access_time(key)
            return self.material_cache[key]
        
        return None
    
    def set_material_cache(self, material_path: str, filepath: str, material_data: Dict):
        """Cache material data"""
        key = self._get_cache_key(CacheType.MATERIAL, material_path, filepath)
        self.material_cache[key] = material_data
        self._update_access_time(key)
    
    def get_scene_state_cache(self, filepath: str) -> Optional[Dict]:
        """Get cached scene state (bookmarks, selections, etc.)"""
        key = self._get_cache_key(CacheType.SCENE_STATE, filepath, filepath)
        
        if key in self.scene_state_cache:
            return self.scene_state_cache[key]
        
        return None
    
    def set_scene_state_cache(self, filepath: str, state: Dict):
        """Cache scene state"""
        key = self._get_cache_key(CacheType.SCENE_STATE, filepath, filepath)
        self.scene_state_cache[key] = state
    
    def clear_cache(self, cache_type: Optional[CacheType] = None):
        """Clear cache"""
        if cache_type is None:
            # Clear all
            self.geometry_cache.clear()
            self.bounds_cache.clear()
            self.transform_cache.clear()
            self.material_cache.clear()
            self.scene_state_cache.clear()
        else:
            # Clear specific type
            if cache_type == CacheType.GEOMETRY:
                self.geometry_cache.clear()
            elif cache_type == CacheType.BOUNDS:
                self.bounds_cache.clear()
            elif cache_type == CacheType.TRANSFORM:
                self.transform_cache.clear()
            elif cache_type == CacheType.MATERIAL:
                self.material_cache.clear()
            elif cache_type == CacheType.SCENE_STATE:
                self.scene_state_cache.clear()
    
    def clear_cache_for_file(self, filepath: str):
        """Clear all cache entries for a specific file"""
        file_hash = self._get_file_hash(filepath)
        
        # Clear memory caches
        keys_to_remove = []
        for key in list(self.geometry_cache.keys()):
            if file_hash in key:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.geometry_cache[key]
        
        # Clear disk cache files
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if data.get('file_hash') == file_hash:
                        cache_file.unlink()
            except:
                pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                total_size += cache_file.stat().st_size
            except:
                pass
        
        return {
            'geometry_entries': len(self.geometry_cache),
            'bounds_entries': len(self.bounds_cache),
            'transform_entries': len(self.transform_cache),
            'material_entries': len(self.material_cache),
            'total_disk_size_mb': total_size / (1024 * 1024),
            'max_size_mb': self.max_size_mb,
        }
    
    def _update_access_time(self, key: str):
        """Update last access time for cache entry"""
        if key in self.cache_metadata:
            self.cache_metadata[key].last_accessed = time.time()
    
    def _update_cache_metadata(self, key: str, cache_type: CacheType, filepath: str, size: int):
        """Update cache metadata entry"""
        if key not in self.cache_metadata:
            self.cache_metadata[key] = CacheEntry(
                cache_type=cache_type.value,
                key=key,
                file_path=filepath,
                file_hash=self._get_file_hash(filepath),
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=size
            )
        else:
            self.cache_metadata[key].last_accessed = time.time()
            self.cache_metadata[key].size_bytes = size
    
    def load_metadata(self):
        """Load cache metadata from disk"""
        metadata_file = self.cache_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    self.cache_metadata = {
                        k: CacheEntry(**v) for k, v in data.items()
                    }
            except:
                pass
    
    def save_metadata(self):
        """Save cache metadata to disk"""
        metadata_file = self.cache_dir / "metadata.json"
        try:
            data = {
                k: asdict(v) for k, v in self.cache_metadata.items()
            }
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache metadata: {e}")

