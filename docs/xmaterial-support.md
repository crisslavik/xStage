# XMaterial/MaterialX Shader Support
## Material Creation During Format Conversion

xStage now supports creating USD materials with various shader types during format conversion, including **XMaterial** (MaterialX-based) shaders.

---

## Supported Shader Types

### 1. **UsdPreviewSurface** (Default)
Standard USD shader for basic PBR materials.

### 2. **MaterialX**
MaterialX shader for advanced material workflows.

### 3. **XMaterial** ⭐
Custom MaterialX-based shader schema. This is the recommended shader type for production pipelines using MaterialX.

### 4. **glTF_PBR**
glTF PBR material shader (uses UsdPreviewSurface with glTF conventions).

---

## Usage

### Command Line

```bash
# Convert with XMaterial shader
xstage model.fbx --export output.usd --material-shader XMaterial

# Convert with MaterialX shader
xstage model.fbx --export output.usd --material-shader MaterialX

# Convert with UsdPreviewSurface (default)
xstage model.fbx --export output.usd --material-shader UsdPreviewSurface
```

### Python API

```python
from xstage import USDConverter, ConversionOptions, MaterialShaderType

# Create converter with XMaterial shader
options = ConversionOptions(
    material_shader_type="XMaterial",
    export_materials=True
)
converter = USDConverter(options)

# Convert file
converter.convert("model.fbx", "model.usd")
```

### Using MaterialCreator Directly

```python
from xstage.converters.material_creator import MaterialCreator, MaterialShaderType

# Create XMaterial shader
creator = MaterialCreator(shader_type=MaterialShaderType.XMATERIAL)

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

## XMaterial Shader Details

XMaterial is a MaterialX-based shader that provides:

- **Advanced Material Support**: Full MaterialX node graph support
- **Production-Ready**: Used in professional VFX pipelines
- **Interoperability**: Works with MaterialX-compatible renderers
- **Node Graph**: Supports complex material networks

### XMaterial Shader ID
- Shader ID: `ND_XMaterial_surface`
- Based on MaterialX standard surface shader
- Compatible with MaterialX renderers

---

## Requirements

### For MaterialX/XMaterial Support

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
- `emissiveTexture`: Emissive texture

---

## Examples

### Example 1: Convert FBX with XMaterial

```python
from xstage import USDConverter, ConversionOptions

options = ConversionOptions(
    material_shader_type="XMaterial",
    export_materials=True
)
converter = USDConverter(options)
converter.convert("character.fbx", "character.usd")
```

### Example 2: Create Custom Material

```python
from xstage.converters.material_creator import MaterialCreator, MaterialShaderType

creator = MaterialCreator(shader_type=MaterialShaderType.XMATERIAL)

material_data = {
    'baseColor': [0.8, 0.2, 0.2],  # Red
    'metallic': 0.8,
    'roughness': 0.2,
    'baseColorTexture': '/path/to/texture.png'
}

material = creator.create_material(stage, "/Materials/RedMetal", material_data)
```

### Example 3: Extract Material from Source

```python
from xstage.converters.material_creator import MaterialCreator

# Extract material from FBX
fbx_material = {
    'DiffuseColor': [0.5, 0.5, 0.5],
    'ReflectionFactor': 0.5,
    'Shininess': 0.8
}

# Convert to standard format
standard_material = MaterialCreator.extract_material_from_source(
    fbx_material, 'fbx'
)
# Result: {'baseColor': [0.5, 0.5, 0.5], 'metallic': 0.5, 'roughness': 0.2}
```

---

## Integration with Converter

The material creator is automatically integrated into all format converters:

- **FBX**: Extracts materials and creates XMaterial shaders
- **OBJ**: Extracts MTL materials and creates shaders
- **glTF**: Extracts PBR materials and creates shaders
- **Alembic**: Preserves material assignments
- **STL/PLY**: Creates default materials if needed

---

## Best Practices

1. **Use XMaterial for Production**: XMaterial provides the best compatibility with MaterialX renderers
2. **Check MaterialX Availability**: Verify MaterialX plugin is loaded before using XMaterial
3. **Fallback Handling**: Always handle fallback to UsdPreviewSurface if MaterialX unavailable
4. **Texture Paths**: Ensure texture paths are relative or use asset paths
5. **Material Naming**: Use descriptive material names for better organization

---

## Troubleshooting

### MaterialX Not Available

If you see "MaterialX not available, falling back to UsdPreviewSurface":
- Install MaterialX plugin
- Check USD installation includes MaterialX
- Verify `UsdMtlx` module is importable

### Materials Not Appearing

- Check `export_materials=True` in ConversionOptions
- Verify source format has material data
- Check material binding to prims

### Texture Not Loading

- Verify texture paths are correct
- Use relative paths or asset paths
- Check texture file exists

---

## References

- [MaterialX Documentation](https://materialx.org/)
- [USD MaterialX Integration](https://openusd.org/release/api/usd_mtlx_page_front.html)
- [UsdShade Documentation](https://openusd.org/release/api/usd_shade_page_front.html)

