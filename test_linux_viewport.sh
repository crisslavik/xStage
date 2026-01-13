#!/bin/bash
# Linux Viewport Test Script
# Tests the viewport fixes and provides debugging information

echo "=== xStage Linux Viewport Test ==="
echo "Date: $(date)"
echo "System: $(uname -a)"
echo ""

# Check OpenGL
echo "1. OpenGL Information:"
if command -v glxinfo >/dev/null 2>&1; then
    echo "OpenGL Version: $(glxinfo | grep 'OpenGL version' | head -1)"
    echo "OpenGL Renderer: $(glxinfo | grep 'OpenGL renderer' | head -1)"
    echo "OpenGL Vendor: $(glxinfo | grep 'OpenGL vendor' | head -1)"
else
    echo "glxinfo not found. Installing..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y mesa-utils
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y mesa-dri-drivers
    fi
fi

echo ""

# Test basic OpenGL
echo "2. Basic OpenGL Test:"
if command -v glxgears >/dev/null 2>&1; then
    echo "Running glxgears for 3 seconds..."
    timeout 3s glxgears >/dev/null 2>&1
    if [ $? -eq 124 ]; then
        echo "✓ OpenGL basic test passed"
    else
        echo "✗ OpenGL basic test failed"
    fi
else
    echo "glxgears not available"
fi

echo ""

# Check Qt
echo "3. Qt Information:"
python3 -c "
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    print('✓ PySide6 with OpenGL support available')
    
    # Test OpenGL format
    from PySide6.QtGui import QSurfaceFormat
    fmt = QSurfaceFormat.defaultFormat()
    print(f'OpenGL Version: {fmt.version()}')
    print(f'OpenGL Profile: {fmt.profile()}')
except ImportError as e:
    print(f'✗ Qt import error: {e}')
except Exception as e:
    print(f'✗ Qt error: {e}')
"

echo ""

# Check USD
echo "4. USD Information:"
python3 -c "
try:
    from pxr import Usd, UsdGeom
    print('✓ USD available')
    print(f'USD Version: {Usd.GetVersion()}')
    
    # Test basic USD functionality
    stage = Usd.Stage.CreateInMemory()
    if stage:
        print('✓ USD basic functionality working')
    else:
        print('✗ USD stage creation failed')
except ImportError as e:
    print(f'✗ USD import error: {e}')
except Exception as e:
    print(f'✗ USD error: {e}')
"

echo ""

# Environment check
echo "5. Environment Variables:"
echo "DISPLAY: $DISPLAY"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "PYTHONPATH: $PYTHONPATH"
echo "QT_QPA_PLATFORM: $QT_QPA_PLATFORM"

echo ""

# Test xStage launch
echo "6. xStage Launch Test:"
if [ -f "./launch_usd_viewer.sh" ]; then
    echo "Testing xStage launch (will exit after 5 seconds)..."
    timeout 5s ./launch_usd_viewer.sh >/dev/null 2>&1
    case $? in
        124) echo "✓ xStage launched successfully (timed out as expected)" ;;
        0) echo "✓ xStage launched and closed cleanly" ;;
        *) echo "✗ xStage launch failed" ;;
    esac
else
    echo "launch_usd_viewer.sh not found"
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "If you see any ✗ marks above, those issues need to be addressed."
echo "Check LINUX_VIEWPORT_DEBUG.md for solutions."
