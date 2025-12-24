#!/bin/bash
# USD Viewer Installation Script for RHEL9/AlmaLinux
# NOX VFX Pipeline Tool

set -e

echo "================================="
echo "USD Viewer Installation - RHEL9"
echo "================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please do not run as root${NC}"
   exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check RHEL/AlmaLinux version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "rhel" && "$ID" != "almalinux" && "$ID" != "rocky" ]]; then
        print_warning "This script is designed for RHEL9/AlmaLinux 9. Current OS: $ID"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    print_error "Python 3.9+ required. Found: $PYTHON_VERSION"
    exit 1
fi
print_status "Python $PYTHON_VERSION found"

# Install system dependencies
echo ""
echo "Installing system dependencies..."
PACKAGES=(
    "python3-pip"
    "python3-devel"
    "gcc"
    "gcc-c++"
    "make"
    "mesa-libGL-devel"
    "mesa-libGLU-devel"
    "libXrender-devel"
    "libXrandr-devel"
    "libXi-devel"
    "libXcursor-devel"
    "libXinerama-devel"
    "qt6-qtbase-devel"
)

MISSING_PACKAGES=()
for pkg in "${PACKAGES[@]}"; do
    if ! rpm -q "$pkg" &> /dev/null; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "Missing packages: ${MISSING_PACKAGES[*]}"
    echo "Installing with sudo..."
    sudo dnf install -y "${MISSING_PACKAGES[@]}"
    print_status "System dependencies installed"
else
    print_status "All system dependencies already installed"
fi

# Create virtual environment
echo ""
echo "Setting up Python virtual environment..."
VENV_DIR="$HOME/usd_viewer_venv"

if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists at $VENV_DIR"
    read -p "Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        print_status "Virtual environment recreated"
    fi
else
    python3 -m venv "$VENV_DIR"
    print_status "Virtual environment created"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
print_status "pip upgraded"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
echo "This may take several minutes as USD is a large package..."

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Verify USD installation
echo ""
echo "Verifying USD installation..."
python3 << EOF
try:
    from pxr import Usd, UsdGeom
    print("✓ USD Python bindings OK")
except ImportError as e:
    print("✗ USD import failed:", e)
    exit(1)
EOF

if [ $? -eq 0 ]; then
    print_status "USD verification passed"
else
    print_error "USD verification failed"
    exit 1
fi

# Create desktop entry
echo ""
echo "Creating desktop launcher..."
DESKTOP_FILE="$HOME/.local/share/applications/usd-viewer.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=USD Viewer
Comment=USD File Viewer and Converter
Exec=$VENV_DIR/bin/python $PWD/usd_viewer.py
Icon=applications-graphics
Terminal=false
Categories=Graphics;3DGraphics;Viewer;
Keywords=USD;3D;VFX;Pipeline;
EOF

chmod +x "$DESKTOP_FILE"
print_status "Desktop launcher created"

# Create launch script
echo ""
echo "Creating launch script..."
LAUNCH_SCRIPT="$PWD/launch_usd_viewer.sh"

cat > "$LAUNCH_SCRIPT" << 'EOF'
#!/bin/bash
# USD Viewer Launch Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$HOME/usd_viewer_venv"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Run application
python3 "$SCRIPT_DIR/usd_viewer.py" "$@"
EOF

chmod +x "$LAUNCH_SCRIPT"
print_status "Launch script created: $LAUNCH_SCRIPT"

# Create uninstall script
echo ""
echo "Creating uninstall script..."
UNINSTALL_SCRIPT="$PWD/uninstall.sh"

cat > "$UNINSTALL_SCRIPT" << EOF
#!/bin/bash
# USD Viewer Uninstall Script

echo "Removing USD Viewer..."
rm -rf "$VENV_DIR"
rm -f "$DESKTOP_FILE"
rm -f "$LAUNCH_SCRIPT"
rm -f "$UNINSTALL_SCRIPT"
echo "USD Viewer uninstalled"
EOF

chmod +x "$UNINSTALL_SCRIPT"
print_status "Uninstall script created: $UNINSTALL_SCRIPT"

# Summary
echo ""
echo "================================="
echo "Installation Complete!"
echo "================================="
echo ""
echo "To run USD Viewer:"
echo "  1. Using launch script: ./launch_usd_viewer.sh"
echo "  2. From applications menu (search for 'USD Viewer')"
echo "  3. Manually: source $VENV_DIR/bin/activate && python3 $PWD/usd_viewer.py"
echo ""
echo "To uninstall: ./uninstall.sh"
echo ""
echo "Supported input formats:"
echo "  - USD: .usd, .usda, .usdc, .usdz"
echo "  - OBJ: .obj"
echo "  - glTF: .gltf, .glb"
echo "  - STL: .stl"
echo "  - PLY: .ply"
echo "  - Alembic: .abc (requires USD with Alembic support)"
echo "  - FBX: .fbx (requires Maya or Blender)"
echo ""
print_status "Ready to use!"