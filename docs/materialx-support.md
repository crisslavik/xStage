# MaterialX Shader Support
## Material Creation During Format Conversion

xStage now supports creating USD materials with various shader types during format conversion, including **MaterialX Standard Surface** shaders.

**MaterialX** is an open standard for representing rich material and look-development content in computer graphics, enabling platform-independent description and exchange across applications and renderers. MaterialX was launched at Industrial Light & Magic in 2012 and became an Academy Software Foundation hosted project in 2021.

- **Official Website**: https://materialx.org/
- **GitHub Repository**: https://github.com/AcademySoftwareFoundation/MaterialX

---

## Supported Shader Types

### 1. **UsdPreviewSurface** (Default)
Standard USD shader for basic PBR materials.

### 2. **MaterialX** ⭐ (Recommended)
MaterialX Standard Surface shader. This is the recommended shader type for production pipelines.

**Note**: "XMaterial" is an alias for MaterialX (maintained for backward compatibility).

### 3. **Karma**
Houdini Karma-optimized MaterialX Standard Surface.

### 4. **Nuke**
Nuke 17 MaterialX Standard Surface (beta).

### 5. **Blender**
Blender MaterialX Standard Surface (stable).

### 6. **glTF_PBR**
glTF PBR material shader (uses UsdPreviewSurface with glTF conventions).

---

## Usage

### Command Line

```bash
# Convert with MaterialX shader (recommended)
xstage model.fbx --export output.usd --material-shader MaterialX

# Convert with XMaterial shader (alias for MaterialX, backward compatibility)
xstage model.fbx --export output.usd --material-shader XMaterial

# Convert with UsdPreviewSurface (default)
xstage model.fbx --export output.usd --material-shader UsdPreviewSurface
```

### Python API

```python
from xstage import USDConverter, ConversionOptions, MaterialShaderType

# Create converter with MaterialX shader (recommended)
options = ConversionOptions(
    material_shader_type="MaterialX",  # Use MaterialX (or "XMaterial" for backward compatibility)
    export_materials=True
)
converter = USDConverter(options)

# Convert file
converter.convert("model.fbx", "model.usd")
```

### Using MaterialCreator Directly

```python
from xstage.converters.material_creator import MaterialCreator, MaterialShaderType

# Create MaterialX shader
creator = MaterialCreator(shader_type=MaterialShaderType.MATERIALX)
# Or use XMATERIAL for backward compatibility: MaterialShaderType.XMATERIAL

# Create material
material = creator.create_material(
    stage=stage,
    material_path="/Materials/MyMaterial",
    material_data={
        'baseColor': [0.8, 0.2, 0.2],
        'metallic': 0.5,
        'roughness': 0.3
    }
)

# Bind to prim
creator.bind_material_to_prim(material, mesh_prim)
```

---

## Material Data Extraction

The converter automatically extracts material data from source formats:

### FBX Materials
- `DiffuseColor` → `baseColor`
- `ReflectionFactor` → `metallic`
- `Shininess` → `roughness`
- `Diffuse` texture → `diffuseTexture`

### glTF Materials
- `pbrMetallicRoughness.baseColorFactor` → `baseColor`
- `pbrMetallicRoughness.metallicFactor` → `metallic`
- `pbrMetallicRoughness.roughnessFactor` → `roughness`
- `pbrMetallicRoughness.baseColorTexture` → `baseColorTexture`

### OBJ Materials (MTL)
- `Kd` → `baseColor`
- `map_Kd` → `diffuseTexture`
- `map_Bump` → `normalMap`

---

## MaterialX Shader Details

MaterialX Standard Surface provides:

- **Advanced Material Support**: Full MaterialX node graph support
- **Production-Ready**: Used in professional VFX pipelines (ILM, Sony Pictures Imageworks, Pixar, Autodesk, Adobe, SideFX)
- **Interoperability**: Works with MaterialX-compatible renderers (Arnold, RenderMan, Karma, etc.)
- **Node Graph**: Supports complex material networks
- **Open Standard**: Academy Software Foundation hosted project

### MaterialX Shader ID
- Shader ID: `ND_standard_surface_surfaceshader` (MaterialX Standard Surface)
- Based on the official MaterialX specification
- Compatible with all MaterialX renderers

**Note**: "XMaterial" was an alias for MaterialX Standard Surface. The code now uses the official MaterialX shader ID.

---

## Requirements

### For MaterialX Support

1. **MaterialX Plugin**: Requires `UsdMtlx` plugin
   ```bash
   # Check if available
   python -c "from pxr import UsdMtlx; print('MaterialX available')"
   ```

2. **MaterialX Library**: MaterialX should be compiled with USD
   - Usually included in USD distributions
   - Or install separately: https://github.com/AcademySoftwareFoundation/MaterialX

### Fallback Behavior

If MaterialX is not available, the converter automatically falls back to `UsdPreviewSurface` shader.

---

## Material Properties

### Supported Properties

- `baseColor` / `diffuseColor`: Base color (RGB)
- `metallic`: Metallic factor (0.0 - 1.0)
- `roughness`: Roughness factor (0.0 - 1.0)
- `specular`: Specular factor (0.0 - 1.0)
- `emissiveColor`: Emissive color (RGB)
- `opacity`: Opacity (0.0 - 1.0)

### Texture Support

- `baseColorTexture` / `diffuseTexture`: Base color texture
- `normalMap`: Normal map texture
- `metallicRoughnessTexture`: Combined metallic/roughness texture

---

## Examples

### Example 1: Convert FBX with MaterialX

```python
from xstage import USDConverter, ConversionOptions

# Create converter with MaterialX shader
options = ConversionOptions(
    material_shader_type="MaterialX",
    export_materials=True,
    validate_materials=True
)

converter = USDConverter(options)
converter.convert("character.fbx", "character.usd")
```

### Example 2: Create MaterialX Material Directly

```python
from xstage.converters.material_creator import MaterialCreator, MaterialShaderType
from pxr import Usd, UsdUtils

# Create stage
stage = Usd.Stage.CreateNew("materials.usd")

# Create MaterialX shader
creator = MaterialCreator(shader_type=MaterialShaderType.MATERIALX)

# Create material
material = creator.create_material(
    stage=stage,
    material_path="/Materials/MyMaterial",
    material_data={
        'baseColor': [0.8, 0.2, 0.2],
        'metallic': 0.5,
        'roughness': 0.3,
        'baseColorTexture': 'textures/diffuse.png',
        'normalMap': 'textures/normal.png'
    }
)

# Save stage
stage.Save()
```

---

## Best Practices

1. **Use MaterialX for Production**: MaterialX Standard Surface provides the best compatibility with MaterialX renderers
2. **Check MaterialX Availability**: Verify MaterialX plugin is loaded before using MaterialX shaders
3. **Use Auto-Detection**: Set `material_shader_type="auto"` to automatically use MaterialX when available
4. **Validate Materials**: Enable `validate_materials=True` to ensure MaterialX compatibility

---

## References

- **MaterialX Official Website**: https://materialx.org/
- **MaterialX GitHub**: https://github.com/AcademySoftwareFoundation/MaterialX
- **MaterialX Specification**: https://materialx.org/docs/api/standard_surface.html
- **Houdini/Nuke/Blender Compatibility**: See `docs/HOUDINI_NUKE_COMPATIBILITY.md`
- **Best Practices**: See `docs/BEST_MATERIAL_PRACTICES.md`

---

*Last Updated: After MaterialX clarification*
