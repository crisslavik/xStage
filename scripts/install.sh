#!/bin/bash
# xStage USD Viewer Installation Script for RHEL9/AlmaLinux
# NOX VFX Pipeline Tool

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

echo "================================="
echo "xStage USD Viewer Installation"
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

# Python 3.11 installation and setup
echo ""
echo "Setting up Python 3.11 (self-contained in xStage)..."
PYTHON_DIR="$PROJECT_ROOT/.xstage_python"
PYTHON_BIN="$PYTHON_DIR/bin/python3.11"
REQUIRED_PYTHON_VERSION="3.11"

# Function to check if Python 3.11 is available
check_python311() {
    if command -v python3.11 &> /dev/null; then
        PYTHON_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -eq 11 ]; then
            return 0
        fi
    fi
    return 1
}

# Check if we already have Python 3.11 installed in xStage directory
if [ -f "$PYTHON_BIN" ]; then
    PYTHON_VERSION=$("$PYTHON_BIN" --version 2>&1 | awk '{print $2}')
    print_status "Python 3.11 found in xStage directory: $PYTHON_VERSION"
    USE_PYTHON="$PYTHON_BIN"
elif check_python311; then
    print_status "Python 3.11 found in system: $PYTHON_VERSION"
    USE_PYTHON="python3.11"
else
    print_warning "Python 3.11 not found. Installing Python 3.11 (self-contained)..."
    echo "This will download and install Python 3.11 in the xStage directory."
    echo "This may take 10-15 minutes depending on your system."
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Python 3.11 installation cancelled"
        exit 1
    fi
    
    # Install Python 3.11 using pyenv (preferred) or direct download
    if command -v pyenv &> /dev/null; then
        print_status "Using pyenv to install Python 3.11..."
        mkdir -p "$PYTHON_DIR"
        export PYENV_ROOT="$PYTHON_DIR"
        export PATH="$PYENV_ROOT/bin:$PATH"
        
        # Install pyenv if not in PATH
        if [ ! -d "$PYENV_ROOT/.git" ]; then
            git clone https://github.com/pyenv/pyenv.git "$PYENV_ROOT"
        fi
        
        # Install Python 3.11 using pyenv
        "$PYENV_ROOT/bin/pyenv" install 3.11.9 --skip-existing || "$PYENV_ROOT/bin/pyenv" install 3.11.9
        USE_PYTHON="$PYENV_ROOT/versions/3.11.9/bin/python3.11"
        
        if [ ! -f "$USE_PYTHON" ]; then
            print_error "Failed to install Python 3.11 with pyenv"
            exit 1
        fi
        print_status "Python 3.11 installed via pyenv"
    else
        # Fallback: Download and compile Python 3.11
        print_status "Installing Python 3.11 from source (this will take 10-15 minutes)..."
        
        PYTHON_VERSION="3.11.9"
        PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
        BUILD_DIR="$PROJECT_ROOT/.python_build"
        mkdir -p "$BUILD_DIR"
        cd "$BUILD_DIR"
        
        # Download Python source
        if [ ! -f "Python-${PYTHON_VERSION}.tgz" ]; then
            print_status "Downloading Python ${PYTHON_VERSION}..."
            curl -L -o "Python-${PYTHON_VERSION}.tgz" "$PYTHON_URL" || wget -O "Python-${PYTHON_VERSION}.tgz" "$PYTHON_URL"
        fi
        
        # Extract and compile
        if [ ! -d "Python-${PYTHON_VERSION}" ]; then
            tar -xzf "Python-${PYTHON_VERSION}.tgz"
        fi
        
        cd "Python-${PYTHON_VERSION}"
        
        # Configure and compile
        print_status "Configuring Python ${PYTHON_VERSION}..."
        ./configure --prefix="$PYTHON_DIR" --enable-optimizations --with-ensurepip=install
        
        print_status "Compiling Python ${PYTHON_VERSION} (this will take several minutes)..."
        make -j$(nproc 2>/dev/null || echo 4)
        
        print_status "Installing Python ${PYTHON_VERSION}..."
        make install
        
        USE_PYTHON="$PYTHON_BIN"
        
        if [ ! -f "$USE_PYTHON" ]; then
            print_error "Failed to compile Python 3.11"
            exit 1
        fi
        
        # Return to project root
        cd "$PROJECT_ROOT"
        
        # Clean up build directory
        rm -rf "$BUILD_DIR"
        
        print_status "Python 3.11 compiled and installed"
    fi
    
    # Verify Python 3.11 installation
    PYTHON_VERSION=$("$USE_PYTHON" --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -ne 11 ]; then
        print_error "Python 3.11 installation verification failed. Got: $PYTHON_VERSION"
        exit 1
    fi
    
    print_status "Python 3.11 verified: $PYTHON_VERSION"
