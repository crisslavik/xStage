"""
Tests for xStage managers
"""

import pytest
import tempfile
from pathlib import Path

try:
    from pxr import Usd, UsdGeom, UsdShade
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


def test_material_manager():
    """Test MaterialManager"""
    pytest.importorskip("pxr")
    
    from xstage.managers import MaterialManager
    from pxr import Usd, UsdShade
    
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        manager = MaterialManager()

        # Find materials on the stage (may be empty)
        materials = manager.find_all_materials(stage)
        assert isinstance(materials, list)

    finally:
        Path(stage_path).unlink()


def test_camera_manager():
    """Test CameraManager"""
    pytest.importorskip("pxr")
    
    from xstage.managers import CameraManager
    from pxr import Usd, UsdGeom
    
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        manager = CameraManager(stage)

        cameras = manager.find_all_cameras()
        assert isinstance(cameras, list)
        
    finally:
        Path(stage_path).unlink()


def test_collection_manager():
    """Test CollectionManager"""
    pytest.importorskip("pxr")
    
    from xstage.managers import CollectionManager
    from pxr import Usd
    
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        manager = CollectionManager()

        collections = manager.get_collections(stage.GetPseudoRoot())
        assert isinstance(collections, list)
        
    finally:
        Path(stage_path).unlink()


def test_variant_manager():
    """Test VariantManager"""
    pytest.importorskip("pxr")
    
    from xstage.managers import VariantManager
    from pxr import Usd
    
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        manager = VariantManager()

        variants = manager.get_variant_sets(stage.GetPseudoRoot())
        assert isinstance(variants, dict)
        
    finally:
        Path(stage_path).unlink()


def test_payload_manager():
    """Test PayloadManager"""
    pytest.importorskip("pxr")
    
    from xstage.managers import PayloadManager
    from pxr import Usd
    
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        manager = PayloadManager(stage)
        
        assert manager.stage == stage
        assert isinstance(manager.loaded_payloads, set)
        
    finally:
        Path(stage_path).unlink()


def test_layer_composition_manager():
    """Test LayerCompositionManager"""
    pytest.importorskip("pxr")
    
    from xstage.managers import LayerCompositionManager
    from pxr import Usd
    
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        manager = LayerCompositionManager(stage)
        
        layers = manager.get_layer_stack()
        assert isinstance(layers, list)
        
    finally:
        Path(stage_path).unlink()

