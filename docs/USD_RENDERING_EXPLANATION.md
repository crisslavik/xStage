# USD Rendering in xStage

## The Problem

When you run `xstage`, you might see:
```
Hydra 2.0 viewport is not available: cannot import name 'UsdImagingGL' from 'pxr'
Using OpenGL fallback
```

This happens because **`usd-core` from PyPI doesn't include `UsdImagingGL`**.

## Why This Happens

The `usd-core` package on PyPI is a **minimal USD build** that includes:
- ✅ Core USD Python bindings (`Usd`, `UsdGeom`, `UsdShade`, etc.)
- ✅ File I/O and stage management
- ❌ **NOT** `UsdImagingGL` (Hydra rendering)
- ❌ **NOT** `Glf` (GL Framework)
- ❌ **NOT** Full imaging/rendering support

## What This Means

### With OpenGL Fallback (Current):
- ✅ Basic geometry renders correctly
- ✅ Camera controls work
- ✅ Viewport navigation works
- ⚠️  Simple materials may work
- ❌ Complex materials may not render correctly
- ❌ Advanced lighting features limited
- ❌ Performance may be slower for large scenes

### With Full USD + Hydra (Like Omniverse):
- ✅ All of the above, PLUS:
- ✅ Proper material rendering (PBR, MaterialX, etc.)
- ✅ Advanced lighting (USD lights, light linking)
- ✅ GPU-accelerated rendering (Storm renderer)
- ✅ Better performance for large scenes
- ✅ Full USD 25.11 feature support

## Solutions

### Option 1: Use xStage's OpenGL Fallback (Current)
**Status:** Already working!

xStage automatically falls back to OpenGL rendering when `UsdImagingGL` is not available. This works for basic viewing and editing, but lacks advanced rendering features.

**To use:** Just run `xstage` or `./launch_usd_viewer.sh` - it will automatically use OpenGL fallback.

### Option 2: Install Full USD Build with Imaging Support

To get full Hydra rendering like Omniverse, you need a complete USD build:

#### Option 2a: Pre-built USD (Recommended)
1. Download pre-built USD from NVIDIA or Pixar
2. Set `PYTHONPATH` to point to USD's Python bindings
3. Ensure `UsdImagingGL` is available

**NVIDIA USD Builds:**
- https://developer.nvidia.com/usd
- Includes full imaging support

**Pixar USD Builds:**
- Build from source: https://github.com/PixarAnimationStudios/USD
- Enable imaging support during build

#### Option 2b: Build USD from Source
```bash
# Clone USD
git clone https://github.com/PixarAnimationStudios/USD.git
cd USD

# Configure with imaging support
python build_scripts/build_usd.py \
    --imaging \
    --openimageio \
    --opencolorio \
    --python \
    /path/to/usd/install

# Set environment
export PYTHONPATH=/path/to/usd/install/lib/python:$PYTHONPATH
```

### Option 3: Use NVIDIA Omniverse
For full-featured USD viewing with all rendering capabilities, consider using NVIDIA Omniverse, which includes a complete USD build with full imaging support.

## Checking Your Setup

Run the diagnostic script:
```bash
./scripts/check_usd_rendering.py
```

Or use the Hydra diagnostic:
```bash
./scripts/diagnose_hydra.py
```

## Current Status

**xStage works with OpenGL fallback**, which provides:
- Basic USD file viewing
- Geometry rendering
- Camera controls
- Basic editing capabilities

For **production-quality rendering** with materials and lighting, you'll need a full USD build with imaging support.

## Why xStage Uses OpenGL Fallback

xStage is designed to work **out of the box** without requiring complex USD builds. The OpenGL fallback ensures:
1. ✅ Easy installation (just `pip install usd-core`)
2. ✅ Works on any system
3. ✅ No complex build requirements
4. ✅ Good enough for basic viewing/editing

For advanced rendering, users can optionally install a full USD build.

## Summary

| Feature | OpenGL Fallback | Full USD + Hydra |
|---------|----------------|------------------|
| Basic geometry | ✅ | ✅ |
| Camera controls | ✅ | ✅ |
| Simple materials | ⚠️  | ✅ |
| Complex materials | ❌ | ✅ |
| Advanced lighting | ❌ | ✅ |
| GPU acceleration | ❌ | ✅ |
| Performance | Good | Excellent |
| Installation | Easy | Complex |

**Current recommendation:** Use OpenGL fallback for basic viewing/editing. Install full USD build only if you need advanced rendering features.
