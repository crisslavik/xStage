# Platform Support
## Linux Compatibility Guide

xStage is designed and tested for Linux distributions commonly used in VFX pipelines.

---

## ✅ **Supported Platforms**

### **Ubuntu**
- **Versions**: Ubuntu 20.04 LTS, 22.04 LTS, 24.04 LTS
- **Status**: ✅ **Fully Supported**
- **Python**: 3.9, 3.10, 3.11
- **Package Manager**: `apt`

### **RHEL 9 (Red Hat Enterprise Linux 9)**
- **Status**: ✅ **Fully Supported**
- **Python**: 3.9, 3.10, 3.11
- **Package Manager**: `dnf` / `yum`
- **Compatible**: AlmaLinux 9, Rocky Linux 9

### **RHEL 10 (Red Hat Enterprise Linux 10)**
- **Status**: ✅ **Fully Supported**
- **Python**: 3.9, 3.10, 3.11
- **Package Manager**: `dnf`
- **Compatible**: AlmaLinux 10, Rocky Linux 10

### **Other Linux Distributions**
- **Status**: ⚠️ **Should Work** (not officially tested)
- **Requirements**: Python 3.9+, POSIX-compliant Linux
- **Tested**: Debian 11+, CentOS Stream 9+

---

## 📦 **Installation by Platform**

### **Ubuntu 20.04/22.04/24.04**

```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    cmake \
    git \
    libgl1-mesa-glx \
    libglu1-mesa \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxinerama1 \
    libxi6 \
    libasound2

# Install xStage
pip install --user xstage

# Or install in virtual environment
python3 -m venv xstage_env
source xstage_env/bin/activate
pip install xstage
```

### **RHEL 9 / AlmaLinux 9 / Rocky Linux 9**

```bash
# Enable EPEL repository (if needed)
sudo dnf install -y epel-release

# Install system dependencies
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    gcc \
    gcc-c++ \
    cmake \
    git \
    mesa-libGL \
    mesa-libGLU \
    libXrandr \
    libXScrnSaver \
    libXcursor \
    libXinerama \
    libXi \
    alsa-lib

# Install xStage
pip3 install --user xstage

# Or install in virtual environment
python3 -m venv xstage_env
source xstage_env/bin/activate
pip install xstage
```

### **RHEL 10 / AlmaLinux 10 / Rocky Linux 10**

```bash
# Install system dependencies
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    gcc \
    gcc-c++ \
    cmake \
    git \
    mesa-libGL \
    mesa-libGLU \
    libXrandr \
    libXScrnSaver \
    libXcursor \
    libXinerama \
    libXi \
    alsa-lib

# Install xStage
pip3 install --user xstage

# Or install in virtual environment
python3 -m venv xstage_env
source xstage_env/bin/activate
pip install xstage
```

---

## 🔍 **Platform-Specific Notes**

### **Ubuntu**

**OpenGL Support:**
- Ubuntu includes Mesa OpenGL drivers by default
- For NVIDIA GPUs, install proprietary drivers:
  ```bash
  sudo ubuntu-drivers autoinstall
  ```

**Qt/PySide6:**
- PySide6 wheels are available for Ubuntu
- No additional system packages needed

**Common Issues:**
- If GUI doesn't launch, check X11 forwarding (for remote connections)
- Ensure `DISPLAY` environment variable is set

### **RHEL 9/10**

**Python Version:**
- RHEL 9 includes Python 3.9 by default
- RHEL 10 includes Python 3.11+ by default
- Both are compatible with xStage

**OpenGL Support:**
- Mesa OpenGL included by default
- For NVIDIA GPUs, use NVIDIA's CUDA repository:
  ```bash
  # RHEL 9
  sudo dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
  
  # RHEL 10
  sudo dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/cuda-rhel10.repo
  ```

**SELinux:**
- SELinux may need configuration for some operations
- If issues occur, check SELinux logs: `sudo ausearch -m avc`

**Firewall:**
- xStage doesn't require network ports
- No firewall configuration needed

---

## 🧪 **Testing & Verification**

### **Verify Installation**

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Check xStage installation
xstage --version

