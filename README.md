# xStage

<div align="center">
  <img src="docs/assets/xstage-logo.svg" alt="xStage Logo" width="200"/>
  
  # xStage
  
  **Extended USD Viewer for Production Pipelines**
  
  [![CI](https://github.com/xstage-pipeline/xstage/workflows/CI/badge.svg)](...)
  [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](...)
  [![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](...)
  [![OpenUSD](https://img.shields.io/badge/OpenUSD-25.11-blue.svg)](...)
  
  [Features](#features) • [Install](#install) • [Docs](#docs) • [Community](#community)
  
  <img src="docs/assets/screenshot.png" alt="xStage Screenshot" width="800"/>
</div>

---

## 🎬 What is xStage?

**xStage** is a professional USD viewer built for VFX pipelines. Think `usdview`, but with the features production demands.
```bash
# Install
pip install xstage

# Run
xstage my-scene.usd

# With scale correction
xstage model.fbx --scale 0.01

# With axis conversion
xstage imported.obj --up-axis Z --flip-y
```

## ⚡ Why xStage?

| Feature | xStage | usdview | Commercial |
|---------|--------|---------|------------|
| **Open Source** | ✅ | ✅ | ❌ |
| **Scene Scale** | ✅ | ❌ | ✅ |
| **Axis Orientation** | ✅ | ❌ | ✅ |
| **Measured Grid** | ✅ | ❌ | ✅ |
| **Pipeline Tools** | ✅ | ❌ | ✅ |
| **Plugin System** | ✅ | ❌ | ✅ |
| **Hydra 2.0** | ✅ | ✅ | ⚠️ |

## 🌟 Features

### Extended Viewing
- 📏 **Scene Scale Control** - Fix imports with wrong units (mm→m, cm→m)
- 🔄 **Axis Orientation** - Handle Y-up/Z-up, flipped axes
- 📐 **Measured Grid** - Houdini-style reference grid with meters
- 🎬 **Timeline** - Full animation playback

### Production Ready
- 🚀 **Hydra 2.0** - Blazing fast rendering
- 🔌 **Plugins** - Extend with custom tools
- 📊 **Pipeline Integration** - ShotGrid, Nuke, Houdini
- ✅ **Validation** - Built-in USD quality checks

### Format Support
- **View**: USD, USDA, USDC, USDZ
- **Import**: FBX, OBJ, glTF, Alembic, STL, PLY
- **Export**: All USD formats

## 🚀 Quick Start
```bash
# Basic viewing
xstage scene.usd

# Fix scale (FBX from cm to meters)
xstage model.fbx --scale 0.01

# Convert axis (OBJ Y-up to Z-up)
xstage mesh.obj --up-axis Z

# Flip inverted axis
xstage broken.fbx --flip-y

# Combine fixes
xstage import.obj --scale 0.001 --up-axis Z --flip-z
```

## 📦 Installation

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

**RHEL/AlmaLinux:**
```bash
sudo dnf install xstage
```

[Full installation guide →](docs/installation.md)

## 🎯 Use Cases

**Asset Review:**
```bash
# Quick asset check with proper scale
xstage /mnt/assets/character.fbx --scale 0.01
```

**Pipeline Integration:**
```python
from xstage import Viewer

viewer = Viewer()
viewer.load_stage("/path/to/scene.usd")
viewer.set_scale(0.01)  # Fix import scale
viewer.show()
```

**Batch Conversion:**
```bash
# Convert all FBX to USD
for file in *.fbx; do
    xstage "$file" --export "${file%.fbx}.usd" --scale 0.01
done
```

## 📖 Documentation

- [User Guide](https://xstage-pipeline.github.io/docs/user-guide)
- [Pipeline Integration](https://xstage-pipeline.github.io/docs/pipeline)
- [Plugin Development](https://xstage-pipeline.github.io/docs/plugins)
- [API Reference](https://xstage-pipeline.github.io/docs/api)

## 🤝 Community

- [Discord](https://discord.gg/xstage) - Chat with the community
- [Forum](https://github.com/xstage-pipeline/xstage/discussions) - Q&A
- [Twitter](https://twitter.com/xstage_pipeline) - Updates

## 🙏 Credits

Built with:
- [OpenUSD](https://openusd.org) by Pixar
- [Qt/PySide6](https://qt.io)

**Production-proven at [NOX VFX](https://nox-vfx.com)** 🎬

---

<div align="center">
  <b>Extended staging for extended pipelines</b>
  <br>
  <sub>Apache 2.0 License • Made by the VFX community</sub>
</div>
```

---

## 🌐 Domain & Social

### Domain
**Primary:** `xstage.org` or `xstage-pipeline.org`

**Alternatives:**
- `xstage.io` (tech-focused)
- `getxstage.com` (marketing)
- `xstage.dev` (developer-focused)

### Social Handles
- **GitHub:** `@xstage-pipeline`
- **Twitter/X:** `@xstage_pipeline`
- **Discord:** `xStage Pipeline`
- **YouTube:** `@xstage-pipeline`

---

## 🎬 Launch Announcement
```
🎬 Introducing xStage - Extended USD Viewer

After years in production at NOX VFX, we're open-sourcing our USD viewer!

✨ What makes xStage different?
- Scene scale control (fix cm→m imports)
- Axis orientation (Y-up/Z-up, flips)
- Measured grid (Houdini-style)
- Hydra 2.0 powered
- Pipeline integration
- 100% open source

Built for pipelines, by pipeline artists.

🔗 github.com/xstage-pipeline/xstage
📖 xstage.org

#OpenUSD #VFX #Pipeline #OpenSource