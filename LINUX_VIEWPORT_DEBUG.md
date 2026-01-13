# Linux Viewport Debugging Guide

## Common Linux Viewport Issues & Solutions

### 1. OpenGL Driver Issues
**Symptoms**: Viewport appears black, stuck, or crashes
**Solutions**:
```bash
# Check OpenGL info
glxinfo | grep "OpenGL version"
glxinfo | grep "OpenGL renderer"

# Install Mesa drivers (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install mesa-utils libgl1-mesa-glx libgl1-mesa-dri

# Install NVIDIA drivers (if using NVIDIA)
sudo ubuntu-drivers autoinstall
# Or download from NVIDIA website

# Check for software rendering
export LIBGL_ALWAYS_SOFTWARE=1  # Force software rendering (for testing)
```

### 2. Qt/X11 Display Issues
**Symptoms**: Window doesn't appear, viewport frozen
**Solutions**:
```bash
# Check display
echo $DISPLAY
xrandr --listmonitors

# Set Qt platform if needed
export QT_QPA_PLATFORM=xcb  # Force X11
# or
export QT_QPA_PLATFORM=wayland  # Force Wayland

# Run with verbose output
./launch_usd_viewer.sh --verbose 2>&1 | tee debug.log
```

### 3. Library Path Issues
**Symptoms**: Import errors, missing USD/OpenGL symbols
**Solutions**:
```bash
# Check library paths
echo $LD_LIBRARY_PATH
echo $PYTHONPATH

# Set proper paths in launch script
export LD_LIBRARY_PATH="$PWD/.xstage_usd/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="$PWD/src:$PYTHONPATH"
```

### 4. Permission Issues
**Symptoms**: Can't access GPU, permission denied
**Solutions**:
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Log out and log back in

# Check GPU access
ls -la /dev/dri/
ls -la /dev/nvidia*  # if NVIDIA
```

## Debugging Steps

### Step 1: Test OpenGL
```bash
# Test basic OpenGL
glxgears
# Should show rotating gears, no errors
```

### Step 2: Test USD Installation
```python
# Test USD Python bindings
python3 -c "
from pxr import Usd, UsdGeom
print('USD version:', Usd.GetVersion())
stage = Usd.Stage.CreateInMemory()
print('USD working:', stage is not None)
"
```

### Step 3: Run with Debug Output
```bash
# Enable all debug output
export XSTAGE_DEBUG=1
export QT_DEBUG_PLUGINS=1
./launch_usd_viewer.sh 2>&1 | tee xstage_debug.log
```

### Step 4: Check for Common Errors
Look for these in the debug output:
- `OpenGL error: 1280` - Invalid enum
- `OpenGL error: 1282` - Invalid operation
- `Failed to create OpenGL context`
- `Cannot share context`
