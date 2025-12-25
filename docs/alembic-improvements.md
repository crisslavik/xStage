# Alembic File Support Improvements

## Overview

Enhanced Alembic (.abc) file support in xStage with multiple conversion methods, better error handling, and Alembic-specific features.

## Improvements Made

### 1. **Enhanced Plugin Detection**
- Automatic detection of USD Alembic plugin (usdAbc)
- Plugin loading with error handling
- Fallback methods when plugin unavailable
- Clear error messages for missing dependencies

### 2. **Multiple Conversion Methods**
Three-tier fallback system:

1. **USD Native Plugin (Primary)**
   - Direct Alembic reading via `usdAbc` plugin
   - Best for animated data
   - Preserves time samples
   - Full scene hierarchy

2. **usdcat CLI Tool (Secondary)**
   - Reliable fallback
   - Supports flattening options
   - Time range selection

3. **Python Alembic Library (Tertiary)**
   - Direct Python API access
   - Manual conversion when plugins unavailable
   - Supports meshes, transforms, cameras

### 3. **Time Sample Support**
- Automatic detection of animated Alembic files
- Option to preserve or flatten time samples
- Frame range selection
- FPS configuration

### 4. **Better Progress Reporting**
- Detailed progress messages
- Time range information for animated files
- Clear error messages
- Step-by-step conversion status

### 5. **Enhanced Data Conversion**
- Mesh geometry (vertices, faces)
- Normals (with interpolation)
- UV coordinates
- Transforms (hierarchical)
- Cameras (focal length, aperture)
- Materials and properties

### 6. **Error Handling**
- Graceful fallbacks between methods
- Detailed error messages
- Timeout handling for large files
- Plugin loading errors caught

## Usage

### Basic Conversion
```python
from xstage.converters import USDConverter, ConversionOptions

options = ConversionOptions()
converter = USDConverter(options)

# Convert Alembic to USD
converter.convert("scene.abc", "scene.usd")
```

### With Time Samples
```python
options = ConversionOptions(
    time_samples=True,
    start_frame=1.0,
    end_frame=100.0,
    fps=24.0
)

converter = USDConverter(options)
converter.convert("animated.abc", "animated.usd")
```

### Flattened (Single Time)
```python
options = ConversionOptions(
    time_samples=False  # Flatten to default time
)

converter = USDConverter(options)
converter.convert("static.abc", "static.usd")
```

## Requirements

### Option 1: USD with Alembic Plugin (Recommended)
```bash
# Build USD with Alembic support
cmake -DPXR_BUILD_ALEMBIC_PLUGIN=ON ...
```

### Option 2: usdcat CLI Tool
```bash
# Usually included with USD installation
usdcat --version
```

### Option 3: Python Alembic Library
```bash
pip install alembic
```

## Known Limitations

1. **Alembic Schema Limitations**
   - FaceSet not fully supported
   - NuPatch (NURBS) limited support
   - Light types may not convert perfectly

2. **Performance**
   - Alembic files in composed USD scenes may be slower than native USD
   - Large animated files may take time to process

3. **Component Ops**
   - Alembic Component Ops flattened to 4x4 Matrix
   - Some transform precision may be lost

## Troubleshooting

### Plugin Not Found
```
Error: USD Alembic plugin (usdAbc) not found
```
**Solution**: Install USD with Alembic plugin support:
```bash
# Rebuild USD with Alembic support
cmake -DPXR_BUILD_ALEMBIC_PLUGIN=ON ...
```

### Conversion Timeout
```
Error: usdcat conversion timed out
```
**Solution**: 
- Use native plugin method (faster)
- Process smaller time ranges
- Increase timeout for very large files

### File Won't Open
```
Error: Failed to open Alembic file
```
**Solution**:
- Verify Alembic file is valid
- Check file permissions
- Try alternative conversion method

## Best Practices

1. **For Animated Data**: Use native plugin with `time_samples=True`
2. **For Static Scenes**: Use flattened conversion for smaller files
3. **For Large Files**: Use usdcat CLI for better memory handling
4. **For Pipeline Integration**: Always check plugin availability first

## Future Enhancements

- [ ] Support for Alembic FaceSet
- [ ] Better NuPatch (NURBS) support
- [ ] Light type conversion improvements
- [ ] Parallel processing for large files
- [ ] Alembic-specific material handling
- [ ] Point cloud support
- [ ] Curve and hair support