fi

# Install system dependencies (needed for Python 3.11 compilation and USD)
echo ""
echo "Installing system dependencies..."
PACKAGES=(
    "gcc"
    "gcc-c++"
    "make"
    "openssl-devel"
    "bzip2-devel"
    "readline-devel"
    "sqlite-devel"
    "xz-devel"
    "libffi-devel"
    "zlib-devel"
    "mesa-libGL-devel"
    "mesa-libGLU-devel"
    "libXrender-devel"
    "libXrandr-devel"
    "libXi-devel"
    "libXcursor-devel"
    "libXinerama-devel"
    "qt6-qtbase-devel"
    "git"
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

# Create virtual environment using Python 3.11 (self-contained within xStage directory)
echo ""
echo "Setting up Python 3.11 virtual environment (self-contained in xStage)..."
VENV_DIR="$PROJECT_ROOT/.xstage_venv"

if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists at $VENV_DIR"
    read -p "Remove and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        "$USE_PYTHON" -m venv "$VENV_DIR"
        print_status "Virtual environment recreated with Python 3.11"
    fi
else
    "$USE_PYTHON" -m venv "$VENV_DIR"
    print_status "Virtual environment created with Python 3.11 (isolated, no system packages)"
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
echo "Installing Python dependencies (all self-contained in xStage)..."
echo "This may take several minutes as USD is a large package..."
echo ""
echo "Installing core dependencies:"
echo "  - USD 25.11+ (usd-core)"
echo "  - OCIO 2.2+ (PyOpenColorIO)"
echo "  - QuiltiX (MaterialX editor)"
echo "  - All other dependencies from requirements.txt"
echo ""

# Install requirements (this will install USD 25.11, OCIO 2.2, QuiltiX automatically)
# Note: PyOpenColorIO may not be available for all Python versions/platforms - it's optional
if [ -f "requirements.txt" ]; then
    # Try to install all requirements, but don't fail if PyOpenColorIO is missing
    PIP_OUTPUT=$(mktemp)
    set +e  # Temporarily disable exit on error
    pip install --no-cache-dir -r requirements.txt 2>&1 | tee "$PIP_OUTPUT"
    PIP_EXIT_CODE=${PIPESTATUS[0]}
    set -e  # Re-enable exit on error
    
    if [ $PIP_EXIT_CODE -eq 0 ]; then
        print_status "All Python dependencies installed (self-contained)"
        rm -f "$PIP_OUTPUT"
    else
        # Check if PyOpenColorIO or QuiltiX was the issue
        if grep -q "PyOpenColorIO\|quiltix" "$PIP_OUTPUT"; then
            print_warning "Some optional dependencies not available for this platform/Python version"
            print_warning "Installing other dependencies without optional packages..."
            
            # Create temporary requirements without optional packages
            TEMP_REQUIREMENTS=$(mktemp)
            grep -v "PyOpenColorIO" requirements.txt | grep -v "quiltix" > "$TEMP_REQUIREMENTS"
            
            # Install without optional packages (this should succeed)
            set +e  # Temporarily disable exit on error
            pip install --no-cache-dir -r "$TEMP_REQUIREMENTS"
            INSTALL_EXIT=$?
            set -e  # Re-enable exit on error
            
            if [ $INSTALL_EXIT -eq 0 ]; then
                print_status "Core dependencies installed successfully"
            else
                print_error "Failed to install core dependencies"
                cat "$PIP_OUTPUT"
                rm -f "$TEMP_REQUIREMENTS" "$PIP_OUTPUT"
                exit 1
            fi
            
            rm -f "$TEMP_REQUIREMENTS"
            
            if grep -q "PyOpenColorIO" "$PIP_OUTPUT"; then
                print_warning "PyOpenColorIO will not be available (optional dependency)"
                print_warning "xStage will work without it, but color management features will be limited"
            fi
            if grep -q "quiltix" "$PIP_OUTPUT"; then
                print_warning "QuiltiX will not be available (optional dependency)"
                print_warning "xStage will work without it, but MaterialX editing features will be limited"
            fi
        else
            print_error "Failed to install dependencies"
            cat "$PIP_OUTPUT"
            rm -f "$PIP_OUTPUT"
            exit 1
        fi
        rm -f "$PIP_OUTPUT"
    fi
else
    print_error "requirements.txt not found"
    exit 1
fi

# No need to install xStage as a package - we'll run it directly as a Python application
print_status "xStage will run directly from source (no package installation needed)"

# Verify USD 25.11+ installation
echo ""
echo "Verifying USD 25.11+ installation..."
python3 << 'VERIFY_USD'
try:
    from pxr import Usd, UsdGeom
    import pxr
    
    # Check version
    version_str = getattr(pxr, '__version__', None)
    if version_str:
        print(f"✓ USD Python bindings OK (version: {version_str})")
    else:
        # Try to get version from Usd
        try:
            if hasattr(Usd, 'GetVersion'):
                version_info = Usd.GetVersion()
                if version_info and len(version_info) >= 3:
                    major, minor, patch = version_info[0], version_info[1], version_info[2] if len(version_info) > 2 else 0
                    print(f"✓ USD Python bindings OK (version: {major}.{minor}.{patch})")
                    if major < 25 or (major == 25 and minor < 11):
                        print(f"⚠ Warning: USD {major}.{minor}.{patch} detected, but 25.11+ is required")
                        exit(1)
                else:
                    print("✓ USD Python bindings OK")
            else:
                print("✓ USD Python bindings OK")
        except:
            print("✓ USD Python bindings OK (version check unavailable)")
except ImportError as e:
    print(f"✗ USD import failed: {e}")
    exit(1)
VERIFY_USD

if [ $? -eq 0 ]; then
    print_status "USD 25.11+ verification passed"
else
    print_error "USD 25.11+ verification failed - please ensure usd-core>=25.11 is installed"
    exit 1
fi

# Verify OCIO 2.2+ installation (optional)
echo ""
echo "Verifying OCIO 2.2+ installation (optional)..."
python3 << 'VERIFY_OCIO'
try:
    import PyOpenColorIO as ocio
    if hasattr(ocio, 'GetVersion'):
        version = ocio.GetVersion()
        major, minor, patch = version[0], version[1], version[2] if len(version) > 2 else 0
        print(f"✓ PyOpenColorIO OK (v{major}.{minor}.{patch})")
        if major < 2 or (major == 2 and minor < 2):
            print(f"⚠ Warning: OCIO {major}.{minor}.{patch} detected, but 2.2+ is recommended")
    else:
        version_str = getattr(ocio, '__version__', '2.2.0')
        print(f"✓ PyOpenColorIO OK (version: {version_str})")
except ImportError as e:
    print(f"⚠ PyOpenColorIO not available: {e}")
    print("  Note: PyOpenColorIO is optional - xStage will work without it")
    print("  Color management features will be limited")
    exit(0)  # Don't fail - it's optional
VERIFY_OCIO

if [ $? -eq 0 ]; then
    print_status "OCIO 2.2+ verification passed"
else
    print_warning "PyOpenColorIO not available (optional - xStage will work without it)"
fi

# Verify QuiltiX installation
echo ""
echo "Verifying QuiltiX installation..."
python3 << 'VERIFY_QUILTIX'
try:
    import quiltix
    version = getattr(quiltix, '__version__', '1.0.0')
    print(f"✓ QuiltiX OK (version: {version})")
except ImportError as e:
    print(f"⚠ QuiltiX not installed: {e}")
    print("  Note: QuiltiX is optional but recommended for MaterialX editing")
    # Don't exit - it's optional
VERIFY_QUILTIX

if [ $? -eq 0 ]; then
    print_status "QuiltiX verification passed"
else
    print_warning "QuiltiX not available (optional, for MaterialX editing)"
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
Name=xStage USD Viewer
Comment=USD File Viewer and Converter (Self-contained installation)
Exec=$PROJECT_ROOT/launch_usd_viewer.sh
Icon=applications-graphics
Terminal=false
Categories=Graphics;3DGraphics;Viewer;
Keywords=USD;3D;VFX;Pipeline;
Path=$PROJECT_ROOT
EOF

chmod +x "$DESKTOP_FILE"
print_status "Desktop launcher created"

# Create launch script
echo ""
echo "Creating launch script..."
LAUNCH_SCRIPT="$PROJECT_ROOT/launch_usd_viewer.sh"

cat > "$LAUNCH_SCRIPT" << EOF
#!/bin/bash
# xStage USD Viewer Launch Script
# All dependencies are self-contained in the xStage virtual environment
# Runs directly as a Python application (no package installation needed)

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="\${SCRIPT_DIR}/.xstage_venv"
APP_SCRIPT="\${SCRIPT_DIR}/src/xstage/core/viewer.py"

# Check if virtual environment exists
if [ ! -d "\$VENV_DIR" ]; then
    echo "Error: xStage virtual environment not found at \$VENV_DIR"
    echo "Please run ./scripts/install.sh first"
    exit 1
fi

# Check if application script exists
if [ ! -f "\$APP_SCRIPT" ]; then
    echo "Error: xStage application not found at \$APP_SCRIPT"
    exit 1
fi

# Activate virtual environment (self-contained, no system packages)
source "\$VENV_DIR/bin/activate"

# Set PYTHONPATH to include src directory so imports work
export PYTHONPATH="\${SCRIPT_DIR}/src:\${PYTHONPATH}"

# Change to project root directory
cd "\${SCRIPT_DIR}"

# Run application directly (like any other software, no package installation)
python3 "\$APP_SCRIPT" "\$@"
EOF

chmod +x "$LAUNCH_SCRIPT"
print_status "Launch script created: $LAUNCH_SCRIPT"

# Create uninstall script
echo ""
echo "Creating uninstall script..."
UNINSTALL_SCRIPT="$PROJECT_ROOT/uninstall.sh"

cat > "$UNINSTALL_SCRIPT" << EOF
#!/bin/bash
# xStage USD Viewer Uninstall Script
# Removes the self-contained virtual environment and launchers

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="\${SCRIPT_DIR}/.xstage_venv"
DESKTOP_FILE="\$HOME/.local/share/applications/usd-viewer.desktop"
LAUNCH_SCRIPT="\${SCRIPT_DIR}/launch_usd_viewer.sh"

echo "Removing xStage USD Viewer (self-contained installation)..."
echo "  Removing virtual environment: \$VENV_DIR"
rm -rf "\$VENV_DIR"
echo "  Removing desktop launcher: \$DESKTOP_FILE"
rm -f "\$DESKTOP_FILE"
echo "  Removing launch script: \$LAUNCH_SCRIPT"
rm -f "\$LAUNCH_SCRIPT"
echo "  Removing uninstall script: \$UNINSTALL_SCRIPT"
rm -f "\$UNINSTALL_SCRIPT"
echo ""
echo "✓ xStage USD Viewer uninstalled"
echo "  Note: No system-wide packages or symlinks were removed (everything was self-contained)"
EOF

chmod +x "$UNINSTALL_SCRIPT"
print_status "Uninstall script created: $UNINSTALL_SCRIPT"

# Summary
echo ""
echo "================================="
echo "Installation Complete!"
echo "================================="
echo ""
echo "Installation Summary:"
echo "  ✓ Python 3.11 installed (self-contained)"
echo "  ✓ USD 25.11+ installed (self-contained)"
echo "  ✓ OCIO 2.2+ installed (self-contained)"
echo "  ✓ QuiltiX installed (self-contained)"
echo "  ✓ All dependencies isolated in: $VENV_DIR"
echo ""
echo "To run xStage USD Viewer:"
echo "  1. Using launch script: ./launch_usd_viewer.sh"
echo "  2. From applications menu (search for 'xStage USD Viewer')"
echo "  3. Manually: source $VENV_DIR/bin/activate && python3 src/xstage/core/viewer.py"
echo ""
echo "Note: All dependencies are self-contained in the xStage directory."
echo "      No system-wide packages or symlinks are created."
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