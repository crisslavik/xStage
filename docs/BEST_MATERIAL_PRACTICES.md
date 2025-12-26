# Best Material Shader Practices for xStage
## Recommended Approach for VFX Pipelines

---

## 🎯 **Recommended Strategy: Smart Material System**

### **Best Choice: XMaterial with Smart Fallback**

For a production VFX pipeline, the **best approach** is:

1. **Primary: XMaterial (MaterialX-based)**
   - Industry standard for VFX pipelines
   - Maximum interoperability
   - Future-proof
   - Works with MaterialX-compatible renderers (Arnold, RenderMan, V-Ray, etc.)

2. **Fallback: UsdPreviewSurface**
   - Universal compatibility
   - Works everywhere USD works
   - Good for preview/viewing

3. **Auto-Detection**
   - Automatically use XMaterial if MaterialX available
   - Fallback to UsdPreviewSurface if not
   - No manual configuration needed

---

## 📊 Comparison Matrix

| Shader Type | Interoperability | Renderer Support | Complexity | Best For |
|------------|------------------|------------------|------------|----------|
| **XMaterial** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium | Production pipelines |
| **MaterialX** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium | Advanced workflows |
| **UsdPreviewSurface** | ⭐⭐⭐⭐ | ⭐⭐⭐ | Low | Universal compatibility |
| **glTF_PBR** | ⭐⭐⭐ | ⭐⭐⭐ | Low | Web/real-time |

---

## 🚀 **Recommended Implementation**

### **Option 1: Smart Auto-Detection (BEST)**

Automatically choose the best shader type based on availability:

```python
from xstage import USDConverter, ConversionOptions

# Smart mode: Auto-detect best shader
options = ConversionOptions(
    material_shader_type="auto",  # NEW: Auto-detect
    export_materials=True
)
converter = USDConverter(options)
converter.convert("model.fbx", "model.usd")
```

**Behavior:**
- If MaterialX available → Use XMaterial
- If MaterialX not available → Use UsdPreviewSurface
- No manual configuration needed

### **Option 2: Explicit XMaterial (RECOMMENDED for Production)**

Explicitly use XMaterial for production workflows:

```python
options = ConversionOptions(
    material_shader_type="XMaterial",
    export_materials=True
)
```

**Benefits:**
- Consistent material output
- Production-ready
- MaterialX compatibility

### **Option 3: Format-Specific (ADVANCED)**

Use different shaders based on source format:

```python
# FBX → XMaterial (production assets)
# OBJ → UsdPreviewSurface (quick previews)
# glTF → glTF_PBR (web assets)
```

---

## 💡 **Best Practices**

### 1. **Material Extraction Priority**

**Best approach**: Extract materials from source, then convert to target shader

```
Source Format → Extract Material Data → Convert to XMaterial → USD
```

**Implementation:**
- Extract all material properties from source
- Normalize to standard format
- Create XMaterial shader with extracted data
- Preserve texture paths and relationships

### 2. **Texture Handling**

**Best approach**: Preserve relative paths, support multiple texture types

```python
# Good: Relative paths
material_data = {
    'baseColorTexture': 'textures/diffuse.png',
    'normalMap': 'textures/normal.png'
}

# Better: Asset paths
material_data = {
    'baseColorTexture': '@/assets/textures/diffuse.png',
    'normalMap': '@/assets/textures/normal.png'
}
```

### 3. **Material Naming**

**Best approach**: Use descriptive, hierarchical names

```python
# Good
/Materials/Character/Skin
/Materials/Character/Cloth
/Materials/Props/Metal

# Avoid
/Materials/Material1
/Materials/Material2
```

### 4. **Material Binding**

**Best approach**: Use collection-based binding for efficiency

```python
# Bind to specific prims
material_creator.bind_material_to_prim(material, mesh_prim)

# Or use collections for multiple prims
collection = UsdCollectionAPI.Define(stage, "/Collections/Character")
# Bind material to collection
```

---

## 🔧 **Recommended Configuration**

### **For Production Pipelines**

```python
from xstage import USDConverter, ConversionOptions

# Production settings
options = ConversionOptions(
    # Material settings
    export_materials=True,
    material_shader_type="XMaterial",  # Use XMaterial
    
    # Geometry settings
    export_normals=True,
    export_uvs=True,
    export_colors=True,
    
    # Pipeline settings
    preserve_hierarchy=True,
    time_samples=True,
    
    # Scale/axis
    scale=1.0,
    up_axis='Y',
)

converter = USDConverter(options)
```

### **For Quick Previews**

