#!/usr/bin/env python3
"""
xStage Hydra 2.0 Diagnostic Script
Run this to diagnose Hydra rendering issues
"""

import sys
import os

print("=" * 60)
print("xStage Hydra 2.0 Diagnostic")
print("=" * 60)

# Python version
print(f"\n📋 Python: {sys.version}")
print(f"   Executable: {sys.executable}")

# USD availability
print("\n📦 USD Modules:")
try:
    from pxr import Usd, UsdGeom, UsdImagingGL, Gf, Hd
    print(f"   ✅ USD modules loaded")
    print(f"   USD Version: {Usd.GetVersion()}")
    
    # Check USD version
    version_str = Usd.GetVersion()
    version_tuple = tuple(map(int, version_str.split('.')))
    if version_tuple >= (0, 25, 11):
        print(f"   ✅ USD 25.11+ detected (Hydra 2.0 compatible)")
    else:
        print(f"   ⚠️  USD {version_str} detected (may not have full Hydra 2.0 support)")
        
except ImportError as e:
    print(f"   ❌ USD import failed: {e}")
    print(f"   Install with: pip install usd-core>=25.11")
    sys.exit(1)

# Check Hydra engine
print("\n🔧 Hydra Engine:")
try:
    engine = UsdImagingGL.Engine()
    print("   ✅ Engine created successfully")
    
    # Check available renderers
    try:
        renderers = engine.GetRendererPlugins()
        print(f"   Available renderers: {renderers}")
        
        if 'HdStormRendererPlugin' in renderers:
            print("   ✅ Storm (Hydra GPU) available")
            
            # Try to set it
            try:
                engine.SetRendererPlugin('HdStormRendererPlugin')
                current = engine.GetCurrentRendererId()
                print(f"   ✅ Storm renderer active: {current}")
            except Exception as e:
                print(f"   ❌ Failed to set Storm: {e}")
        else:
            print("   ❌ Storm NOT available")
            print("   Possible causes:")
            print("     - OpenGL < 4.5")
            print("     - GPU drivers not installed")
            print("     - USD built without Storm support")
            
    except Exception as e:
        print(f"   ⚠️  Could not get renderer plugins: {e}")
    
    # Check Scene Index (Hydra 2.0)
    try:
        engine.SetEnableSceneIndex(True)
        print("   ✅ Scene Index (Hydra 2.0) enabled")
    except Exception as e:
        print(f"   ⚠️  Scene Index enable failed: {e}")
        print("   This may indicate Hydra 1.0 (legacy)")
        
except Exception as e:
    print(f"   ❌ Engine creation failed: {e}")
    import traceback
    traceback.print_exc()

# Check OpenGL
print("\n🖥️  OpenGL:")
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    from OpenGL import GL
    
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    
    widget = QOpenGLWidget()
    widget.show()
    widget.makeCurrent()
    
    try:
        version_str = GL.glGetString(GL.GL_VERSION)
        if version_str:
            version = version_str.decode() if isinstance(version_str, bytes) else str(version_str)
            print(f"   Version: {version}")
            
            # Check version number
            try:
                major = int(version.split('.')[0])
                minor = int(version.split('.')[1].split()[0])
                if major > 4 or (major == 4 and minor >= 5):
                    print("   ✅ OpenGL 4.5+ (Storm compatible)")
                elif major == 4:
                    print(f"   ⚠️  OpenGL 4.{minor} (Storm may work)")
                else:
                    print(f"   ❌ OpenGL {major}.{minor} (Storm requires 4.5+)")
            except:
                pass
        else:
            print("   ⚠️  Could not get OpenGL version")
            
        vendor = GL.glGetString(GL.GL_VENDOR)
        if vendor:
            vendor_str = vendor.decode() if isinstance(vendor, bytes) else str(vendor)
            print(f"   Vendor: {vendor_str}")
            
        renderer = GL.glGetString(GL.GL_RENDERER)
        if renderer:
            renderer_str = renderer.decode() if isinstance(renderer, bytes) else str(renderer)
            print(f"   Renderer: {renderer_str}")
            
    except Exception as e:
        print(f"   ❌ OpenGL info failed: {e}")
    
    widget.close()
    
except Exception as e:
    print(f"   ❌ OpenGL check failed: {e}")
    import traceback
    traceback.print_exc()

# Check system
print("\n💻 System:")
try:
    import platform
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Architecture: {platform.machine()}")
except:
    pass

# Check environment
print("\n🌍 Environment:")
env_vars = ['DISPLAY', 'QT_QPA_PLATFORM', 'QT_OPENGL', 'LD_LIBRARY_PATH']
for var in env_vars:
    value = os.environ.get(var, 'Not set')
    if value != 'Not set':
        print(f"   {var}: {value}")

print("\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)
print("\n💡 Next Steps:")
print("   1. If Storm is not available, check GPU drivers")
print("   2. If Scene Index fails, USD may be built without Hydra 2.0")
print("   3. If OpenGL < 4.5, update graphics drivers")
print("   4. Check USD build configuration for Storm support")
