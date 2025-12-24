#!/bin/bash
# Install Adobe USD Fileformat Plugins
# Provides native FBX, improved OBJ/glTF/STL support for USD

set -e

echo "=========================================="
echo "Adobe USD Fileformat Plugins Installer"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_info() { echo -e "${BLUE}[i]${NC} $1"; }

# Check for USD installation
if ! python3 -c "from pxr import Usd" 2>/dev/null; then
    print_error "USD not found. Please install USD first:"
    echo "  pip install usd-core"
    exit 1
fi

USD_ROOT=$(python3 -c "from pxr import Usd; import os; print(os.path.dirname(os.path.dirname(Usd.__file__)))")
print_status "Found USD at: $USD_ROOT"

# Installation directory
INSTALL_DIR="${INSTALL_DIR:-/opt/adobe-usd-plugins}"
BUILD_DIR="${BUILD_DIR:-$HOME/adobe-usd-build}"

echo ""
echo "Installation options:"
echo "  1) Build from source (recommended, latest features)"
echo "  2) Install FBX Python SDK only (lighter, FBX support only)"
echo "  3) Check plugin status and exit"
echo ""
read -p "Select option [1-3]: " OPTION

case $OPTION in
    1)
        echo ""
        echo "Building Adobe USD Fileformat Plugins from source..."
        echo ""
        
        # Install build dependencies
        print_info "Installing build dependencies..."
        sudo dnf install -y \
            git cmake gcc gcc-c++ \
            boost-devel tbb-devel \
            libxml2-devel zlib-devel
        
        # Clone repository
        if [ -d "$BUILD_DIR/USD-Fileformat-plugins" ]; then
            print_warning "Source directory exists, updating..."
            cd "$BUILD_DIR/USD-Fileformat-plugins"
            git pull
        else
            mkdir -p "$BUILD_DIR"
            cd "$BUILD_DIR"
            print_info "Cloning Adobe USD Fileformat Plugins..."
            git clone https://github.com/adobe/USD-Fileformat-plugins.git
            cd USD-Fileformat-plugins
        fi
        
        # Create build directory
        mkdir -p build
        cd build
        
        print_info "Configuring build..."
        cmake .. \
            -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
            -DUSD_ROOT="$USD_ROOT" \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SHARED_LIBS=ON
        
        print_info "Building (this may take a while)..."
        make -j$(nproc)
        
        print_info "Installing..."
        sudo make install
        
        # Set up environment
        print_info "Setting up environment..."
        
        cat > ~/.usd_adobe_env << EOF
# Adobe USD Fileformat Plugins Environment
export PXR_PLUGINPATH_NAME=$INSTALL_DIR/plugin:\$PXR_PLUGINPATH_NAME
export LD_LIBRARY_PATH=$INSTALL_DIR/lib:\$LD_LIBRARY_PATH
EOF
        
        # Add to bashrc if not already there
        if ! grep -q "usd_adobe_env" ~/.bashrc; then
            echo "source ~/.usd_adobe_env" >> ~/.bashrc
        fi
        
        print_status "Build and installation complete!"
        print_info "Please run: source ~/.bashrc"
        ;;
        
    2)
        echo ""
        echo "Installing FBX Python SDK..."
        echo ""
        
        print_warning "You need to download FBX SDK from Autodesk:"
        echo "  https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-2"
        echo ""
        read -p "Have you downloaded the FBX Python SDK installer? (y/n) " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Please download and run this script again"
            exit 0
        fi
        
        read -p "Enter path to FBX installer: " FBX_INSTALLER
        
        if [ ! -f "$FBX_INSTALLER" ]; then
            print_error "File not found: $FBX_INSTALLER"
            exit 1
        fi
        
        # Make executable and run
        chmod +x "$FBX_INSTALLER"
        
        FBX_INSTALL_DIR="${FBX_INSTALL_DIR:-/opt/fbx-sdk}"
        sudo mkdir -p "$FBX_INSTALL_DIR"
        
        print_info "Running FBX installer..."
        sudo "$FBX_INSTALLER" "$FBX_INSTALL_DIR"
        
        # Find Python version
        PYTHON_VERSION=$(python3 -c "import sys; print(f'Python{sys.version_info.major}{sys.version_info.minor}_x64')")
        
        # Set up environment
        cat > ~/.fbx_sdk_env << EOF
