# Adobe USD Fileformat Plugins - Supported Formats

## Overview

Adobe's open-source USD Fileformat Plugins extend USD's native format support by providing enhanced readers and writers for several widely-used 3D file formats. These plugins enable USD to directly read and write these formats as if they were native USD files.

## Supported Formats

### 1. **FBX (Filmbox)** ⭐ Primary Focus
- **Plugin Name**: `usdFbx`
- **Status**: Native reading and writing
- **Features**:
  - Full scene hierarchy preservation
  - Materials and textures
  - Animation (keyframes, curves)
  - Cameras and lights
  - No external dependencies when plugin is installed
- **Installation**: Requires Adobe USD Fileformat Plugins or FBX Python SDK

### 2. **OBJ (Wavefront OBJ)**
- **Plugin Name**: `usdObj`
- **Status**: Enhanced with material support
- **Features**:
  - Geometry (vertices, faces, normals)
  - UV coordinates
  - Material library (.mtl) support
  - Improved over USD's basic OBJ support

### 3. **glTF / GLB (GL Transmission Format)**
- **Plugin Name**: `usdGltf`
- **Status**: Enhanced with PBR materials
- **Features**:
  - Static models
  - Animations
  - Scenes
  - PBR (Physically Based Rendering) materials
  - Textures
  - Optimized for web applications

### 4. **STL (Stereolithography)**
- **Plugin Name**: `usdStl`
- **Status**: Native support
- **Features**:
  - 3D printing format
  - Triangle meshes
  - Binary and ASCII formats

### 5. **PLY (Polygon File Format)**
- **Status**: Native support
- **Features**:
  - 3D scanner data
  - Point clouds
  - Polygon meshes
  - Color and normal data

### 6. **Substance (SBSAR)** - Adobe Proprietary
- **Status**: Adobe's proprietary format
- **Features**:
  - Materials and textures
  - Substance Designer integration
  - Procedural materials

## Plugin Detection

The plugins are registered with USD's plugin system and can be checked:

```python
from pxr import Plug

registry = Plug.Registry()
plugins = ['usdFbx', 'usdObj', 'usdGltf', 'usdStl']

for plugin_name in plugins:
    plugin = registry.GetPluginWithName(plugin_name)
    if plugin:
        print(f"✓ {plugin_name}: {'loaded' if plugin.isLoaded else 'registered'}")
    else:
        print(f"✗ {plugin_name}: not found")
```

## Usage in xStage

When Adobe plugins are installed, xStage automatically uses them for conversion:

```python
from xstage.converters.adobe_converter import AdobeUSDConverter
from xstage.converters.converter import ConversionOptions

options = ConversionOptions()
converter = AdobeUSDConverter(options)

# FBX conversion uses Adobe plugin if available
converter.convert("model.fbx", "model.usd")
```

## Installation

### Option 1: Build from Source (Recommended)
```bash
git clone https://github.com/adobe/USD-Fileformat-plugins.git
cd USD-Fileformat-plugins
mkdir build && cd build

cmake -DUSD_ROOT=/usr/local/USD \
      -DCMAKE_INSTALL_PREFIX=/usr/local/USD \
      ..

make -j$(nproc)
sudo make install
```

### Option 2: Use xStage Installer Script
```bash
./scripts/install_adobe_plugins.sh
```

## Benefits Over Standard USD

1. **Native FBX Support**: No need for external conversion tools
2. **Better Material Support**: Enhanced material handling for OBJ and glTF
3. **Performance**: Direct file format reading without intermediate conversion
4. **Integration**: Seamless integration with USD pipeline

## Comparison with Standard USD

| Format | Standard USD | With Adobe Plugins |
|--------|--------------|-------------------|
| FBX | ❌ Requires external tools | ✅ Native support |
| OBJ | ⚠️ Basic support | ✅ Enhanced with materials |
| glTF | ⚠️ Basic support | ✅ Enhanced with PBR |
| STL | ⚠️ Basic support | ✅ Native support |
| PLY | ⚠️ Basic support | ✅ Native support |

## Resources

- **GitHub Repository**: https://github.com/adobe/USD-Fileformat-plugins
- **Documentation**: See Adobe's USD Fileformat Plugins repository
- **Presentation**: [Adobe's USD File Format Plugins for Interoperability](https://www.youtube.com/watch?v=4F4wNc3Bu80)

## Notes

- Adobe plugins are **read-only** for some formats (they enable USD to read these formats)
- For writing, you may still need format-specific exporters
- FBX support is the primary focus and most mature feature
- Other formats benefit from improved material and texture handling

