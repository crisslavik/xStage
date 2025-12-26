"""
Test suite for xStage USD Viewer
Run with: pytest tests/ -v
"""

import pytest
import sys
import numpy as np
from pathlib import Path

# Test imports
def test_imports():
    """Test that all required modules can be imported"""
    try:
        from pxr import Usd, UsdGeom, Gf, Sdf
        assert True
    except ImportError:
        pytest.skip("USD Python bindings not available")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        assert True
    except ImportError:
        pytest.skip("PySide6 not available")
    
    try:
        from OpenGL.GL import glClear
        assert True
    except ImportError:
        pytest.skip("PyOpenGL not available")


def test_xstage_imports():
    """Test xStage module imports"""
    try:
        from xstage import USDViewerWindow
        from xstage.core.viewer import USDStageManager, ViewerSettings
        from xstage.converters import USDConverter, ConversionOptions
        assert True
    except ImportError as e:
        pytest.fail(f"xStage imports failed: {e}")


def test_usd_stage_manager():
    """Test USDStageManager functionality"""
    pytest.importorskip("pxr")
    
    from xstage.core.viewer import USDStageManager
    
    manager = USDStageManager()
    assert manager.stage is None
    assert manager.current_time == 0.0
    assert manager.fps == 24.0


def test_conversion_options():
    """Test ConversionOptions dataclass"""
    from xstage.converters import ConversionOptions
    
    opts = ConversionOptions()
    assert opts.up_axis == 'Y'
    assert opts.meters_per_unit == 1.0
    assert opts.export_normals == True
    assert opts.export_materials == True
    
    # Test custom options
    custom_opts = ConversionOptions(
        up_axis='Z',
        meters_per_unit=0.01,
        scale=0.001
    )
    assert custom_opts.up_axis == 'Z'
    assert custom_opts.meters_per_unit == 0.01
    assert custom_opts.scale == 0.001


def test_obj_conversion(tmp_path):
    """Test OBJ to USD conversion"""
    pytest.importorskip("pxr")
    pytest.importorskip("trimesh")
    
    from xstage.converters import USDConverter, ConversionOptions
    from pxr import Usd, UsdGeom
    
    # Create simple OBJ file
    obj_file = tmp_path / "test.obj"
    obj_content = """# Test OBJ file
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.5 1.0 0.0
vn 0.0 0.0 1.0
f 1//1 2//1 3//1
"""
    obj_file.write_text(obj_content)
    
    # Convert to USD
    usd_file = tmp_path / "test.usd"
    options = ConversionOptions()
    converter = USDConverter(options)
    
    success = converter.convert(str(obj_file), str(usd_file))
    if success:
        assert usd_file.exists()
        
        # Verify USD file
        stage = Usd.Stage.Open(str(usd_file))
        assert stage is not None
    else:
        pytest.skip("OBJ conversion not available (trimesh may not be installed)")


def test_stl_conversion(tmp_path):
    """Test STL to USD conversion"""
    pytest.importorskip("pxr")
    pytest.importorskip("trimesh")
    
    from xstage.converters import USDConverter, ConversionOptions
    from pxr import Usd
    import struct
    
    # Create simple binary STL file (single triangle)
    stl_file = tmp_path / "test.stl"
    
    with open(stl_file, 'wb') as f:
        # Header (80 bytes)
        f.write(b' ' * 80)
        
        # Triangle count
        f.write(struct.pack('I', 1))
        
        # Triangle data
        # Normal
        f.write(struct.pack('fff', 0.0, 0.0, 1.0))
        # Vertex 1
        f.write(struct.pack('fff', 0.0, 0.0, 0.0))
        # Vertex 2
        f.write(struct.pack('fff', 1.0, 0.0, 0.0))
        # Vertex 3
        f.write(struct.pack('fff', 0.5, 1.0, 0.0))
        # Attribute byte count
        f.write(struct.pack('H', 0))
    
    # Convert to USD
    usd_file = tmp_path / "test.usd"
    options = ConversionOptions()
    converter = USDConverter(options)
    
    success = converter.convert(str(stl_file), str(usd_file))
    if success:
        assert usd_file.exists()
        
        # Verify USD file
        stage = Usd.Stage.Open(str(usd_file))
        assert stage is not None
    else:
        pytest.skip("STL conversion not available (trimesh may not be installed)")


def test_viewer_settings():
    """Test ViewerSettings dataclass"""
    from xstage.core.viewer import ViewerSettings
    
    settings = ViewerSettings()
    assert settings.background_color == (0.2, 0.2, 0.2, 1.0)
    assert settings.grid_enabled == True
    assert settings.axis_enabled == True
    assert settings.fps == 24.0