# FBX Python SDK Environment
export PYTHONPATH=$FBX_INSTALL_DIR/lib/$PYTHON_VERSION:\$PYTHONPATH
export LD_LIBRARY_PATH=$FBX_INSTALL_DIR/lib/$PYTHON_VERSION:\$LD_LIBRARY_PATH
EOF
        
        if ! grep -q "fbx_sdk_env" ~/.bashrc; then
            echo "source ~/.fbx_sdk_env" >> ~/.bashrc
        fi
        
        print_status "FBX SDK installation complete!"
        print_info "Please run: source ~/.bashrc"
        ;;
        
    3)
        echo ""
        echo "Checking plugin status..."
        echo ""
        
        python3 << 'EOF'
import sys
import os

# Check USD
try:
    from pxr import Usd, Plug
    print("✓ USD Python bindings available")
    
    # Check plugins
    registry = Plug.Registry()
    
    plugins_to_check = ['usdFbx', 'usdObj', 'usdGltf', 'usdStl']
    for plugin_name in plugins_to_check:
        plugin = registry.GetPluginWithName(plugin_name)
        if plugin:
            status = "loaded" if plugin.isLoaded else "registered"
            print(f"  ✓ {plugin_name}: {status}")
        else:
            print(f"  ✗ {plugin_name}: not found")
            
except ImportError:
    print("✗ USD not available")
    sys.exit(1)

# Check FBX SDK
try:
    import fbx
    print("✓ FBX Python SDK available")
except ImportError:
    print("✗ FBX Python SDK not available")

# Check usdcat
import subprocess
try:
    result = subprocess.run(['usdcat', '--version'], capture_output=True, timeout=2)
    if result.returncode == 0:
        print("✓ usdcat CLI tool available")
except:
    print("✗ usdcat not available")

# Check fbx2usd
try:
    result = subprocess.run(['fbx2usd', '--version'], capture_output=True, timeout=2)
    if result.returncode == 0:
        print("✓ fbx2usd CLI tool available")
except:
    print("✗ fbx2usd not available")

print()
print("Plugin paths:")
if 'PXR_PLUGINPATH_NAME' in os.environ:
    print(f"  PXR_PLUGINPATH_NAME: {os.environ['PXR_PLUGINPATH_NAME']}")
else:
    print("  PXR_PLUGINPATH_NAME: not set")
EOF
        ;;
        
    *)
        print_error "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Installation Summary"
echo "=========================================="
echo ""

if [ $OPTION -eq 1 ]; then
    echo "Adobe USD Fileformat Plugins installed to: $INSTALL_DIR"
    echo ""
    echo "Supported formats:"
    echo "  • FBX - Native reading, materials, animation"
    echo "  • OBJ - Improved with materials"
    echo "  • glTF - Enhanced with PBR materials"
    echo "  • STL - Native support"
    echo "  • PLY - Native support"
    echo ""
    echo "Environment setup:"
    echo "  • PXR_PLUGINPATH_NAME configured"
    echo "  • Added to ~/.bashrc"
    echo ""
elif [ $OPTION -eq 2 ]; then
    echo "FBX Python SDK installed to: $FBX_INSTALL_DIR"
    echo ""
    echo "Supported formats:"
    echo "  • FBX - Full support via Python SDK"
    echo ""
    echo "Environment setup:"
    echo "  • PYTHONPATH configured"
    echo "  • Added to ~/.bashrc"
    echo ""
fi

echo "Next steps:"
echo "  1. Reload environment: source ~/.bashrc"
echo "  2. Verify installation: ./install_adobe_plugins.sh (option 3)"
echo "  3. Test with USD Viewer"
echo ""

print_status "Installation complete!"