# Test USD import
python3 -c "from pxr import Usd; print('USD: OK')"

# Test xStage import
python3 -c "from xstage import USDViewerWindow; print('xStage: OK')"
```

### **Test GUI Launch**

```bash
# Launch xStage
xstage

# Or with a test file
xstage test.usd
```

### **Check Dependencies**

```bash
# Check PySide6
python3 -c "from PySide6.QtWidgets import QApplication; print('PySide6: OK')"

# Check OpenGL
python3 -c "from OpenGL.GL import *; print('OpenGL: OK')"

# Check MaterialX
python3 -c "from pxr import UsdMtlx; print('MaterialX: OK')"
```

---

## 🐛 **Troubleshooting**

### **Ubuntu Issues**

**Problem**: `libGL.so.1: cannot open shared object file`
```bash
sudo apt install libgl1-mesa-glx libglu1-mesa
```

**Problem**: GUI doesn't appear
```bash
# Check X11
echo $DISPLAY

# For remote connections
export DISPLAY=:0.0
```

**Problem**: PySide6 import error
```bash
# Reinstall PySide6
pip install --force-reinstall PySide6
```

### **RHEL Issues**

**Problem**: `libGL.so.1: cannot open shared object file`
```bash
sudo dnf install mesa-libGL mesa-libGLU
```

**Problem**: SELinux blocking execution
```bash
# Check SELinux status
getenforce

# If enforcing, check logs
sudo ausearch -m avc

# Temporarily set to permissive (for testing)
sudo setenforce 0
```

**Problem**: Python version mismatch
```bash
# Check available Python versions
ls /usr/bin/python*

# Use specific version
python3.9 -m pip install xstage
```

---

## 📊 **Platform Comparison**

| Feature | Ubuntu | RHEL 9 | RHEL 10 |
|---------|--------|--------|---------|
| **Python 3.9+** | ✅ | ✅ | ✅ |
| **PySide6** | ✅ | ✅ | ✅ |
| **OpenGL** | ✅ | ✅ | ✅ |
| **USD Core** | ✅ | ✅ | ✅ |
| **MaterialX** | ✅ | ✅ | ✅ |
| **Adobe Plugins** | ✅ | ✅ | ✅ |
| **Package Manager** | apt | dnf/yum | dnf |
| **Default Python** | 3.10+ | 3.9 | 3.11+ |

---

## 🚀 **Performance Notes**

### **GPU Acceleration**
- **Ubuntu**: NVIDIA drivers work out of the box
- **RHEL**: May need NVIDIA repository for proprietary drivers
- **OpenGL**: Mesa drivers work for basic rendering
- **Hydra 2.0**: Requires compatible GPU drivers

### **Memory Requirements**
- **Minimum**: 4 GB RAM
- **Recommended**: 8+ GB RAM
- **Large Scenes**: 16+ GB RAM

### **Disk Space**
- **xStage**: ~500 MB
- **Dependencies**: ~2 GB
- **Adobe Plugins** (optional): ~100 MB

---

## 📚 **Additional Resources**

- **Installation Guide**: `docs/installation.md`
- **Adobe Plugins**: `docs/adobe-plugin-formats.md`
- **Troubleshooting**: See platform-specific sections above

---

## ✅ **Compatibility Matrix**

| Component | Ubuntu 20.04+ | RHEL 9 | RHEL 10 |
|-----------|---------------|--------|---------|
| **Python 3.9** | ✅ | ✅ | ✅ |
| **Python 3.10** | ✅ | ✅ | ✅ |
| **Python 3.11** | ✅ | ✅ | ✅ |
| **usd-core** | ✅ | ✅ | ✅ |
| **PySide6** | ✅ | ✅ | ✅ |
| **PyOpenGL** | ✅ | ✅ | ✅ |
| **numpy** | ✅ | ✅ | ✅ |
| **Pillow** | ✅ | ✅ | ✅ |
| **psutil** | ✅ | ✅ | ✅ |
| **trimesh** | ✅ | ✅ | ✅ |
| **pygltflib** | ✅ | ✅ | ✅ |
| **alembic** | ✅ | ✅ | ✅ |

---

*Last Updated: Platform support documentation*

