#!/bin/bash
# Fix broken virtual environment and recreate with correct Python version

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Fixing xStage Virtual Environment"
echo "========================================="
echo ""

# Remove broken virtual environment
echo "Removing broken virtual environment..."
if [ -d ".xstage_venv" ]; then
    rm -rf .xstage_venv
    echo "✓ Removed old virtual environment"
fi

# Detect Python version
echo ""
echo "Detecting Python..."
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "✓ Found Python 3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✓ Found Python 3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo "✓ Found Python 3.10"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    echo "✓ Found Python $PYTHON_VERSION"
else
    echo "✗ Error: Python 3.10+ not found"
    exit 1
fi

# Check if python3-venv is installed (required on Debian/Ubuntu)
echo ""
echo "Checking for venv module..."
if ! $PYTHON_CMD -m venv --help &> /dev/null; then
    echo "✗ Error: venv module not available"
    echo ""
    echo "Please install it:"
    if command -v apt-get &> /dev/null; then
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
        echo "  sudo apt-get install python${PYTHON_VERSION}-venv"
    elif command -v dnf &> /dev/null; then
        echo "  sudo dnf install python3-venv"
    else
        echo "  Install python3-venv package for your distribution"
    fi
    exit 1
fi

# Create new virtual environment
echo ""
echo "Creating new virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv .xstage_venv
echo "✓ Virtual environment created"

# Activate virtual environment
source .xstage_venv/bin/activate

# Verify Python in venv
echo ""
echo "Verifying virtual environment..."
VENV_PYTHON=$(python3 --version 2>&1)
echo "✓ Virtual environment Python: $VENV_PYTHON"

# Upgrade pip
echo ""
echo "Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "This may take a few minutes..."

# Install in order of importance
echo ""
echo "1/5 Installing Qt6..."
pip install PySide6>=6.6.0

echo ""
echo "2/5 Installing OpenGL..."
pip install PyOpenGL>=3.1.7 PyOpenGL-accelerate>=3.1.7

echo ""
echo "3/5 Installing numpy..."
pip install numpy>=1.24.0

echo ""
echo "4/5 Installing USD..."
pip install usd-core

echo ""
echo "5/5 Installing optional packages..."
pip install Pillow psutil pygltflib trimesh || echo "Some optional packages failed (non-critical)"

# Test installation
echo ""
echo "========================================="
echo "Testing Installation"
echo "========================================="

# Test USD
echo ""
echo "Testing USD..."
python3 << 'EOF'
try:
    from pxr import Usd, UsdGeom
    print(f"✓ USD version: {Usd.GetVersion()}")
    print("✓ UsdGeom available")
except Exception as e:
    print(f"✗ USD test failed: {e}")
    exit(1)
EOF

# Test UsdImagingGL
echo ""
echo "Testing Hydra 2.0..."
python3 << 'EOF'
try:
    from pxr import UsdImagingGL
    print("✓ UsdImagingGL available - Hydra 2.0 will work!")
except ImportError:
    print("⚠ UsdImagingGL NOT available - Only OpenGL rendering")
    print("  (This is normal with pip-installed USD)")
EOF

# Test Qt
echo ""
echo "Testing Qt..."
python3 << 'EOF'
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    print("✓ PySide6 with OpenGL support available")
except Exception as e:
    print(f"✗ Qt test failed: {e}")
    exit(1)
EOF

# Test OpenGL
echo ""
echo "Testing OpenGL..."
python3 << 'EOF'
try:
    from OpenGL.GL import glGetString, GL_VERSION
    print("✓ PyOpenGL available")
except Exception as e:
    print(f"✗ OpenGL test failed: {e}")
    exit(1)
EOF

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "✓ Virtual environment: .xstage_venv/"
echo "✓ Python: $VENV_PYTHON"
echo "✓ USD installed"
echo "✓ Qt6 and OpenGL installed"
echo ""
echo "You can now launch xStage:"
echo "  ./launch_usd_viewer.sh"
echo ""
