# xStage Quick Start Guide
## Pipeline-Friendly USD Viewer & Converter

---

## 🚀 Quick Start

### Installation
```bash
pip install xstage
# or
pip install -e .
```

### Basic Usage
```bash
# View USD file
xstage scene.usd

# Convert FBX to USD
xstage model.fbx --export output.usd --scale 0.01

# Convert with axis correction
xstage imported.obj --up-axis Z --flip-y
```

---

## 📋 Features Overview

### Viewer Features
- **Hydra 2.0 Rendering** - GPU-accelerated with proper materials
- **Layer Composition** - Visualize and manage layer stack
- **Animation Editor** - Edit animation curves
- **Material Editor** - Edit material properties
- **Scene Search** - Find prims quickly
- **Camera Management** - Switch and edit cameras
- **Prim Properties** - Edit transforms and attributes
- **Multi-Viewport** - Professional multi-view workflow

### Converter Features
- **FBX** → USD (multiple methods)
- **OBJ** → USD
- **Alembic (ABC)** → USD
- **glTF/GLB** → USD
- **STL/PLY** → USD
- **Batch Conversion** - Process multiple files

### Pipeline Integration
- Batch operations
- Progress reporting
- Error handling
- Pipeline config support
- Standard shot structure creation

---

## 🎯 Common Workflows

### Asset Review
```bash
# Quick review with scale correction
xstage /pipeline/assets/character.fbx --scale 0.01
```

### Batch Conversion
```python
from xstage import USDConverter, ConversionOptions

options = ConversionOptions(scale=0.01, up_axis='Y')
converter = USDConverter(options)

# Convert single file
converter.convert('model.fbx', 'model.usd')

# Batch convert
files = ['model1.fbx', 'model2.fbx', 'model3.fbx']
for f in files:
    converter.convert(f, f.replace('.fbx', '.usd'))
```

### Pipeline Integration
```python
from xstage import USDViewerWindow, PipelineIntegration

# Load pipeline config
pipeline = PipelineIntegration()
pipeline.load_config('/pipeline/config.json')

# Get asset
asset_path = pipeline.get_asset_path('character_01', 'model')

# View
viewer = USDViewerWindow()
viewer.load_usd_file(asset_path)
viewer.show()
```

---

## ⌨️ Keyboard Shortcuts

- **Ctrl+O** - Open USD file
- **Ctrl+I** - Import and convert
- **F** - Frame all geometry
- **F1** - Help

---

## 🛠️ Tools Menu

All advanced features are in the **Tools** menu:

- Layer Composition
- Animation Curve Editor
- Material Editor
- Scene Search & Filter
- Camera Management
- Prim Properties
- Collection Editor
- Primvar Editor
- Render Settings Editor
- Stage Variables
- Multi-Viewport
- Scene Comparison
- Batch Operations

---

## 📖 Help

- **Help Menu** → Help - Full documentation
- **Tooltips** - Hover over UI elements for quick help
- **Status Bar** - Shows current operation status

---

*xStage - Extended staging for extended pipelines* 🎬

