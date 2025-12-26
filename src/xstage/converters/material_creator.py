"""
Material Creator for USD Conversion
Creates USD materials with various shader types including MaterialX Standard Surface
Enhanced for Houdini Karma, Nuke 17, and Blender compatibility

MaterialX is an open standard for representing rich material and look-development content.
See: https://materialx.org/ and https://github.com/AcademySoftwareFoundation/MaterialX
"""

from typing import Optional, Dict, List, Tuple
from pathlib import Path
import os

try:
    from pxr import Usd, UsdShade, Gf, Sdf, Tf, Vt
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False

try:
    from pxr import UsdMtlx
    MATERIALX_AVAILABLE = True
except ImportError:
    MATERIALX_AVAILABLE = False


class MaterialShaderType:
    """Material shader types"""
    PREVIEW_SURFACE = "UsdPreviewSurface"  # Standard USD shader
    MATERIALX = "MaterialX"  # MaterialX shader
    XMATERIAL = "XMaterial"  # Alias for MaterialX Standard Surface (for backward compatibility)
    GLTF_PBR = "glTF_PBR"  # glTF PBR shader
    KARMA = "Karma"  # Houdini Karma-optimized MaterialX
    NUKE = "Nuke"  # Nuke 17 MaterialX Standard Surface
    BLENDER = "Blender"  # Blender MaterialX Standard Surface (beta/future-proof)