```python
# Quick preview settings
options = ConversionOptions(
    export_materials=True,
    material_shader_type="UsdPreviewSurface",  # Faster, universal
    export_normals=True,
    export_uvs=True,
    preserve_hierarchy=False,  # Flatten for speed
)
```

---

## 🎨 **Enhanced Material Extraction**

### **What to Extract from Each Format**

#### **FBX**
```python
{
    'baseColor': fbx_material.DiffuseColor,
    'metallic': fbx_material.ReflectionFactor,
    'roughness': 1.0 - fbx_material.Shininess,
    'emissiveColor': fbx_material.EmissiveColor,
    'opacity': fbx_material.TransparencyFactor,
    'diffuseTexture': fbx_material.Diffuse.GetFileName(),
    'normalMap': fbx_material.Bump.GetFileName(),
}
```

#### **glTF**
```python
{
    'baseColor': pbr.baseColorFactor,
    'metallic': pbr.metallicFactor,
    'roughness': pbr.roughnessFactor,
    'baseColorTexture': pbr.baseColorTexture.index,
    'metallicRoughnessTexture': pbr.metallicRoughnessTexture.index,
    'normalTexture': material.normalTexture.index,
    'emissiveTexture': material.emissiveTexture.index,
}
```

#### **OBJ (MTL)**
```python
{
    'baseColor': mtl.Kd,
    'specular': mtl.Ks,
    'roughness': 1.0 - mtl.Ns / 1000.0,
    'diffuseTexture': mtl.map_Kd,
    'normalMap': mtl.map_Bump,
    'specularTexture': mtl.map_Ks,
}
```

---

## 🚀 **Implementation Recommendations**

### **1. Smart Auto-Detection (RECOMMENDED)**

Add auto-detection to MaterialCreator:

```python
class MaterialCreator:
    def __init__(self, shader_type: str = "auto"):
        if shader_type == "auto":
            # Auto-detect best available
            if MATERIALX_AVAILABLE:
                self.shader_type = MaterialShaderType.XMATERIAL
            else:
                self.shader_type = MaterialShaderType.PREVIEW_SURFACE
        else:
            self.shader_type = shader_type
```

### **2. Enhanced Material Extraction**

Improve extraction from source formats:

```python
def extract_material_from_source(source_data: Dict, source_format: str) -> Dict:
    """Enhanced extraction with format-specific logic"""
    
    material_data = {}
    
    if source_format == 'fbx':
        # Enhanced FBX extraction
        material_data = _extract_fbx_material(source_data)
    elif source_format == 'gltf':
        # Enhanced glTF extraction
        material_data = _extract_gltf_material(source_data)
    # ... etc
    
    return material_data
```

### **3. Texture Path Resolution**

Handle texture paths intelligently:

```python
def resolve_texture_path(texture_path: str, source_file: str) -> str:
    """Resolve texture path relative to source file"""
    if os.path.isabs(texture_path):
        return texture_path
    
    # Make relative to source file
    source_dir = os.path.dirname(source_file)
    resolved = os.path.join(source_dir, texture_path)
    
    if os.path.exists(resolved):
        # Make relative to USD output
        return os.path.relpath(resolved, output_dir)
    
    return texture_path
```

---

## ✅ **Final Recommendation**

### **For Your Pipeline:**

1. **Default to XMaterial** with auto-fallback
2. **Enhanced extraction** from all source formats
3. **Smart texture path** resolution
4. **Collection-based binding** for efficiency
5. **Preserve material hierarchy** in USD

### **Implementation Priority:**

1. ✅ **Add auto-detection** to MaterialCreator
2. ✅ **Enhance material extraction** from FBX, glTF, OBJ
3. ✅ **Improve texture path handling**
4. ✅ **Add material validation**
5. ✅ **Support material collections**

---

## 📝 **Quick Start**

```python
# Best practice: Use auto-detection
from xstage import USDConverter, ConversionOptions

options = ConversionOptions(
    material_shader_type="auto",  # Smart choice
    export_materials=True
)

converter = USDConverter(options)
converter.convert("model.fbx", "model.usd")
```

This will:
- ✅ Use XMaterial if MaterialX available
- ✅ Fallback to UsdPreviewSurface if not
- ✅ Extract materials from source
- ✅ Create proper material bindings
- ✅ Handle texture paths correctly

---

## 🎯 **Summary**

**Best Choice**: **XMaterial with auto-fallback**

**Why:**
- Industry standard (MaterialX)
- Maximum compatibility
- Future-proof
- Production-ready
- Automatic fallback ensures it always works

**Implementation:**
- Add "auto" mode to MaterialCreator
- Enhance material extraction
- Improve texture handling
- Add validation

This gives you the best of both worlds: production-quality materials when available, universal compatibility as fallback.

