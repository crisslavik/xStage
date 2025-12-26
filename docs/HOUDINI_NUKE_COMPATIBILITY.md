# Houdini Karma, Nuke 17 & Blender Material Compatibility
## Enhanced Material Support for Production Pipelines

xStage now includes enhanced material support specifically optimized for **Houdini Karma**, **Nuke 17**, and **Blender** (beta/future-proof) compatibility.

---

## 🎯 **Houdini Karma Support**

### **Karma MaterialX Integration**

Houdini Karma (CPU/XPU) uses MaterialX Standard Surface shaders through the Solaris framework. xStage creates materials that are fully compatible with Karma.

### **Usage**

```python
from xstage import USDConverter, ConversionOptions

# Create converter optimized for Houdini Karma
options = ConversionOptions(
    material_shader_type="Karma",  # Houdini Karma-optimized
    export_materials=True,
    validate_materials=True  # Validate for Karma compatibility
)

converter = USDConverter(options)
converter.convert("model.fbx", "model.usd")
```

### **Features**

- ✅ MaterialX Standard Surface shader (`ND_standard_surface_surfaceshader`)
- ✅ Full PBR material support (baseColor, metallic, roughness, specular)
- ✅ Texture support with proper UV mapping
- ✅ Normal maps with MaterialX normalmap node
- ✅ Subsurface scattering support
- ✅ Emission support
- ✅ Displacement support
- ✅ Houdini metadata for better integration

### **Material Properties Supported**

```python
material_data = {
    # Base properties
    'baseColor': [0.8, 0.2, 0.2],
    'metallic': 0.5,
    'roughness': 0.3,
    'specular': 0.5,
    'specularColor': [1.0, 1.0, 1.0],
    
    # Textures
    'baseColorTexture': 'textures/diffuse.png',
    'metallicTexture': 'textures/metallic.png',
    'roughnessTexture': 'textures/roughness.png',
    'normalMap': 'textures/normal.png',
    
    # Advanced
    'emissiveColor': [1.0, 0.5, 0.0],
    'subsurface': 0.2,
    'subsurfaceColor': [0.8, 0.2, 0.2],
    'transmission': 0.0,
    'opacity': 1.0,
    
    # Displacement
    'displacement': {
        'height': 'textures/displacement.exr',
        'scale': 0.1
    }
}
```

---

## 🎨 **Blender Support** (Beta/Future-Proof)

### **Blender MaterialX Integration**

Blender has been adding USD and MaterialX support (currently in beta/development). xStage creates materials that will be compatible with Blender's MaterialX implementation as it matures.

### **Usage**

```python
from xstage import USDConverter, ConversionOptions

# Create converter optimized for Blender
options = ConversionOptions(
    material_shader_type="Blender",  # Blender-optimized MaterialX
    export_materials=True,
    validate_materials=True  # Validate for Blender compatibility
)

converter = USDConverter(options)
converter.convert("model.fbx", "model.usd")
```

### **Features**

- ✅ MaterialX Standard Surface shader (`ND_standard_surface_surfaceshader`)
- ✅ Full PBR material support (baseColor, metallic, roughness, specular)
- ✅ Texture support with proper UV mapping
- ✅ Normal maps with MaterialX normalmap node
- ✅ Subsurface scattering support
- ✅ Emission support
- ✅ Displacement support
- ✅ Blender metadata for better integration (future-proof)

### **Blender-Specific Features**

- Materials compatible with Blender's USD import/export
- MaterialX Standard Surface for future Blender MaterialX support
- Blender metadata tags for identification
- Ready for Blender's MaterialX implementation when available

### **Status**

**Current**: Blender USD support is available, MaterialX support is in development  
**Future**: Full MaterialX Standard Surface support expected in future Blender releases  
**xStage**: Materials are created with Blender-compatible structure and metadata

---

## 🎬 **Nuke 17 Support**

### **Nuke MaterialX Integration**

