#!/usr/bin/env python3
"""
Check USD Rendering Capabilities
Diagnoses why USD rendering might not be working
"""

import sys

print("=" * 70)
print("USD Rendering Diagnostic")
print("=" * 70)
print()

# Check Python version
print(f"Python: {sys.version}")
print(f"Python executable: {sys.executable}")
print()

# Check USD availability
print("1. Checking USD Python bindings...")
try:
    from pxr import Usd
    print(f"   ✅ USD available: {Usd.GetVersion()}")
    USD_VERSION = Usd.GetVersion()
except ImportError as e:
    print(f"   ❌ USD not available: {e}")
    print()
    print("   SOLUTION: Install USD:")
    print("     pip install usd-core>=25.11")
    sys.exit(1)

# Check UsdImagingGL (required for Hydra rendering)
print()
print("2. Checking UsdImagingGL (Hydra rendering)...")
try:
    from pxr import UsdImagingGL
    print("   ✅ UsdImagingGL available")
    USD_IMAGING_AVAILABLE = True
except ImportError as e:
    print(f"   ❌ UsdImagingGL NOT available: {e}")
    print()
    print("   ⚠️  PROBLEM: Your USD installation doesn't include imaging support!")
    print()
    print("   The 'usd-core' package from PyPI is a minimal build that doesn't")
    print("   include UsdImagingGL (Hydra rendering).")
    print()
    print("   SOLUTIONS:")
    print()
    print("   Option 1: Use a full USD build with imaging support")
    print("   - Download pre-built USD from NVIDIA or Pixar")
    print("   - Or build USD from source with imaging enabled")
    print("   - See: https://github.com/PixarAnimationStudios/USD")
    print()
    print("   Option 2: Use xStage's OpenGL fallback (current)")
    print("   - xStage will use basic OpenGL rendering")
    print("   - Works but lacks advanced features (materials, lighting, etc.)")
    print()
    USD_IMAGING_AVAILABLE = False

# Check Glf (GL Framework - required for Storm renderer)
print()
print("3. Checking Glf (GL Framework)...")
try:
    from pxr import Glf
    print("   ✅ Glf available")
    GLF_AVAILABLE = True
except ImportError as e:
    print(f"   ❌ Glf NOT available: {e}")
    GLF_AVAILABLE = False

# Check available renderers
if USD_IMAGING_AVAILABLE:
    print()
    print("4. Checking available Hydra renderers...")
    try:
        engine = UsdImagingGL.Engine()
        renderers = engine.GetRendererPlugins()
        print(f"   Available renderers: {renderers}")
        
        if 'HdStormRendererPlugin' in renderers:
            print("   ✅ Storm renderer (GPU-accelerated) available")
        else:
            print("   ⚠️  Storm renderer NOT available")
            print("   This means GPU-accelerated rendering won't work")
    except Exception as e:
        print(f"   ❌ Could not check renderers: {e}")

# Check OpenGL
print()
print("5. Checking OpenGL support...")
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    from OpenGL import GL
    
    app = QApplication.instance() or QApplication([])
    widget = QOpenGLWidget()
    widget.show()
    widget.makeCurrent()
    
    version = GL.glGetString(GL.GL_VERSION)
    vendor = GL.glGetString(GL.GL_VENDOR)
    renderer = GL.glGetString(GL.GL_RENDERER)
    
    if version:
        version_str = version.decode() if isinstance(version, bytes) else str(version)
        vendor_str = vendor.decode() if isinstance(vendor, bytes) else str(vendor)
        renderer_str = renderer.decode() if isinstance(renderer, bytes) else str(renderer)
        
        print(f"   ✅ OpenGL Version: {version_str}")
        print(f"   ✅ Vendor: {vendor_str}")
        print(f"   ✅ Renderer: {renderer_str}")
        
        # Check version
        try:
            major = int(version_str.split('.')[0])
            if major >= 4:
                print("   ✅ OpenGL 4.x+ (good for rendering)")
            elif major >= 3:
                print("   ⚠️  OpenGL 3.x (may have limitations)")
            else:
                print("   ⚠️  OpenGL < 3.0 (very limited)")
        except:
            pass
    
    widget.close()
except Exception as e:
    print(f"   ❌ OpenGL check failed: {e}")

# Summary
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()

if USD_IMAGING_AVAILABLE:
    print("✅ USD rendering (Hydra) should work!")
    print("   You can use Tools > Use Hydra 2.0 Rendering")
else:
    print("⚠️  USD rendering (Hydra) is NOT available")
    print()
    print("   xStage will use OpenGL fallback rendering:")
    print("   - ✅ Basic geometry rendering works")
    print("   - ✅ Camera controls work")
    print("   - ❌ Advanced materials may not render correctly")
    print("   - ❌ Complex lighting may not work")
    print("   - ❌ Performance may be slower")
    print()
    print("   To get full USD rendering support:")
    print("   1. Install a full USD build with imaging support")
    print("   2. Or use NVIDIA Omniverse for full-featured USD viewing")

print()
print("=" * 70)