class MaterialCreator:
    """Creates USD materials with various shader types"""
    
    def __init__(self, shader_type: str = "auto"):
        """
        Initialize material creator
        
        Args:
            shader_type: Type of shader to create:
                - "auto" (RECOMMENDED): Auto-detect best available (MaterialX if available, else UsdPreviewSurface)
                - "MaterialX": MaterialX Standard Surface shader (best for production)
                - "XMaterial": Alias for MaterialX (for backward compatibility)
                - "Karma": Houdini Karma-optimized MaterialX
                - "Nuke": Nuke 17 MaterialX Standard Surface
                - "Blender": Blender MaterialX Standard Surface (beta/future-proof)
                - "MaterialX": Standard MaterialX shader
                - "UsdPreviewSurface": Standard USD shader (universal compatibility)
                - "glTF_PBR": glTF PBR shader
        """
        if shader_type == "auto":
            # Smart auto-detection: Use MaterialX if available, else UsdPreviewSurface
            if MATERIALX_AVAILABLE:
                self.shader_type = MaterialShaderType.MATERIALX
            else:
                self.shader_type = MaterialShaderType.PREVIEW_SURFACE
        else:
            self.shader_type = shader_type
    
    def create_material(self, stage: Usd.Stage, material_path: str, 
                       material_data: Optional[Dict] = None) -> Optional[UsdShade.Material]:
        """
        Create a USD material with the specified shader type
        
        Args:
            stage: USD stage
            material_path: Path for the material prim
            material_data: Material properties (baseColor, metallic, roughness, etc.)
        
        Returns:
            Created UsdShade.Material or None
        """
        if not USD_AVAILABLE:
            return None
        
        try:
            # Create material prim
            material = UsdShade.Material.Define(stage, material_path)
            
            # Create shader based on type
            if self.shader_type in [MaterialShaderType.MATERIALX, MaterialShaderType.XMATERIAL, 
                                    MaterialShaderType.KARMA, MaterialShaderType.NUKE, MaterialShaderType.BLENDER]:
                return self._create_materialx_material(material, stage, material_path, material_data)
            elif self.shader_type == MaterialShaderType.GLTF_PBR:
                return self._create_gltf_pbr_material(material, stage, material_path, material_data)
            else:
                # Default to UsdPreviewSurface
                return self._create_preview_surface_material(material, stage, material_path, material_data)
        
        except Exception as e:
            print(f"Error creating material {material_path}: {e}")
            return None
    
    def _create_preview_surface_material(self, material: UsdShade.Material, 
                                        stage: Usd.Stage, material_path: str,
                                        material_data: Optional[Dict]) -> UsdShade.Material:
        """Create material with UsdPreviewSurface shader"""
        # Create shader prim
        shader_path = f"{material_path}/PreviewSurface"
        shader = UsdShade.Shader.Define(stage, shader_path)
        shader.CreateIdAttr("UsdPreviewSurface")
        
        # Set default values
        material_data = material_data or {}
        
        # Base color
        base_color = material_data.get('baseColor', [0.18, 0.18, 0.18])
        if isinstance(base_color, (list, tuple)) and len(base_color) >= 3:
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
                Gf.Vec3f(base_color[0], base_color[1], base_color[2])
            )
        
        # Metallic
        metallic = material_data.get('metallic', 0.0)
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metallic))
        
        # Roughness
        roughness = material_data.get('roughness', 0.5)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(roughness))
        
        # Emissive color
        if 'emissiveColor' in material_data:
            emissive = material_data['emissiveColor']
            if isinstance(emissive, (list, tuple)) and len(emissive) >= 3:
                shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(
                    Gf.Vec3f(emissive[0], emissive[1], emissive[2])
                )
        
        # Opacity
        if 'opacity' in material_data:
            shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(float(material_data['opacity']))
        
        # Normal map
        if 'normalMap' in material_data:
            normal_map_path = material_data['normalMap']
            normal_shader = self._create_texture_shader(stage, f"{shader_path}/normalMap", normal_map_path)
            if normal_shader:
                shader.CreateInput("normal", Sdf.ValueTypeNames.Normal3f).ConnectToSource(
                    normal_shader.ConnectableAPI(), "rgb"
                )
        
        # Diffuse texture
        if 'diffuseTexture' in material_data:
            diffuse_tex_path = material_data['diffuseTexture']
            diffuse_shader = self._create_texture_shader(stage, f"{shader_path}/diffuseTexture", diffuse_tex_path)
            if diffuse_shader:
                shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
                    diffuse_shader.ConnectableAPI(), "rgb"
                )
        
        # Connect shader to material
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        
        return material
    
    def _create_materialx_material(self, material: UsdShade.Material,
                                  stage: Usd.Stage, material_path: str,
                                  material_data: Optional[Dict]) -> UsdShade.Material:
        """Create material with MaterialX Standard Surface shader - Enhanced for Houdini Karma, Nuke 17, and Blender"""
        if not MATERIALX_AVAILABLE:
            # Fallback to PreviewSurface if MaterialX not available
            print("MaterialX not available, falling back to UsdPreviewSurface")
            return self._create_preview_surface_material(material, stage, material_path, material_data)
        
        try:
            material_data = material_data or {}
            
            # Determine shader ID based on target
            if self.shader_type == MaterialShaderType.KARMA:
                # Houdini Karma uses MaterialX Standard Surface
                shader_id = "ND_standard_surface_surfaceshader"
                shader_name = "KarmaSurface"
            elif self.shader_type == MaterialShaderType.NUKE:
                # Nuke 17 uses MaterialX Standard Surface
                shader_id = "ND_standard_surface_surfaceshader"
                shader_name = "NukeSurface"
            elif self.shader_type == MaterialShaderType.BLENDER:
                # Blender uses MaterialX Standard Surface (beta/future-proof)
                shader_id = "ND_standard_surface_surfaceshader"
                shader_name = "BlenderSurface"
            elif self.shader_type == MaterialShaderType.XMATERIAL:
                # XMaterial is an alias for MaterialX Standard Surface
                shader_id = "ND_standard_surface_surfaceshader"  # MaterialX Standard Surface
                shader_name = "MaterialXSurface"  # Use MaterialX naming
            else:
                # Standard MaterialX
                shader_id = "ND_standard_surface_surfaceshader"
                shader_name = "MaterialXSurface"
            
            # Create MaterialX shader
            shader_path = f"{material_path}/{shader_name}"
            shader = UsdShade.Shader.Define(stage, shader_path)
            shader.CreateIdAttr(shader_id)
            
            # MaterialX Standard Surface properties (compatible with Karma and Nuke)
            # Base color
            base_color = material_data.get('baseColor', material_data.get('diffuseColor', [0.18, 0.18, 0.18]))
            if isinstance(base_color, (list, tuple)) and len(base_color) >= 3:
                base_color_input = shader.CreateInput("base_color", Sdf.ValueTypeNames.Color3f)
                base_color_input.Set(Gf.Vec3f(base_color[0], base_color[1], base_color[2]))
            
            # Base color texture
            if 'baseColorTexture' in material_data or 'diffuseTexture' in material_data:
                tex_path = material_data.get('baseColorTexture') or material_data.get('diffuseTexture')
                tex_shader = self._create_materialx_texture(stage, f"{shader_path}/baseColorTex", tex_path)
                if tex_shader:
                    shader.CreateInput("base_color", Sdf.ValueTypeNames.Color3f).ConnectToSource(
                        tex_shader.ConnectableAPI(), "out"
                    )
            
            # Metallic
            metallic = material_data.get('metallic', 0.0)
            shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metallic))
            
            # Metallic texture
            if 'metallicTexture' in material_data:
                tex_shader = self._create_materialx_texture(stage, f"{shader_path}/metallicTex", 
                                                            material_data['metallicTexture'])
                if tex_shader:
                    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).ConnectToSource(
                        tex_shader.ConnectableAPI(), "out"
                    )
            
            # Roughness
            roughness = material_data.get('roughness', 0.5)
            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(roughness))
            
            # Roughness texture
            if 'roughnessTexture' in material_data:
                tex_shader = self._create_materialx_texture(stage, f"{shader_path}/roughnessTex", 
                                                            material_data['roughnessTexture'])
                if tex_shader:
                    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).ConnectToSource(
                        tex_shader.ConnectableAPI(), "out"
                    )
            
            # Specular (MaterialX Standard Surface)
            specular = material_data.get('specular', 0.5)
            shader.CreateInput("specular", Sdf.ValueTypeNames.Float).Set(float(specular))
            
            # Specular color
            specular_color = material_data.get('specularColor', [1.0, 1.0, 1.0])
            if isinstance(specular_color, (list, tuple)) and len(specular_color) >= 3:
                shader.CreateInput("specular_color", Sdf.ValueTypeNames.Color3f).Set(
                    Gf.Vec3f(specular_color[0], specular_color[1], specular_color[2])
                )
            
            # Normal map
            if 'normalMap' in material_data or 'normalTexture' in material_data:
                normal_path = material_data.get('normalMap') or material_data.get('normalTexture')
                normal_shader = self._create_materialx_normalmap(stage, f"{shader_path}/normalMap", normal_path)
                if normal_shader:
                    shader.CreateInput("normal", Sdf.ValueTypeNames.Vector3f).ConnectToSource(
                        normal_shader.ConnectableAPI(), "out"
                    )
            
            # Emission
            if 'emissiveColor' in material_data or 'emission' in material_data:
                emissive = material_data.get('emissiveColor') or material_data.get('emission', [0.0, 0.0, 0.0])
                if isinstance(emissive, (list, tuple)) and len(emissive) >= 3:
                    shader.CreateInput("emission", Sdf.ValueTypeNames.Color3f).Set(
                        Gf.Vec3f(emissive[0], emissive[1], emissive[2])
                    )
            
            # Emission texture
            if 'emissiveTexture' in material_data:
                tex_shader = self._create_materialx_texture(stage, f"{shader_path}/emissionTex", 
                                                           material_data['emissiveTexture'])
                if tex_shader:
                    shader.CreateInput("emission", Sdf.ValueTypeNames.Color3f).ConnectToSource(
                        tex_shader.ConnectableAPI(), "out"
                    )
            
            # Subsurface scattering (for advanced materials)
            if 'subsurface' in material_data:
                subsurface = material_data.get('subsurface', 0.0)
                shader.CreateInput("subsurface", Sdf.ValueTypeNames.Float).Set(float(subsurface))
            
            if 'subsurfaceColor' in material_data:
                subsurface_color = material_data['subsurfaceColor']
                if isinstance(subsurface_color, (list, tuple)) and len(subsurface_color) >= 3:
                    shader.CreateInput("subsurface_color", Sdf.ValueTypeNames.Color3f).Set(
                        Gf.Vec3f(subsurface_color[0], subsurface_color[1], subsurface_color[2])
                    )
            
            # Opacity/Transmission
            if 'opacity' in material_data:
                opacity = material_data.get('opacity', 1.0)
                shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(float(opacity))
            
            if 'transmission' in material_data:
                transmission = material_data.get('transmission', 0.0)
                shader.CreateInput("transmission", Sdf.ValueTypeNames.Float).Set(float(transmission))
            
            # Displacement (for advanced workflows)
            if 'displacement' in material_data:
                displacement_shader = self._create_materialx_displacement(
                    stage, f"{shader_path}/displacement", material_data['displacement']
                )
                if displacement_shader:
                    material.CreateDisplacementOutput().ConnectToSource(
                        displacement_shader.ConnectableAPI(), "out"
                    )
            
            # Connect to material output
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "out")
            
            # Add metadata for Houdini/Nuke/Blender compatibility
            if self.shader_type == MaterialShaderType.KARMA:
                material.GetPrim().SetMetadata("houdini:material", "karma")
            elif self.shader_type == MaterialShaderType.NUKE:
                material.GetPrim().SetMetadata("nuke:material", "mtlx_standard_surface")
            elif self.shader_type == MaterialShaderType.BLENDER:
                material.GetPrim().SetMetadata("blender:material", "mtlx_standard_surface")
                material.GetPrim().SetMetadata("blender:usd_materialx", "true")
            
            return material
        
        except Exception as e:
            print(f"Error creating MaterialX material: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to PreviewSurface
            return self._create_preview_surface_material(material, stage, material_path, material_data)
    
    def _create_materialx_texture(self, stage: Usd.Stage, shader_path: str, 
                                  texture_path: str) -> Optional[UsdShade.Shader]:
        """Create MaterialX image node for texture"""
        if not USD_AVAILABLE or not texture_path:
            return None
        
        try:
            # Create MaterialX image node
            texture_shader = UsdShade.Shader.Define(stage, shader_path)
            texture_shader.CreateIdAttr("ND_image_color3")
            
            # Set file path (resolve relative paths)
            resolved_path = self._resolve_texture_path(texture_path)
            texture_shader.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(resolved_path)
            
            # Set UV coordinates (will be connected from mesh primvar)
            # Create UV reader node
            uv_reader_path = f"{shader_path}_uv"
            uv_reader = UsdShade.Shader.Define(stage, uv_reader_path)
            uv_reader.CreateIdAttr("ND_texcoord_vector2")
            uv_reader.CreateInput("index", Sdf.ValueTypeNames.Integer).Set(0)
            
            # Connect UV to texture
            texture_shader.CreateInput("texcoord", Sdf.ValueTypeNames.Vector2f).ConnectToSource(
                uv_reader.ConnectableAPI(), "out"
            )
            
            return texture_shader
        
        except Exception as e:
            print(f"Error creating MaterialX texture: {e}")
            return None
    
    def _create_materialx_normalmap(self, stage: Usd.Stage, shader_path: str,
                                    normal_path: str) -> Optional[UsdShade.Shader]:
        """Create MaterialX normal map node"""
        if not USD_AVAILABLE or not normal_path:
            return None
        
        try:
            # Create normal map shader
            normal_shader = UsdShade.Shader.Define(stage, shader_path)
            normal_shader.CreateIdAttr("ND_normalmap")
            
            # Create image node for normal texture
            image_path = f"{shader_path}_image"
            image_shader = self._create_materialx_texture(stage, image_path, normal_path)
            
            if image_shader:
                # Connect image to normal map
                normal_shader.CreateInput("in", Sdf.ValueTypeNames.Color3f).ConnectToSource(
                    image_shader.ConnectableAPI(), "out"
                )
            
            # Set normal map scale
            normal_shader.CreateInput("scale", Sdf.ValueTypeNames.Float).Set(1.0)
            
            return normal_shader
        
        except Exception as e:
            print(f"Error creating MaterialX normal map: {e}")
            return None
    
    def _create_materialx_displacement(self, stage: Usd.Stage, shader_path: str,
                                      displacement_data: Dict) -> Optional[UsdShade.Shader]:
        """Create MaterialX displacement node"""
        if not USD_AVAILABLE:
            return None
        
        try:
            displacement_shader = UsdShade.Shader.Define(stage, shader_path)
            displacement_shader.CreateIdAttr("ND_displacement_float")
            
            # Displacement height
            if 'height' in displacement_data:
                if isinstance(displacement_data['height'], str):
                    # Texture path
                    height_shader = self._create_materialx_texture(stage, f"{shader_path}_height", 
                                                                  displacement_data['height'])
                    if height_shader:
                        displacement_shader.CreateInput("in", Sdf.ValueTypeNames.Float).ConnectToSource(
                            height_shader.ConnectableAPI(), "out"
                        )
                else:
                    # Constant value
                    displacement_shader.CreateInput("in", Sdf.ValueTypeNames.Float).Set(
                        float(displacement_data['height'])
                    )
            
            # Displacement scale
            scale = displacement_data.get('scale', 0.1)
            displacement_shader.CreateInput("scale", Sdf.ValueTypeNames.Float).Set(float(scale))
            
            return displacement_shader
        
        except Exception as e:
            print(f"Error creating MaterialX displacement: {e}")
            return None
    
    def _create_gltf_pbr_material(self, material: UsdShade.Material,
                                  stage: Usd.Stage, material_path: str,
                                  material_data: Optional[Dict]) -> UsdShade.Material:
        """Create material with glTF PBR shader"""
        # glTF PBR uses UsdPreviewSurface with specific conventions
        return self._create_preview_surface_material(material, stage, material_path, material_data)
    
    def _create_texture_shader(self, stage: Usd.Stage, shader_path: str, 
                               texture_path: str) -> Optional[UsdShade.Shader]:
        """Create a texture shader for image input"""
        if not USD_AVAILABLE:
            return None
        
        try:
            # Create UsdUVTexture shader
            texture_shader = UsdShade.Shader.Define(stage, shader_path)
            texture_shader.CreateIdAttr("UsdUVTexture")
            
            # Set file path (resolve relative paths)
            resolved_path = self._resolve_texture_path(texture_path)
            texture_shader.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(resolved_path)
            
            # Set st (UV coordinates) - will be connected from mesh primvar
            texture_shader.CreateInput("st", Sdf.ValueTypeNames.Float2).Set(
                Gf.Vec2f(0.0, 0.0)  # Default, should be connected to mesh st primvar
            )
            
            return texture_shader
        
        except Exception as e:
            print(f"Error creating texture shader: {e}")
            return None
    
    def _resolve_texture_path(self, texture_path: str) -> str:
        """Resolve texture path - handle relative and absolute paths"""
        if not texture_path:
            return ""
        
        # If already absolute and exists, return as-is
        if os.path.isabs(texture_path) and os.path.exists(texture_path):
            return texture_path
        
        # Try to resolve relative paths
        # In production, textures are often in asset paths
        # Return as-is for now (USD will handle asset resolution)
        return texture_path
    
    def bind_material_to_prim(self, material: UsdShade.Material, prim: Usd.Prim):
        """Bind material to a prim"""
        if not USD_AVAILABLE:
            return
        
        try:
            binding_api = UsdShade.MaterialBindingAPI(prim)
            binding_api.Bind(material)
        except Exception as e:
            print(f"Error binding material to prim: {e}")
    
    @staticmethod
    def extract_material_from_source(source_data: Dict, source_format: str) -> Dict:
        """
        Extract material data from source format - Enhanced extraction
        
        Args:
            source_data: Material data from source format (FBX, OBJ, glTF, etc.)
            source_format: Source format name
        
        Returns:
            Standardized material data dictionary
        """
        material_data = {}
        
        if source_format.lower() == 'fbx':
            # Enhanced FBX material extraction
            material_data['baseColor'] = source_data.get('DiffuseColor', 
                                                         source_data.get('diffuseColor', [0.18, 0.18, 0.18]))
            material_data['metallic'] = source_data.get('ReflectionFactor', 
                                                        source_data.get('metallic', 0.0))
            material_data['roughness'] = 1.0 - (source_data.get('Shininess', 
                                                                source_data.get('shininess', 0.5)) / 100.0)
            material_data['specular'] = source_data.get('SpecularFactor', 
                                                       source_data.get('specular', 0.5))
            material_data['specularColor'] = source_data.get('SpecularColor', [1.0, 1.0, 1.0])
            
            # Textures
            if 'Diffuse' in source_data:
                material_data['diffuseTexture'] = source_data['Diffuse']
            if 'NormalMap' in source_data or 'Bump' in source_data:
                material_data['normalMap'] = source_data.get('NormalMap') or source_data.get('Bump')
            if 'Emissive' in source_data:
                material_data['emissiveColor'] = source_data['Emissive']
                material_data['emissiveTexture'] = source_data.get('EmissiveTexture')
            
            # Advanced properties
            if 'TransparencyFactor' in source_data:
                material_data['opacity'] = 1.0 - source_data['TransparencyFactor']
            if 'SubsurfaceColor' in source_data:
                material_data['subsurfaceColor'] = source_data['SubsurfaceColor']
                material_data['subsurface'] = source_data.get('SubsurfaceFactor', 0.0)
        
        elif source_format.lower() == 'gltf' or source_format.lower() == 'glb':
            # Enhanced glTF PBR material extraction
            pbr = source_data.get('pbrMetallicRoughness', {})
            
            # Base properties
            if 'baseColorFactor' in pbr:
                material_data['baseColor'] = pbr['baseColorFactor']
            if 'metallicFactor' in pbr:
                material_data['metallic'] = pbr['metallicFactor']
            if 'roughnessFactor' in pbr:
                material_data['roughness'] = pbr['roughnessFactor']
            
            # Textures
            if 'baseColorTexture' in pbr:
                tex_info = pbr['baseColorTexture']
                if isinstance(tex_info, dict) and 'index' in tex_info:
                    material_data['baseColorTexture'] = tex_info['index']
                else:
                    material_data['baseColorTexture'] = tex_info
            
            if 'metallicRoughnessTexture' in pbr:
                material_data['metallicRoughnessTexture'] = pbr['metallicRoughnessTexture']
            
            # Additional glTF properties
            if 'normalTexture' in source_data:
                material_data['normalTexture'] = source_data['normalTexture']
            if 'emissiveTexture' in source_data:
                material_data['emissiveTexture'] = source_data['emissiveTexture']
            if 'emissiveFactor' in source_data:
                material_data['emissiveColor'] = source_data['emissiveFactor']
            if 'occlusionTexture' in source_data:
                material_data['occlusionTexture'] = source_data['occlusionTexture']
        
        elif source_format.lower() == 'obj':
            # Enhanced OBJ material (MTL) extraction
            material_data['baseColor'] = source_data.get('Kd', [0.8, 0.8, 0.8])
            material_data['specular'] = source_data.get('Ks', [0.0, 0.0, 0.0])
            material_data['roughness'] = 1.0 - (source_data.get('Ns', 100.0) / 1000.0)
            
            # Textures
            if 'map_Kd' in source_data:
                material_data['diffuseTexture'] = source_data['map_Kd']
            if 'map_Bump' in source_data or 'bump' in source_data:
                material_data['normalMap'] = source_data.get('map_Bump') or source_data.get('bump')
            if 'map_Ks' in source_data:
                material_data['specularTexture'] = source_data['map_Ks']
            if 'map_Ka' in source_data:
                material_data['ambientTexture'] = source_data['map_Ka']
            
            # Transparency
            if 'd' in source_data:
                material_data['opacity'] = source_data['d']
            if 'Tr' in source_data:
                material_data['opacity'] = 1.0 - source_data['Tr']
        
        else:
            # Generic material extraction with common property names
            material_data['baseColor'] = source_data.get('baseColor', 
                                                         source_data.get('color', 
                                                                        source_data.get('diffuse', [0.18, 0.18, 0.18])))
            material_data['metallic'] = source_data.get('metallic', 0.0)
            material_data['roughness'] = source_data.get('roughness', 0.5)
            material_data['specular'] = source_data.get('specular', 0.5)
            
            # Try to find textures with common names
            for tex_key in ['baseColorTexture', 'diffuseTexture', 'colorTexture', 'albedoTexture']:
                if tex_key in source_data:
                    material_data['baseColorTexture'] = source_data[tex_key]
                    break
        
        return material_data
