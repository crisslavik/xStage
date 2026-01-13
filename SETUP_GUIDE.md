# xStage Setup Guide - Complete Installation

## 🔍 Current Issue
Your xStage viewer is not working because:
1. ❌ Virtual environment not created (`.xstage_venv` missing)
2. ❌ USD not installed (`.xstage_usd` missing)
3. ❌ Python dependencies not installed

## ✅ Solution: Run Installation Script

### Step 1: Run the Installer

```bash
cd /Users/slavik/Documents/xStage
./scripts/install.sh
```

This script will:
- ✅ Set up Python 3.11 virtual environment
- ✅ Install all Python dependencies (PySide6, PyOpenGL, numpy, etc.)
- ✅ Build or download USD with imaging support
- ✅ Configure Hydra 2.0 rendering
- ✅ Set up all necessary environment variables

### Step 2: Launch xStage

After installation completes:

```bash
./launch_usd_viewer.sh
```

## 🐧 Linux-Specific Setup

If you're on Linux (which you mentioned), the installer will:

1. **Check for system dependencies:**
   ```bash
   # The installer checks for these automatically
   - gcc/g++ compiler
   - cmake
   - OpenGL development libraries
   - Qt6 libraries
   ```

2. **If dependencies are missing, install them:**
   ```bash
   # RHEL/AlmaLinux/Rocky
   sudo dnf install -y gcc gcc-c++ cmake mesa-libGL-devel \
                       qt6-qtbase-devel python3.11-devel

   # Ubuntu/Debian
   sudo apt-get install -y build-essential cmake libgl1-mesa-dev \
                           qt6-base-dev python3.11-dev

   # Arch Linux
   sudo pacman -S base-devel cmake mesa qt6-base python
   ```

3. **Build USD from source** (if pre-built binaries not available)
   - This can take 30-60 minutes on first install
   - Includes UsdImagingGL for Hydra 2.0 rendering

## 🚨 Common Installation Issues

### Issue 1: Python 3.11 Not Found
```bash
# Check Python version
python3 --version

# If < 3.11, install Python 3.11:
# RHEL/AlmaLinux
sudo dnf install python3.11

# Ubuntu (if not in repos, use deadsnakes PPA)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev
```

### Issue 2: USD Build Fails
```bash
# Check build logs
cat /Users/slavik/Documents/xStage/.xstage_usd/build.log

# Common fixes:
# 1. Install missing system libraries
# 2. Ensure enough disk space (USD build needs ~5GB)
# 3. Check compiler version (gcc 8+ required)
```

### Issue 3: Qt6 Issues
```bash
# Install Qt6 development packages
# RHEL/AlmaLinux
sudo dnf install qt6-qtbase-devel

# Ubuntu
sudo apt-get install qt6-base-dev
```

## 📊 Installation Time Estimates

| Component | Time | Notes |
|-----------|------|-------|
| Virtual Environment | 1-2 min | Quick |
| Python Dependencies | 2-5 min | Downloads packages |
| USD Build (source) | 30-60 min | First time only |
| USD Download (binary) | 5-10 min | If available |
| **Total** | **10-70 min** | Depends on method |

## 🔍 Verify Installation

After installation, verify everything works:

```bash
# 1. Check virtual environment
ls -la .xstage_venv/

# 2. Check USD installation
ls -la .xstage_usd/

# 3. Test USD import
source .xstage_venv/bin/activate
python3 -c "from pxr import Usd, UsdGeom, UsdImagingGL; print('USD OK')"

# 4. Test Hydra availability
python3 scripts/diagnose_hydra.py
```

## 🎯 Expected Output After Installation

When you run `./launch_usd_viewer.sh`, you should see:

```
DEBUG: Initializing OpenGL viewport...
DEBUG: OpenGL Version: b'X.X'
DEBUG: OpenGL Renderer: b'Your GPU'
DEBUG: OpenGL viewport initialized successfully
```

**OR** (if Hydra 2.0 available):

```
✅ Hydra 2.0 Scene Index enabled
✅ Storm renderer (Hydra 2.0 GPU) enabled
Available renderers: ['HdStormRendererPlugin']
Current renderer: HdStormRendererPlugin
✅ Hydra engine initialized successfully
```

## 🔧 Manual Installation (If Script Fails)

If the automatic installer fails, you can install manually:

### 1. Create Virtual Environment
```bash
cd /Users/slavik/Documents/xStage
python3.11 -m venv .xstage_venv
source .xstage_venv/bin/activate
```

### 2. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install USD
```bash
# Option A: Use pip (basic USD, no Hydra)
pip install usd-core

# Option B: Build from source (full USD with Hydra)
# Follow: https://github.com/PixarAnimationStudios/OpenUSD
```

### 4. Test Installation
```bash
python3 -c "from pxr import Usd; print('USD version:', Usd.GetVersion())"
```

## 📝 Post-Installation

After successful installation:

1. **Create a test USD file** (optional):
   ```bash
   # The installer should create sample files
   ls examples/*.usd
   ```

2. **Launch xStage**:
   ```bash
   ./launch_usd_viewer.sh
   ```

3. **Open a USD file**:
   - File → Open
   - Navigate to a .usd/.usda/.usdc file
   - Should render in viewport

## 🆘 Still Having Issues?

If installation fails:

1. **Check the logs**:
   ```bash
   cat .xstage_venv/install.log
   cat .xstage_usd/build.log
   ```

2. **Run diagnostics**:
   ```bash
   python3 scripts/diagnose_hydra.py
   python3 scripts/check_usd_rendering.py
   ```

3. **Check system requirements**:
   - Python 3.11+
   - OpenGL 2.1+ (for basic rendering)
   - OpenGL 4.1+ (for Hydra 2.0)
   - 4GB+ RAM
   - 5GB+ disk space

## 🚀 Quick Start After Installation

```bash
# 1. Launch viewer
./launch_usd_viewer.sh

# 2. Open USD file
# File → Open → Select .usd file

# 3. Navigate viewport
# - Left-click drag: Rotate camera
# - Middle-click drag: Pan camera
# - Scroll wheel: Zoom
# - F key: Frame geometry
# - H key: Home view

# 4. Toggle rendering mode
# View → Rendering → Hydra 2.0 / OpenGL
```

---

**Next Step**: Run `./scripts/install.sh` and wait for installation to complete!
