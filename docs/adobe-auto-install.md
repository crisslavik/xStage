# Adobe Plugins Auto-Installation
## Automatic Installation to xStage Directory

xStage can automatically download and install Adobe USD Fileformat Plugins to an isolated directory, without affecting other software or system-wide USD installations.

---

## 🎯 **How It Works**

### **Isolated Installation**
- Plugins are installed to `~/.xstage/plugins/adobe-usd-plugins/`
- Completely isolated from system USD installation
- Does not affect other software using USD
- Uses USD's `PXR_PLUGINPATH_NAME` environment variable (xStage only)

### **Automatic Detection**
- xStage automatically detects if plugins are available
- Checks system-wide installation first
- Falls back to xStage directory
- Auto-installs if not found (optional)

---

## 🚀 **Usage**

### **Automatic Installation (Default)**

xStage automatically installs plugins when needed:

```python
from xstage.converters import AdobeUSDConverter, ConversionOptions

# Auto-install enabled by default
converter = AdobeUSDConverter(ConversionOptions())
# Plugins will be installed automatically if not found

# Convert FBX (uses auto-installed plugins)
converter.convert("model.fbx", "model.usd")
```

### **Manual Installation**

You can also install plugins manually:

```python
from xstage.utils import AdobePluginInstaller

installer = AdobePluginInstaller()

# Install plugins
installer.install()

# Verify installation
if installer.verify_installation():
    print("✅ Plugins installed successfully!")
```

### **Disable Auto-Install**

If you prefer to install manually:

```python
# Disable auto-install
converter = AdobeUSDConverter(ConversionOptions(), auto_install=False)
```

---

## 📦 **Installation Methods**

### **Method 1: Pre-built Binaries (Preferred)**

xStage automatically downloads pre-built binaries if available:

```python
from xstage.utils import auto_install_adobe_plugins

# Try to download and install pre-built binary
auto_install_adobe_plugins()
```

**Requirements:**
- Internet connection
- Pre-built binaries available for your platform

### **Method 2: Build from Source (Fallback)**

If pre-built binaries are not available, xStage builds from source:

```python
from xstage.utils import AdobePluginInstaller

installer = AdobePluginInstaller()

# Build from source
installer.install_from_source()
```

**Requirements:**
- Git
- CMake
- C++ compiler (gcc/clang)
- USD development headers

---

## 🔍 **Verification**

### **Check Installation Status**

```python
from xstage.utils import AdobePluginInstaller

installer = AdobePluginInstaller()

# Check if installed
if installer.is_installed():
    print("✅ Plugins installed in xStage directory")

# Check if system plugins available
if installer.check_system_plugins():
    print("✅ System plugins available")

# Verify plugins can be loaded
if installer.verify_installation():
    print("✅ Plugins verified and working")
```

### **Check Plugin Path**

```python
from xstage.utils import AdobePluginInstaller

installer = AdobePluginInstaller()
plugin_path = installer.get_xstage_plugin_path()
print(f"Plugins installed at: {plugin_path}")
```

---

## 🗂️ **Directory Structure**

After installation, the directory structure looks like:

```
~/.xstage/
├── plugins/
│   └── adobe-usd-plugins/
│       ├── plugInfo.json
│       ├── usdFbx/
│       │   ├── plugInfo.json
│       │   └── resources/
│       ├── usdObj/
│       ├── usdGltf/
│       └── usdStl/
├── src/
│   └── adobe-usd-plugins/  # Source code (if built from source)
└── downloads/  # Downloaded archives
```

---

## ⚙️ **Configuration**

### **Environment Variables**

xStage automatically sets these for its own process:

- `PXR_PLUGINPATH_NAME`: Points to `~/.xstage/plugins/adobe-usd-plugins/`
- `PXR_PLUGINPATH`: Alternative plugin path variable

**Note:** These are set only for the xStage process, not system-wide.

### **USD Root Detection**

xStage automatically finds USD installation:

1. Checks `USD_ROOT` environment variable
2. Checks common paths (`/usr/local/USD`, `/opt/pixar/USD`, etc.)
3. Detects via Python `pxr` module location

---

## 🔧 **Troubleshooting**

### **Installation Fails**

**Problem:** Auto-installation fails

**Solutions:**
1. Check internet connection (for binary download)
2. Install build tools (for source build):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install git cmake build-essential
   
   # RHEL/CentOS
   sudo yum install git cmake gcc-c++
   ```
3. Set `USD_ROOT` environment variable:
   ```bash
   export USD_ROOT=/usr/local/USD
   ```
4. Install manually (see `OPTIONAL_PLUGINS.md`)

### **Plugins Not Loading**

**Problem:** Plugins installed but not loading

**Solutions:**
1. Verify installation:
   ```python
   installer.verify_installation()
   ```
2. Check plugin path:
   ```python
   print(installer.get_xstage_plugin_path())
   ```
3. Check USD version compatibility
4. Reinstall plugins:
   ```python
   installer.uninstall()
   installer.install()
   ```

### **Build Errors**

**Problem:** Source build fails

**Solutions:**
1. Ensure USD is properly installed
2. Check USD version (requires USD 23.11+)
3. Verify CMake can find USD:
   ```bash
   cmake -DUSD_ROOT=/path/to/usd ..
   ```
4. Check build logs for specific errors

---

## 📊 **Benefits**

### **Isolation**
- ✅ No system-wide changes
- ✅ Doesn't affect other USD applications
- ✅ Easy to uninstall (just delete `~/.xstage/`)

### **Convenience**
- ✅ Automatic installation
- ✅ No manual configuration needed
- ✅ Works out of the box

### **Flexibility**
- ✅ Can use system plugins if available
- ✅ Falls back to xStage plugins
- ✅ Can disable auto-install

---

## 🚫 **Uninstallation**

To remove xStage's Adobe plugins:

```python
from xstage.utils import AdobePluginInstaller

installer = AdobePluginInstaller()
installer.uninstall()
```

Or manually:
```bash
rm -rf ~/.xstage/plugins/adobe-usd-plugins
```

---

## 📚 **Related Documentation**

- **Adobe Plugins**: `docs/adobe-plugin-formats.md`
- **Optional Plugins**: `OPTIONAL_PLUGINS.md`
- **Installation Guide**: `docs/installation.md`

---

## ❓ **FAQ**

### **Q: Does this affect my system USD installation?**
**A:** No! Plugins are installed to `~/.xstage/plugins/` and only affect xStage.

### **Q: Can I use system plugins instead?**
**A:** Yes! xStage checks system plugins first. Auto-install only happens if system plugins are not found.

### **Q: What if I don't want auto-install?**
**A:** Set `auto_install=False` when creating `AdobeUSDConverter`.

### **Q: Can I install plugins for all users?**
**A:** Yes, but you'll need to install system-wide manually. xStage's auto-install is user-specific.

### **Q: Do I need internet for auto-install?**
**A:** Only if downloading pre-built binaries. Source build doesn't require internet (after cloning).

---

*Last Updated: After auto-install implementation*