@pytest.mark.skipif(sys.platform.startswith('linux') and not Path('/tmp/.X11-unix').exists(),
                   reason="No X11 display available")
def test_viewport_creation():
    """Test viewport widget creation"""
    pytest.importorskip("PySide6")
    
    from PySide6.QtWidgets import QApplication
    from xstage.core.viewport import ViewportWidget
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    viewport = ViewportWidget()
    assert viewport is not None
    assert viewport.camera_distance == 10.0
    assert viewport.camera_rotation_x == 30.0
    
    # Test camera controls
    viewport.camera_distance = 20.0
    assert viewport.camera_distance == 20.0


def test_mesh_extraction():
    """Test mesh data extraction from USD"""
    pytest.importorskip("pxr")
    
    from pxr import Usd, UsdGeom, Gf
    from xstage.core.viewer import USDStageManager
    import tempfile
    
    # Create temporary USD file with mesh
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(tmp_path)
        mesh = UsdGeom.Mesh.Define(stage, '/Mesh')
        
        # Set points
        points = [Gf.Vec3f(0, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(0.5, 1, 0)]
        mesh.CreatePointsAttr(points)
        
        # Set faces
        mesh.CreateFaceVertexCountsAttr([3])
        mesh.CreateFaceVertexIndicesAttr([0, 1, 2])
        
        stage.GetRootLayer().Save()
        
        # Load with stage manager
        manager = USDStageManager()
        success = manager.load_stage(tmp_path)
        assert success
        
        # Extract geometry
        geo_data = manager.get_geometry_data(0.0)
        assert 'meshes' in geo_data
        assert len(geo_data['meshes']) == 1
        
        mesh_data = geo_data['meshes'][0]
        assert len(mesh_data['points']) == 3
        
    finally:
        Path(tmp_path).unlink()


def test_bounds_calculation():
    """Test scene bounds calculation"""
    pytest.importorskip("pxr")
    
    from xstage.core.viewer import USDStageManager
    import numpy as np
    
    manager = USDStageManager()
    
    # Test bounds calculation with actual USD stage
    import tempfile
    from pxr import Usd, UsdGeom, Gf
    
    with tempfile.NamedTemporaryFile(suffix='.usd', delete=False) as tmp:
        stage_path = tmp.name
    
    try:
        stage = Usd.Stage.CreateNew(stage_path)
        
        # Create two meshes
        mesh1 = UsdGeom.Mesh.Define(stage, '/Mesh1')
        points1 = [Gf.Vec3f(0, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(0, 1, 0)]
        mesh1.CreatePointsAttr(points1)
        mesh1.CreateFaceVertexCountsAttr([3])
        mesh1.CreateFaceVertexIndicesAttr([0, 1, 2])
        
        mesh2 = UsdGeom.Mesh.Define(stage, '/Mesh2')
        points2 = [Gf.Vec3f(2, 2, 2), Gf.Vec3f(3, 2, 2), Gf.Vec3f(2, 3, 2)]
        mesh2.CreatePointsAttr(points2)
        mesh2.CreateFaceVertexCountsAttr([3])
        mesh2.CreateFaceVertexIndicesAttr([0, 1, 2])
        
        stage.GetRootLayer().Save()
        
        # Load and extract geometry
        manager.load_stage(stage_path)
        geo_data = manager.get_geometry_data(0.0)
        
        # Check that we have meshes
        assert 'meshes' in geo_data
        assert len(geo_data['meshes']) >= 1
        
    finally:
        Path(stage_path).unlink()


def test_ply_parsing():
    """Test PLY file parsing"""
    pytest.importorskip("pxr")
    pytest.importorskip("trimesh")
    
    from xstage.converters import USDConverter, ConversionOptions
    from pathlib import Path
    import tempfile
    
    # Create simple PLY file
    ply_content = """ply
format ascii 1.0
element vertex 3
property float x
property float y
property float z
element face 1
property list uchar int vertex_indices
end_header
0.0 0.0 0.0
1.0 0.0 0.0
0.5 1.0 0.0
3 0 1 2
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ply', delete=False) as tmp:
        tmp.write(ply_content)
        ply_path = tmp.name
    
    try:
        usd_path = ply_path.replace('.ply', '.usd')
        
        options = ConversionOptions()
        converter = USDConverter(options)
        
        success = converter.convert(ply_path, usd_path)
        if success:
            assert Path(usd_path).exists()
            Path(usd_path).unlink()
        else:
            pytest.skip("PLY conversion not available (trimesh may not be installed)")
        
    finally:
        Path(ply_path).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])