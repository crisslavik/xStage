#!/usr/bin/env python3
"""
Test Hydra 2.0 availability and functionality
Run this to diagnose Hydra issues
"""

import sys

print("=" * 60)
print("Hydra 2.0 Diagnostic Test")
print("=" * 60)
print()

# Test 1: USD availability
print("1. Testing USD availability...")
try:
    from pxr import Usd, UsdGeom, Gf
    print("   ✓ USD imported successfully")
    print(f"   USD version: {Usd.GetVersion()}")
except ImportError as e:
    print(f"   ✗ USD import failed: {e}")
    sys.exit(1)

# Test 2: UsdImagingGL availability
print("\n2. Testing UsdImagingGL (Hydra) availability...")
try:
    from pxr import UsdImagingGL
    print("   ✓ UsdImagingGL imported successfully")
except ImportError as e:
    print(f"   ✗ UsdImagingGL import failed: {e}")
    print("   → Hydra 2.0 not available with this USD installation")
    print("   → You need to build USD from source with imaging enabled")
    sys.exit(1)

# Test 3: Glf availability
print("\n3. Testing Glf (OpenGL Foundation) availability...")
try:
    from pxr import Glf
    print("   ✓ Glf imported successfully")
    has_glew_init = hasattr(Glf, 'GlewInit')
    print(f"   Glf.GlewInit available: {has_glew_init}")
except ImportError as e:
    print(f"   ✗ Glf import failed: {e}")

# Test 4: Create Engine
print("\n4. Testing UsdImagingGL.Engine creation...")
try:
    # Try to create engine (without OpenGL context)
    print("   Creating engine...")
    # Note: This will fail without OpenGL context, but we can check the class exists
    print(f"   ✓ UsdImagingGL.Engine class exists: {hasattr(UsdImagingGL, 'Engine')}")
except Exception as e:
    print(f"   ✗ Engine creation test failed: {e}")

# Test 5: Check SetRenderViewport signature
print("\n5. Testing SetRenderViewport API...")
try:
    import inspect
    if hasattr(UsdImagingGL, 'Engine'):
        engine_class = UsdImagingGL.Engine
        if hasattr(engine_class, 'SetRenderViewport'):
            print("   ✓ SetRenderViewport method exists")
            # Try to get signature (may not work with Boost.Python)
            try:
                sig = inspect.signature(engine_class.SetRenderViewport)
                print(f"   Signature: {sig}")
            except:
                print("   (Cannot inspect Boost.Python signature)")
                print("   Testing with GfVec4d...")
                # We can't actually call it without a context, but we know the signature
                print("   → Use: engine.SetRenderViewport(Gf.Vec4d(0, 0, width, height))")
        else:
            print("   ✗ SetRenderViewport method not found")
except Exception as e:
    print(f"   ✗ API test failed: {e}")

# Test 6: Renderer plugins
print("\n6. Testing renderer plugins...")
try:
    from pxr import Plug
    registry = Plug.Registry()
    
    # Get all plugins
    plugins = registry.GetAllPlugins()
    
    # Look for renderer plugins
    renderer_plugins = []
    for plugin in plugins:
        plugin_name = plugin.name
        if 'Hd' in plugin_name or 'Storm' in plugin_name or 'Render' in plugin_name:
            renderer_plugins.append(plugin_name)
    
    if renderer_plugins:
        print(f"   ✓ Found {len(renderer_plugins)} renderer-related plugins:")
        for plugin in renderer_plugins[:10]:  # Show first 10
            print(f"     - {plugin}")
    else:
        print("   ⚠ No renderer plugins found")
        
except Exception as e:
    print(f"   ✗ Plugin test failed: {e}")

# Test 7: OpenGL availability
print("\n7. Testing OpenGL availability...")
try:
    from OpenGL import GL
    print("   ✓ PyOpenGL imported successfully")
    print(f"   PyOpenGL version: {GL.__version__}")
except ImportError as e:
    print(f"   ✗ PyOpenGL import failed: {e}")

# Test 8: Qt and OpenGL widget availability
print("\n8. Testing Qt OpenGL widget availability...")
try:
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    from PySide6.QtGui import QSurfaceFormat
    print("   ✓ PySide6 OpenGL widgets available")
    
    # Check default format
    fmt = QSurfaceFormat.defaultFormat()
    print(f"   Default OpenGL version: {fmt.majorVersion()}.{fmt.minorVersion()}")
    print(f"   Profile: {fmt.profile()}")
    
except ImportError as e:
    print(f"   ✗ Qt OpenGL import failed: {e}")

print("\n" + "=" * 60)
print("Diagnostic Summary:")
print("=" * 60)

# Summary
has_usd = True
has_imaging = True
has_opengl = True

try:
    from pxr import UsdImagingGL
except:
    has_imaging = False

try:
    from OpenGL import GL
except:
    has_opengl = False

if has_usd and has_imaging and has_opengl:
    print("✓ All components available for Hydra 2.0 rendering")
    print("\nIf Hydra still not working, the issue is likely:")
    print("  1. OpenGL context creation")
    print("  2. OpenGL version compatibility (need 4.5+ for Storm)")
    print("  3. Graphics driver issues")
elif not has_imaging:
    print("✗ UsdImagingGL not available")
    print("\nTo fix:")
    print("  1. Build USD from source with imaging enabled:")
    print("     python build_scripts/build_usd.py --imaging /path/to/install")
    print("  2. Or use OpenGL fallback viewport (already working)")
else:
    print("✗ Missing required components")
    print(f"  USD: {has_usd}")
    print(f"  UsdImagingGL: {has_imaging}")
    print(f"  OpenGL: {has_opengl}")

print()