Nuke 17.0 introduced MaterialX support with the `MtlXStandardSurface` node. xStage creates materials that work seamlessly with Nuke's MaterialX implementation.

### **Usage**

```python
from xstage import USDConverter, ConversionOptions

# Create converter optimized for Nuke 17
options = ConversionOptions(
    material_shader_type="Nuke",  # Nuke 17-optimized
    export_materials=True,
    validate_materials=True  # Validate for Nuke compatibility
)

converter = USDConverter(options)
converter.convert("model.fbx", "model.usd")
```

### **Features**

- ✅ MaterialX Standard Surface shader
- ✅ Compatible with Nuke's MtlXStandardSurface node
- ✅ Hydra viewer preview support
- ✅ ScanlineRender2 renderer compatibility
- ✅ Accurate material representation for compositing
- ✅ Nuke metadata for better integration

### **Nuke-Specific Features**

- Materials can be previewed in Nuke's Hydra viewer
- Renders correctly with ScanlineRender2
- Maintains material properties through compositing pipeline
- Reduces need for round-tripping between applications

---

## 🔧 **Enhanced Material Extraction**

### **FBX Materials**

Enhanced extraction from FBX files:

```python
# Automatically extracts:
- DiffuseColor → baseColor
- ReflectionFactor → metallic
- Shininess → roughness
- SpecularFactor → specular
- NormalMap/Bump → normalMap
- Emissive → emissiveColor
- TransparencyFactor → opacity
- SubsurfaceColor → subsurfaceColor
```

### **glTF Materials**

Full glTF PBR material support:

```python
# Extracts:
- pbrMetallicRoughness → baseColor, metallic, roughness
- normalTexture → normalMap
- emissiveTexture → emissiveTexture
- occlusionTexture → occlusionTexture
```

### **OBJ Materials (MTL)**

Complete MTL file support:

```python
# Extracts:
- Kd → baseColor
- Ks → specular
- Ns → roughness
- map_Kd → diffuseTexture
- map_Bump → normalMap
- map_Ks → specularTexture
```

---

## ✅ **Material Validation**

xStage includes material validation to ensure compatibility:

```python
from xstage.converters.material_validator import MaterialValidator

# Validate for Karma
validator = MaterialValidator(target="karma")
issues = validator.validate_material(material)

# Validate for Nuke
validator = MaterialValidator(target="nuke")
issues = validator.validate_material(material)

# Validate for Blender
validator = MaterialValidator(target="blender")
issues = validator.validate_material(material)

# Auto-detect target
validator = MaterialValidator(target="auto")
issues = validator.validate_material(material)
```

### **Validation Checks**

- ✅ Surface output connection
- ✅ Shader ID compatibility
- ✅ Required material properties
- ✅ Texture path validity
- ✅ MaterialX node graph structure
- ✅ Houdini/Nuke/Blender metadata

---

## 🚀 **Best Practices**

### **For Houdini Karma**

1. **Use "Karma" shader type**:
   ```python
   options = ConversionOptions(material_shader_type="Karma")
   ```

2. **Enable material validation**:
   ```python
   options = ConversionOptions(validate_materials=True)
   ```

3. **Use MaterialX Standard Surface properties**:
   - `baseColor` (not `diffuseColor`)
   - `metallic` and `roughness` (PBR workflow)
   - `specular` and `specularColor`

4. **Texture paths**: Use relative paths or asset paths

### **For Nuke 17**

1. **Use "Nuke" shader type**:
   ```python
   options = ConversionOptions(material_shader_type="Nuke")
   ```

2. **Test in Hydra viewer**: Preview materials in Nuke's Hydra viewer

3. **Render with ScanlineRender2**: Materials render correctly with Nuke's renderer

4. **Maintain material hierarchy**: Keep materials organized for compositing

---

## 📊 **Comparison**

