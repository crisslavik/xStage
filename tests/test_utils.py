"""
Tests for xStage utilities
"""

import pytest
from pathlib import Path
import tempfile

try:
    from pxr import Usd
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


def test_theme_manager():
    """Test ThemeManager"""
    from xstage.utils import ThemeManager, ThemeMode
    
    manager = ThemeManager()
    assert manager is not None
    
    # Test theme modes
    assert ThemeMode.DARK is not None
    assert ThemeMode.LIGHT is not None
    assert ThemeMode.HIGH_CONTRAST is not None


def test_recent_files_manager():
    """Test RecentFilesManager"""
    from xstage.utils import RecentFilesManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "recent_files.json"
        manager = RecentFilesManager(config_path=config_path)
        
        # Add a file
        manager.add_file("/test/path/file.usd", "usd", "Test Stage")
        
        # Get recent files
        recent = manager.get_recent_files()
        assert len(recent) == 1
        assert recent[0].path == "/test/path/file.usd"
        assert recent[0].file_type == "usd"
        
        # Remove file
        manager.remove_file("/test/path/file.usd")
        recent = manager.get_recent_files()
        assert len(recent) == 0


def test_bookmark_manager():
    """Test BookmarkManager"""
    from xstage.utils import BookmarkManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "bookmarks.json"
        manager = BookmarkManager(config_path=config_path)
        
        from xstage.utils.bookmarks import Bookmark
        
        bookmark = Bookmark(
            name="Test Bookmark",
            stage_path="/test/stage.usd",
            prim_path="/World/Mesh"
        )
        
        manager.add_bookmark(bookmark)
        
        bookmarks = manager.get_bookmarks_for_stage("/test/stage.usd")
        assert len(bookmarks) == 1
        assert bookmarks[0].name == "Test Bookmark"


def test_annotation_manager():
    """Test AnnotationManager"""
    from xstage.utils import AnnotationManager
    from xstage.utils.annotations import Annotation
    
    manager = AnnotationManager()
    
    annotation = Annotation(
        type="text",
        text="Test annotation",
        position={"x": 100, "y": 200}
    )
    
    manager.add_annotation(annotation)
    assert len(manager.annotations) == 1
    
    manager.remove_annotation(annotation.id)
    assert len(manager.annotations) == 0


def test_cache_manager():
    """Test CacheManager"""
    from xstage.utils import CacheManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cache"
        manager = CacheManager(cache_dir=cache_dir)
        
        assert manager is not None
        assert manager.cache_dir == cache_dir
        
        # Test cache stats
        stats = manager.get_cache_stats()
        assert 'total_files' in stats
        assert 'total_disk_size_mb' in stats


def test_viewport_overlay():
    """Test ViewportOverlay"""
    from xstage.utils import ViewportOverlay
    
    overlay = ViewportOverlay()
    assert overlay is not None
    assert overlay.show_fps == True
    assert overlay.show_stats == True


def test_color_space_manager():
    """Test ColorSpaceManager"""
    pytest.importorskip("pxr")
    
    from xstage.utils import ColorSpaceManager
    from pxr import Usd
    
    manager = ColorSpaceManager()
    assert manager is not None
    
    # Test with a stage
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        color_space = manager.get_default_color_space(stage)
        # May be None if not set, which is OK
        assert color_space is None or isinstance(color_space, str)
    finally:
        Path(stage_path).unlink()


def test_validation_manager():
    """Test ValidationManager"""
    pytest.importorskip("pxr")
    
    from xstage.utils import ValidationManager
    from pxr import Usd
    
    manager = ValidationManager()
    assert manager is not None
    
    # Test validation
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        stage.GetRootLayer().Save()
        
        results = manager.validate_stage(stage_path)
        assert isinstance(results, list)
    finally:
        Path(stage_path).unlink()

