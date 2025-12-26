"""
Tests for xStage converters
"""

import pytest
import tempfile
from pathlib import Path

try:
    from pxr import Usd, UsdGeom
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


def test_converter_initialization():
    """Test USDConverter initialization"""
    from xstage.converters import USDConverter, ConversionOptions
    
    options = ConversionOptions()
    converter = USDConverter(options)
    
    assert converter.options == options
    assert converter.supported_formats is not None
    assert '.usd' not in converter.supported_formats  # USD is output, not input


def test_conversion_options_defaults():
    """Test ConversionOptions default values"""
    from xstage.converters import ConversionOptions
    
    opts = ConversionOptions()
    assert opts.up_axis == 'Y'
    assert opts.meters_per_unit == 1.0
    assert opts.scale == 1.0
    assert opts.export_materials == True
    assert opts.export_normals == True
    assert opts.export_uvs == True
    assert opts.material_shader_type == "auto"


def test_material_creator():
    """Test MaterialCreator initialization"""
    pytest.importorskip("pxr")
    
    from xstage.converters.material_creator import MaterialCreator, MaterialShaderType
    
    # Test auto-detection
    creator = MaterialCreator(shader_type="auto")
    assert creator.shader_type in [MaterialShaderType.XMATERIAL, MaterialShaderType.PREVIEW_SURFACE]
    
    # Test explicit types
    creator_preview = MaterialCreator(shader_type="UsdPreviewSurface")
    assert creator_preview.shader_type == MaterialShaderType.PREVIEW_SURFACE


def test_material_creator_with_stage():
    """Test MaterialCreator with USD stage"""
    pytest.importorskip("pxr")
    
    from pxr import Usd, UsdShade
    from xstage.converters.material_creator import MaterialCreator
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        
        creator = MaterialCreator(shader_type="auto")
        material = creator.create_material(
            stage=stage,
            material_path="/Materials/TestMaterial",
            material_data={
                'baseColor': [0.8, 0.2, 0.2],
                'metallic': 0.5,
                'roughness': 0.3
            }
        )
        
        assert material is not None
        assert isinstance(material, UsdShade.Material)
        
    finally:
        Path(stage_path).unlink()


def test_adobe_converter_detection():
    """Test Adobe converter plugin detection"""
    pytest.importorskip("pxr")
    
    from xstage.converters import AdobeUSDConverter, ConversionOptions
    
    options = ConversionOptions()
    converter = AdobeUSDConverter(options, auto_install=False)
    
    # Should not fail even if plugins not available
    assert hasattr(converter, 'adobe_plugins_available')
    assert isinstance(converter.adobe_plugins_available, bool)


def test_converter_supported_formats():
    """Test converter supported formats"""
    from xstage.converters import USDConverter, ConversionOptions
    
    options = ConversionOptions()
    converter = USDConverter(options)
    
    # Check common formats
    assert '.fbx' in converter.supported_formats
    assert '.obj' in converter.supported_formats
    assert '.abc' in converter.supported_formats
    assert '.gltf' in converter.supported_formats
    assert '.glb' in converter.supported_formats
    assert '.stl' in converter.supported_formats
    assert '.ply' in converter.supported_formats

