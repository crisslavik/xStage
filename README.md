# xStage

<div align="center">
  <img src="docs/assets/xstage-logo.svg" alt="xStage Logo" width="200"/>
  
  # xStage
  
  **Extended USD Viewer for Production Pipelines**
  
  [![CI](https://github.com/xstage-pipeline/xstage/workflows/CI/badge.svg)](...)
  [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](...)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg)](...)
  [![OpenUSD](https://img.shields.io/badge/OpenUSD-25.11-blue.svg)](...)
  
  [Features](#-features) • [Install](#-installation) • [Quick Start](#-quick-start) • [Docs](#-documentation)
  
  <img src="docs/assets/screenshot.png" alt="xStage Screenshot" width="800"/>
</div>

---

## 🎬 What is xStage?

**xStage** is a professional, production-ready USD viewer and converter built for VFX pipelines. It combines the power of OpenUSD with an intuitive interface and comprehensive toolset designed for real-world production workflows.

```bash
# Install xStage (self-contained, includes Python 3.11, USD 25.11+, OCIO 2.2+, QuiltiX)
git clone https://github.com/xstage-pipeline/xstage
cd xstage
./scripts/install.sh

# Launch xStage
./launch_usd_viewer.sh

# Then use the GUI for:
# - Viewing USD files (File → Open USD)
# - Converting formats (File → Import & Convert)
# - Editing materials, lights, cameras, and more
```

---

## ⚡ Why xStage?

| Feature | xStage | usdview | Commercial Tools |
|---------|--------|---------|------------------|
| **Open Source** | ✅ | ✅ | ❌ |
| **Hydra 2.0 Rendering** | ✅ | ✅ | ⚠️ |
| **Scene Scale Control** | ✅ | ❌ | ✅ |
| **Axis Orientation** | ✅ | ❌ | ✅ |
| **Format Converter** | ✅ (8+ formats) | ❌ | ✅ |
| **Layer Composition** | ✅ | ⚠️ | ✅ |
| **Animation Editor** | ✅ | ❌ | ✅ |
| **Material Editor** | ✅ | ❌ | ✅ |
| **Multi-Viewport** | ✅ | ❌ | ✅ |
| **Scene Comparison** | ✅ | ❌ | ✅ |
| **Pipeline Integration** | ✅ | ❌ | ✅ |
| **OpenExec Support** | ✅ | ❌ | ⚠️ |
| **Theme System** | ✅ | ❌ | ✅ |
| **Viewport Overlays** | ✅ | ❌ | ✅ |
| **Selection Sets** | ✅ | ❌ | ✅ |
| **Smart Caching** | ✅ | ❌ | ⚠️ |
| **LOD System** | ✅ | ❌ | ⚠️ |
| **AOV Visualization** | ✅ | ❌ | ✅ |
| **Texture/Material Preview** | ✅ | ❌ | ✅ |

---

## 🌟 Features

### 🎬 Core Viewer
- **Hydra 2.0 GPU Rendering** - Blazing fast, GPU-accelerated rendering with proper material support
- **OpenGL Fallback** - Reliable fallback rendering for compatibility
- **Scene Hierarchy** - Full scene graph navigation with icons and indicators
- **Timeline & Playback** - Full animation timeline with scrubbing and playback controls
- **Camera Controls** - Intuitive rotate, pan, zoom with frame-all support
- **Depth of Field (DOF)** - Camera focus distance and f-stop controls (USD 25.11+)
- **Look-Through Lights** - View scene from light's perspective (USD 25.11+)
- **Measured Grid** - Houdini-style reference grid with real-world units
- **Payload Management** - Load/unload payloads for performance optimization

### 🎨 Editing & Management
- **Layer Composition** - Visualize and manage USD layer stack (subLayers, references, payloads)
- **Animation Curve Editor** - Edit animation curves with graph editor and keyframe manipulation
- **Material Editor** - Edit material properties, shader networks, and assignments
- **Light Management** - Manage lights, properties, and light linking (USD 25.11+)
- **Light Linking** - Control which lights affect which objects (USD 25.11+)
- **Prim Properties** - Edit transforms, attributes, and prim properties
- **Collection Editor** - Manage collection membership and material bindings
- **Primvar Editor** - Edit primvar values and interpolation modes
- **Render Settings** - Configure render settings, cameras, and AOVs
- **Namespace Editing** - Rename and move prims with namespace management
- **OCIO Preferences** - Configure color management with custom OCIO config files

### 🔍 Search & Navigation
- **Scene Graph Search** - Advanced search and filtering by name, type, path, metadata
- **Multi-Viewport** - Professional multi-view workflow (perspective, top, front, side)
- **Camera Management** - Switch between cameras, edit properties, create new cameras
- **Bookmarks** - Quick access to frequently used prims and locations
- **Recent Files** - Quick access to recently opened files
- **Selection Sets** - Save and manage named selection groups

### 🔄 Conversion & Import
- **Comprehensive Converter** - Convert 8+ formats to USD:
  - **FBX** → USD (multiple conversion methods)
  - **OBJ** → USD
  - **Alembic (ABC)** → USD
  - **glTF/GLB** → USD
  - **STL** → USD
  - **PLY** → USD
  - **Collada (DAE)** → USD
  - **3DS** → USD
- **Batch Conversion** - Process multiple files at once
- **Progress Reporting** - Real-time progress bars for long operations
- **Conversion Options** - Scale, axis correction, material export, UV/normal export

### 🚀 Advanced Features
- **Undo/Redo System** - Safe editing with full undo/redo support
- **Scene Comparison/Diff** - Compare two USD stages side-by-side
- **Batch Operations** - Process multiple prims simultaneously
- **Performance Profiling** - Track performance metrics and optimization
- **OpenExec Support** - Computed attributes and automatic extent calculations
- **Stage Variables** - Manage stage variables for dynamic asset paths
- **Coordinate Systems** - Support for coordinate system bindings
- **Variant Sets** - View and switch variant selections
- **USD Validation** - Built-in USD compliance checking
- **Smart Caching** - Geometry, bounds, and transform caching for performance
- **LOD System** - Automatic Level of Detail management
- **Instancing Optimization** - Instance detection and memory optimization
- **AOV Visualization** - Render Var extraction and preview
- **Texture/Material Preview** - Preview textures and materials on 3D geometry

### 🔗 Pipeline Integration
- **Pipeline Configuration** - Easy integration with VFX pipelines
- **Asset Path Management** - Standard asset path resolution
- **Shot Stage Creation** - Create standard shot structures
- **Nuke/Houdini/Blender Export** - Optimized export for pipeline tools (Nuke 17 beta with USD support, Blender latest release)
- **OCIO Color Management** - Full OpenColorIO 2.2+ integration for color-accurate asset review
- **QuiltiX Integration** - Launch QuiltiX MaterialX editor for material editing

### 📚 Help & Documentation
- **Help System** - In-app help with context-sensitive tooltips
- **Tooltips** - Comprehensive tooltips for all UI elements
- **Documentation** - Complete user documentation

### 🎨 UI & Polish
- **Theme System** - Dark, Light, and High Contrast themes
- **Viewport Overlays** - FPS counter, statistics, memory usage, selection info
- **Customizable UI** - Professional, polished interface

---

## 🚀 Quick Start

### Platform Support
xStage is fully supported on:
- ✅ **Ubuntu** 20.04 LTS, 22.04 LTS, 24.04 LTS
- ✅ **RHEL 9** (Red Hat Enterprise Linux 9)
- ✅ **RHEL 10** (Red Hat Enterprise Linux 10)
- ✅ **AlmaLinux** 9/10, **Rocky Linux** 9/10

See [Platform Support Guide](docs/platform-support.md) for detailed installation instructions.

### Installation

xStage uses a **self-contained installation** that automatically installs Python 3.11, USD 25.11+, OCIO 2.2+, and QuiltiX - all isolated within the xStage directory.

**Quick Install:**
```bash
git clone https://github.com/xstage-pipeline/xstage
cd xstage
./scripts/install.sh
```

The installation script will:
- ✅ Install Python 3.11 (self-contained in `.xstage_python/`)
- ✅ Create virtual environment with Python 3.11 (`.xstage_venv/`)
- ✅ Automatically install USD 25.11+ (`usd-core>=25.11`)
- ✅ Automatically install OCIO 2.2+ (`PyOpenColorIO>=2.2.0`)
- ✅ Automatically install QuiltiX (`quiltix>=1.0.0`)
- ✅ Install all other dependencies
- ✅ Create launch script (`./launch_usd_viewer.sh`)

**Run xStage:**
```bash
# Using launch script (recommended)
./launch_usd_viewer.sh

# Or manually
source .xstage_venv/bin/activate
python3 src/xstage/core/viewer.py
```

**Dependencies (automatically installed):**
- Python 3.11 (installed self-contained if not available)
- OpenUSD 25.11+ (usd-core) - automatically installed
- OCIO 2.2+ (PyOpenColorIO) - automatically installed
- QuiltiX (MaterialX editor) - automatically installed
- PySide6 (Qt bindings) - automatically installed
- NumPy - automatically installed
- All other dependencies - automatically installed

**Note:** Everything is self-contained in the xStage directory. No system-wide packages or symlinks are created.

### Basic Usage

After installation, launch xStage and use the GUI:

```bash
# Launch xStage
./launch_usd_viewer.sh

# Or if virtual environment is activated
python3 src/xstage/core/viewer.py
```

**In the GUI:**
- **File → Open USD** - Open USD files (.usd, .usda, .usdc, .usdz)
- **File → Import & Convert** - Convert other formats (FBX, OBJ, glTF, etc.) to USD
- **Tools → Material Editor** - Edit materials and shaders
- **Tools → Animation Curve Editor** - Edit animation curves
- **Tools → Camera Management** - Manage cameras and depth of field
- **Tools → Light Management** - Manage lights and light linking (USD 25.11+)
- **View → Preferences** - Configure OCIO color management

**Command Line (Python API):**
```python
from xstage.core.viewer import USDViewerWindow

# Create viewer
viewer = USDViewerWindow()
viewer.load_usd_file("scene.usd")
viewer.show()
```

### Python API

```python
from xstage.core.viewer import USDViewerWindow
# Or use the convenience import:
# from xstage import USDViewerWindow

# Create viewer
viewer = USDViewerWindow()
viewer.load_usd_file("scene.usd")
viewer.show()
```

### Converter API

```python
from xstage import USDConverter, ConversionOptions

# Create converter
options = ConversionOptions(
    scale=0.01,
    up_axis='Y',
    export_materials=True
)
converter = USDConverter(options)

# Convert file
converter.convert("model.fbx", "model.usd")
```

---

## 🎯 Use Cases

### Asset Review
1. Launch xStage: `./launch_usd_viewer.sh`
2. **File → Import & Convert** - Import FBX/OBJ/glTF files
3. Configure scale and axis correction in the conversion dialog
4. Review assets with proper color management (OCIO)
5. Use **Tools → Light Management** for lighting review (USD 25.11+)

### Animation Editing
- Edit animation curves directly in viewer
- Visualize and adjust keyframes
- Export/import animation data

### Material Workflows
- Edit material properties
- Assign materials to prims
- Preview material changes
- Manage material libraries

### Scene Management
- Compare scene versions
- Manage layer composition
- Edit prim properties
- Organize with collections

### Pipeline Integration
```python
from xstage import PipelineIntegration

pipeline = PipelineIntegration()
pipeline.load_config("/path/to/pipeline.json")
asset_path = pipeline.get_asset_path("character_01", "model")
```

### Batch Processing
```python
from xstage import BatchOperationManager

# Batch convert files
files = ["model1.fbx", "model2.fbx", "model3.fbx"]
for f in files:
    converter.convert(f, f.replace('.fbx', '.usd'))
```

---

## 📖 Documentation

- **[Feature List](docs/ADDED_FEATURES.md)** - All implemented features
- **[Future Features](docs/FUTURE_FEATURES.md)** - Planned enhancements
- **[Documentation Index](DOCUMENTATION_INDEX.md)** - Complete documentation guide
- **[Platform Support](docs/platform-support.md)** - Installation by platform
- **[Material Support](docs/materialx-support.md)** - MaterialX and shader support

---

## 🛠️ Tools Menu

All advanced features are accessible from the **Tools** menu:

- **Layer Composition** - Visualize and manage layer stack
- **Animation Curve Editor** - Edit animation curves
- **Material Editor** - Edit material properties
- **Scene Search & Filter** - Advanced search and filtering
- **Camera Management** - Manage cameras
- **Prim Properties** - Edit prim properties
- **Collection Editor** - Edit collections
- **Primvar Editor** - Edit primvars
- **Render Settings Editor** - Configure render settings
- **Stage Variables** - Manage stage variables
- **OpenExec** - Computed attributes and extent calculations
- **Multi-Viewport** - Multiple synchronized viewports
- **Scene Comparison** - Compare two stages
- **Batch Operations** - Process multiple prims/files
- **AOV Visualization** - Render Var extraction and preview
- **Texture/Material Preview** - Preview textures and materials
- **Selection Sets** - Save and manage named selection groups

---

## ⌨️ Keyboard Shortcuts

- **Ctrl+O** - Open USD file
- **Ctrl+I** - Import and convert
- **F** - Frame all geometry
- **F1** - Help
- **Space** - Play/pause animation
- **Left/Right Arrow** - Previous/Next frame

## 🎨 View Menu

- **Theme** - Switch between Dark, Light, and High Contrast themes
- **Show Viewport Overlay** - Toggle FPS, stats, and memory display
- **Recent Files** - Quick access to recently opened files
- **Bookmarks** - Access saved bookmarks

---

## 🤝 Community

- **[Discord](https://discord.gg/xstage)** - Chat with the community
- **[GitHub Discussions](https://github.com/xstage-pipeline/xstage/discussions)** - Q&A and discussions
- **[Issues](https://github.com/xstage-pipeline/xstage/issues)** - Bug reports and feature requests

---

## 🙏 Credits

Built with:
- **[OpenUSD](https://openusd.org)** by Pixar - Universal Scene Description
- **[Qt/PySide6](https://qt.io)** - Cross-platform UI framework
- **[NumPy](https://numpy.org)** - Numerical computing

**Production-proven at [NOX VFX](https://nox-vfx.com)** 🎬

---

## 📊 Statistics

- **34+ Features Implemented** - All high and medium priority features complete, plus Phase 1-3 enhancements
- **8+ Format Support** - Comprehensive converter system
- **50+ Modules** - Well-organized, maintainable codebase
- **Production Ready** - Fully tested and pipeline-integrated
- **Phase 1-3 Complete** - Polish, Performance, and Visual Features implemented

---

## 🎉 Status

**xStage is production-ready!** All critical features have been implemented:
- ✅ Hydra 2.0 rendering
- ✅ Complete editing capabilities
- ✅ Comprehensive converter
- ✅ Pipeline integration
- ✅ Professional workflow tools

---

<div align="center">
  <b>Extended staging for extended pipelines</b>
  <br>
  <sub>Apache 2.0 License • Made by the VFX community</sub>
</div>
