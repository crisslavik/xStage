#!/bin/bash
# Quick Setup for xStage USD Viewer
# This creates a minimal working environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "xStage Quick Setup"
echo "========================================="
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d. -f1,2)
    if (( $(echo "$PYTHON_VERSION >= 3.10" | bc -l) )); then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.10+ required but not found"
    echo "Please install Python 3.10 or 3.11"
    exit 1
fi

echo "Using Python: $PYTHON_CMD ($($PYTHON_CMD --version))"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d ".xstage_venv" ]; then
    $PYTHON_CMD -m venv .xstage_venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source .xstage_venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install core dependencies
echo ""
echo "Installing core dependencies..."
pip install PySide6>=6.6.0 PyOpenGL>=3.1.7 numpy>=1.24.0

# Install USD
echo ""
echo "Installing USD..."
echo "Note: usd-core provides basic USD but NOT Hydra 2.0 rendering"
echo "For Hydra 2.0, you need to build USD from source (see SETUP_GUIDE.md)"
pip install usd-core

# Install optional dependencies
echo ""
echo "Installing optional dependencies..."
pip install Pillow psutil pygltflib trimesh || echo "Some optional packages failed (non-critical)"

# Test installation
echo ""
echo "========================================="
echo "Testing Installation"
echo "========================================="

# Test USD
echo ""
echo "Testing USD..."
python3 -c "
from pxr import Usd, UsdGeom
print('✓ USD version:', Usd.GetVersion())
print('✓ UsdGeom available')
" || { echo "✗ USD test failed"; exit 1; }

# Test UsdImagingGL (Hydra)
echo ""
echo "Testing Hydra 2.0 (UsdImagingGL)..."
python3 -c "
try:
    from pxr import UsdImagingGL
    print('✓ UsdImagingGL available - Hydra 2.0 will work')
except ImportError:
    print('✗ UsdImagingGL NOT available - Only OpenGL rendering will work')
    print('  To enable Hydra 2.0, you need to build USD from source')
    print('  See: ./scripts/install.sh or SETUP_GUIDE.md')
"

# Test Qt
echo ""
echo "Testing Qt..."
python3 -c "
from PySide6.QtWidgets import QApplication
from PySide6.QtOpenGLWidgets import QOpenGLWidget
print('✓ PySide6 with OpenGL support available')
" || { echo "✗ Qt test failed"; exit 1; }

# Test OpenGL
echo ""
echo "Testing OpenGL..."
python3 -c "
from OpenGL.GL import *
print('✓ PyOpenGL available')
" || { echo "✗ OpenGL test failed"; exit 1; }

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Installation Summary:"
echo "  ✓ Virtual environment: .xstage_venv/"
echo "  ✓ USD installed (basic support)"
echo "  ✓ Qt6 and OpenGL installed"
echo ""
echo "Rendering Capabilities:"
echo "  ✓ OpenGL viewport - WORKING"
python3 -c "
try:
    from pxr import UsdImagingGL
    print('  ✓ Hydra 2.0 viewport - WORKING')
except ImportError:
    print('  ✗ Hydra 2.0 viewport - NOT AVAILABLE')
    print('    (requires USD built from source with imaging support)')
"
echo ""
echo "Next Steps:"
echo "  1. Launch xStage:"
echo "     ./launch_usd_viewer.sh"
echo ""
echo "  2. Open a USD file:"
echo "     File → Open → Select .usd/.usda/.usdc file"
echo ""
echo "  3. For Hydra 2.0 support (optional):"
echo "     Run: ./scripts/install.sh"
echo "     (This will build USD from source with full imaging support)"
echo ""
