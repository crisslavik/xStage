# xStage

<div align="center">
  <img src="docs/assets/xstage-logo.svg" alt="xStage Logo" width="200"/>
  
  # xStage
  
  **Extended USD Viewer for Production Pipelines**
  
  [![CI](https://github.com/xstage-pipeline/xstage/workflows/CI/badge.svg)](...)
  [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](...)
  [![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](...)
  [![OpenUSD](https://img.shields.io/badge/OpenUSD-25.11-blue.svg)](...)
  
  [Features](#-features) • [Install](#-installation) • [Quick Start](#-quick-start) • [Docs](#-documentation)
  
  <img src="docs/assets/screenshot.png" alt="xStage Screenshot" width="800"/>
</div>

---

## 🎬 What is xStage?

**xStage** is a professional, production-ready USD viewer and converter built for VFX pipelines. It combines the power of OpenUSD with an intuitive interface and comprehensive toolset designed for real-world production workflows.

```bash
# View USD files
xstage scene.usd

# Convert FBX to USD with scale correction
xstage model.fbx --export output.usd --scale 0.01

# Convert with axis correction
xstage imported.obj --up-axis Z --flip-y
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
- **Measured Grid** - Houdini-style reference grid with real-world units
- **Payload Management** - Load/unload payloads for performance optimization

### 🎨 Editing & Management
- **Layer Composition** - Visualize and manage USD layer stack (subLayers, references, payloads)
- **Animation Curve Editor** - Edit animation curves with graph editor and keyframe manipulation
- **Material Editor** - Edit material properties, shader networks, and assignments
- **Prim Properties** - Edit transforms, attributes, and prim properties
- **Collection Editor** - Manage collection membership and material bindings
- **Primvar Editor** - Edit primvar values and interpolation modes
- **Render Settings** - Configure render settings, cameras, and AOVs
- **Namespace Editing** - Rename and move prims with namespace management

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
- **Nuke/Houdini Export** - Optimized export for pipeline tools

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

**PyPI:**
```bash
pip install xstage
```

**From source:**
```bash
git clone https://github.com/xstage-pipeline/xstage
cd xstage
pip install -e .
```

**Dependencies:**
- Python 3.9+
- PySide6 (Qt bindings)
- OpenUSD 25.11+ (usd-core)
- NumPy
- Optional: trimesh (for OBJ/STL/PLY conversion)
- Optional: pygltflib (for glTF conversion)

### Basic Usage

```bash
# View USD file
xstage scene.usd

# Convert FBX to USD with scale correction
xstage model.fbx --export output.usd --scale 0.01

# Convert with axis correction
xstage imported.obj --up-axis Z --flip-y

# Combine fixes
xstage import.obj --scale 0.001 --up-axis Z --flip-z
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
```bash
# Quick asset check with proper scale
xstage /pipeline/assets/character.fbx --scale 0.01
```

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

- **[User Guide](docs/user-guide.md)** - Complete user documentation
- **[Pipeline Integration](docs/pipeline.md)** - Pipeline setup and integration
- **[API Reference](docs/api.md)** - Complete API documentation
- **[Feature List](ADDED_FEATURES.md)** - All implemented features
- **[Future Features](FUTURE_FEATURES.md)** - Planned enhancements

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
