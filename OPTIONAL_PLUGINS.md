# Optional Plugins & Extensions
## Adobe USD Fileformat Plugins & MaterialX Support

This document explains optional components that enhance xStage functionality but are not Python packages.

---

## 🎨 **MaterialX Support**

### **Status**: ✅ **Included in usd-core**

MaterialX shader support is **already included** in the `usd-core` package. No additional installation needed!

**MaterialX** is an open standard for representing rich material and look-development content, launched at Industrial Light & Magic in 2012 and now hosted by the Academy Software Foundation. See [materialx.org](https://materialx.org/) and [GitHub](https://github.com/AcademySoftwareFoundation/MaterialX).

### **What's Included:**
- `UsdMtlx` module (MaterialX support)
- MaterialX Standard Surface shader support (`ND_standard_surface_surfaceshader`)
- Houdini Karma compatibility
- Nuke 17 MaterialX Standard Surface compatibility (beta)
- Blender MaterialX compatibility (stable)

### **Verification:**
```bash
# Check if MaterialX is available
python -c "from pxr import UsdMtlx; print('✅ MaterialX available')"
```

### **Usage:**
xStage automatically uses MaterialX/XMaterial when available:
```python
from xstage import USDConverter, ConversionOptions

# Auto-detect (recommended)
options = ConversionOptions(material_shader_type="auto")
# Will use MaterialX if available, else UsdPreviewSurface

# Explicit MaterialX
options = ConversionOptions(material_shader_type="MaterialX")
# Or use "XMaterial" for backward compatibility
```

### **If MaterialX Not Available:**
- xStage automatically falls back to `UsdPreviewSurface`
- All features work, just with standard USD shaders
- To enable MaterialX: Ensure your USD installation includes MaterialX (usually default)

---

## 🔌 **Adobe USD Fileformat Plugins**

### **Status**: ⚠️ **Optional C++ Plugins (Install Separately)**

Adobe USD Fileformat Plugins are **C++ plugins** (not Python packages) that must be installed separately. They provide native format support for FBX, OBJ, glTF, STL, PLY, and Substance (SBSAR).

### **Why Not in requirements.txt?**
- These are **C++ compiled plugins**, not Python packages
- They must be built from source or installed as binaries
- They integrate with USD's plugin system at runtime
- xStage automatically detects and uses them if available

### **What They Provide:**
- **FBX (usdFbx)**: Native FBX reading/writing ⭐ Primary focus
- **OBJ (usdObj)**: Enhanced OBJ with material support
- **glTF (usdGltf)**: Enhanced glTF with PBR materials
- **STL (usdStl)**: Native STL support
- **PLY**: Native PLY support
- **Substance (SBSAR)**: Adobe's proprietary material format

### **Installation Options:**

#### **Option 1: Build from Source (Recommended)**
```bash
# Clone Adobe's repository
git clone https://github.com/adobe/USD-Fileformat-plugins.git
cd USD-Fileformat-plugins

# Build
mkdir build && cd build
cmake -DUSD_ROOT=/usr/local/USD \
      -DCMAKE_INSTALL_PREFIX=/usr/local/USD \
      ..

make -j$(nproc)
sudo make install
```

#### **Option 2: Pre-built Binaries**
Check Adobe's releases page for pre-built packages:
- https://github.com/adobe/USD-Fileformat-plugins/releases

#### **Option 3: Package Manager**
Some distributions provide packages:
```bash
# Check your distribution's package manager
# Example for some systems:
# yum install adobe-usd-plugins
# apt-get install adobe-usd-plugins
```

### **Verification:**
```python
from xstage.converters.adobe_converter import AdobeUSDConverter
from xstage.converters.converter import ConversionOptions

converter = AdobeUSDConverter(ConversionOptions())
print(f"Adobe Plugins Available: {converter.adobe_plugins_available}")
```

Or check USD plugin registry:
```python
from pxr import Plug

registry = Plug.Registry()
plugins = ['usdFbx', 'usdObj', 'usdGltf', 'usdStl']

for plugin_name in plugins:
    plugin = registry.GetPluginWithName(plugin_name)
    if plugin:
        print(f"✅ {plugin_name}: {'loaded' if plugin.isLoaded else 'registered'}")
    else:
        print(f"❌ {plugin_name}: not found")
```

### **Benefits:**
1. **Native FBX Support**: No external conversion tools needed
2. **Better Material Support**: Enhanced material handling for OBJ and glTF
3. **Performance**: Direct file format reading without intermediate conversion
4. **Integration**: Seamless integration with USD pipeline

### **Fallback Behavior:**
If Adobe plugins are not available, xStage falls back to:
- Python libraries (trimesh, pygltflib)
- External CLI tools (usdcat, fbx2usd)
- Basic USD format support

**All features work without Adobe plugins**, but with reduced format support.

---

## 📊 **Comparison**

| Component | Type | Installation | Included in requirements.txt? |
|-----------|------|--------------|-------------------------------|
| **MaterialX** | USD Module | ✅ Included in usd-core | ✅ Yes (via usd-core) |
| **Adobe Plugins** | C++ Plugins | ⚠️ Install separately | ❌ No (C++ plugins, not Python) |

---

## 🚀 **Recommended Setup**

### **For Production Pipelines:**

1. **Install usd-core** (includes MaterialX):
   ```bash
   pip install usd-core>=23.11
   ```

2. **Install Adobe Plugins** (optional, for FBX support):
   ```bash
   # Build from source (see above)
   # Or use pre-built binaries
   ```

3. **Verify Installation:**
   ```python
   # Check MaterialX
   python -c "from pxr import UsdMtlx; print('MaterialX: ✅')"
   
   # Check Adobe plugins
   from xstage.converters.adobe_converter import AdobeUSDConverter
   converter = AdobeUSDConverter(ConversionOptions())
   print(f"Adobe Plugins: {'✅' if converter.adobe_plugins_available else '❌'}")
   ```

---

## 📚 **Documentation**

- **MaterialX**: See `docs/materialx-support.md`
- **Adobe Plugins**: See `docs/adobe-plugin-formats.md`
- **Houdini/Nuke Compatibility**: See `docs/HOUDINI_NUKE_COMPATIBILITY.md`
- **Best Practices**: See `docs/BEST_MATERIAL_PRACTICES.md`

---

## ❓ **FAQ**

### **Q: Do I need Adobe plugins for xStage to work?**
**A:** No! xStage works without Adobe plugins. They're optional enhancements for better FBX/OBJ/glTF support.

### **Q: Do I need to install MaterialX separately?**
**A:** No! MaterialX (UsdMtlx) is included in `usd-core`. Just install `usd-core` and MaterialX support is available.

### **Q: Why aren't Adobe plugins in requirements.txt?**
**A:** They're C++ compiled plugins, not Python packages. They must be installed separately via building from source or installing binaries.

### **Q: How do I know if plugins are available?**
**A:** xStage automatically detects and reports plugin availability. Check the converter's `adobe_plugins_available` attribute.

---

*Last Updated: After requirements.txt update*