| Feature | Houdini Karma | Nuke 17 | Blender | xStage Support |
|---------|---------------|---------|---------|----------------|
| MaterialX Standard Surface | ✅ | ✅ | 🔄 Beta | ✅ |
| PBR Materials | ✅ | ✅ | ✅ | ✅ |
| Texture Support | ✅ | ✅ | ✅ | ✅ |
| Normal Maps | ✅ | ✅ | ✅ | ✅ |
| Subsurface Scattering | ✅ | ✅ | ✅ | ✅ |
| Displacement | ✅ | ⚠️ | 🔄 Beta | ✅ |
| Emission | ✅ | ✅ | ✅ | ✅ |
| Hydra Preview | ✅ | ✅ | 🔄 Beta | ✅ |
| USD Import/Export | ✅ | ✅ | ✅ | ✅ |

**Legend**: ✅ Full Support | ⚠️ Limited | 🔄 Beta/In Development

---

## 🎨 **Example Workflow**

### **Convert FBX for Houdini**

```python
from xstage import USDConverter, ConversionOptions

# Convert with Karma-optimized materials
options = ConversionOptions(
    material_shader_type="Karma",
    export_materials=True,
    validate_materials=True
)

converter = USDConverter(options)
converter.convert("character.fbx", "character_karma.usd")

# Open in Houdini Solaris
# Materials will render correctly in Karma
```

### **Convert for Nuke Compositing**

```python
# Convert with Nuke-optimized materials
options = ConversionOptions(
    material_shader_type="Nuke",
    export_materials=True,
    validate_materials=True
)

converter = USDConverter(options)
converter.convert("scene.fbx", "scene_nuke.usd")

# Import in Nuke 17
# Materials work with MtlXStandardSurface node
# Preview in Hydra viewer
# Render with ScanlineRender2
```

### **Convert for Blender**

```python
# Convert with Blender-optimized materials (future-proof)
options = ConversionOptions(
    material_shader_type="Blender",
    export_materials=True,
    validate_materials=True
)

converter = USDConverter(options)
converter.convert("model.fbx", "model_blender.usd")

# Import in Blender (current USD support)
# Materials ready for MaterialX when available
# Future-proof structure for Blender MaterialX implementation
```

---

## 🔍 **Troubleshooting**

### **Materials not rendering in Karma**

1. Check shader ID: Should be `ND_standard_surface_surfaceshader`
2. Verify MaterialX plugin is loaded in Houdini
3. Check material validation results
4. Ensure texture paths are correct

### **Materials not showing in Nuke**

1. Verify Nuke 17.0+ is being used
2. Check MaterialX plugin is available
3. Use Hydra viewer for preview
4. Verify material validation passes

### **Materials not working in Blender**

1. Verify Blender version supports USD (3.0+)
2. Check MaterialX support status (currently beta/development)
3. Materials use standard MaterialX structure (future-proof)
4. USD import should work, MaterialX rendering depends on Blender version

### **Texture not loading**

1. Check texture paths are relative or asset paths
2. Verify texture files exist
3. Check UV coordinates are properly set
4. Validate texture shader connections

---

## 📚 **References**

- [Houdini Karma MaterialX](https://www.sidefx.com/docs/houdini/solaris/karma.html)
- [Nuke 17 MaterialX](https://learn.foundry.com/nuke/17.0/content/user_guide/3d_environment/materialx.html)
- [MaterialX Standard Surface](https://materialx.org/docs/api/standard_surface.html)

---

## ✅ **Summary**

xStage now provides:

- ✅ **Houdini Karma** optimized materials
- ✅ **Nuke 17** compatible materials
- ✅ **Blender** compatible materials (beta/future-proof)
- ✅ Enhanced material extraction from all formats
- ✅ Material validation for compatibility
- ✅ Full MaterialX Standard Surface support
- ✅ Advanced material properties (subsurface, displacement, emission)
- ✅ Production-ready material workflows

Your materials will work seamlessly in Houdini Karma, Nuke 17, and Blender! 🎬

