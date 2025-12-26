"""
USD Converter - Comprehensive 3D Format Conversion
Supports FBX, OBJ, Alembic, glTF, STL, PLY and more
Pipeline-friendly with progress reporting and error handling
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field

try:
    from pxr import Usd, UsdGeom, Gf, Sdf, UsdShade, UsdUtils
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


@dataclass
class ConversionOptions:
    """Options for USD conversion"""
    up_axis: str = 'Y'  # 'Y' or 'Z'
    meters_per_unit: float = 1.0
    scale: float = 1.0  # Additional scale factor
    flip_y: bool = False
    flip_z: bool = False
    export_materials: bool = True
    material_shader_type: str = "auto"  # "auto" (recommended), "MaterialX", "Karma", "Nuke", "Blender", "XMaterial" (alias), "UsdPreviewSurface", "glTF_PBR"
    validate_materials: bool = True  # Validate materials for target application compatibility
    export_normals: bool = True
    export_uvs: bool = True
    export_colors: bool = True
    time_samples: bool = True
    start_frame: float = 0.0
    end_frame: float = 100.0
    fps: float = 24.0
    default_prim_name: str = 'Root'
    merge_meshes: bool = False
    preserve_hierarchy: bool = True


class USDConverter:
    """Comprehensive USD converter for multiple 3D formats"""
    
    def __init__(self, options: ConversionOptions = None):
        self.options = options or ConversionOptions()
        self.supported_formats = {
            '.fbx': self.convert_fbx,
            '.obj': self.convert_obj,
            '.abc': self.convert_alembic,
            '.gltf': self.convert_gltf,
            '.glb': self.convert_gltf,
            '.stl': self.convert_stl,
            '.ply': self.convert_ply,
            '.dae': self.convert_dae,  # Collada
            '.3ds': self.convert_3ds,
            '.blend': self.convert_blender,
        }
        
        # Initialize material creator with smart defaults
        from .material_creator import MaterialCreator, MaterialShaderType
        # Use "auto" if not specified, or use provided type
        shader_type = self.options.material_shader_type or "auto"
        self.material_creator = MaterialCreator(shader_type=shader_type)
        
        # Initialize material validator if validation enabled
        if self.options.validate_materials:
            from .material_validator import MaterialValidator
            # Determine target from shader type
            if shader_type in ["Karma", "karma"]:
                self.material_validator = MaterialValidator(target="karma")
            elif shader_type in ["Nuke", "nuke"]:
                self.material_validator = MaterialValidator(target="nuke")
            elif shader_type in ["Blender", "blender"]:
                self.material_validator = MaterialValidator(target="blender")
            else:
                self.material_validator = MaterialValidator(target="auto")
        else:
            self.material_validator = None
    
    def convert(self, input_path: str, output_path: str, 
                progress_callback: Optional[Callable] = None) -> bool:
        """
        Convert any supported format to USD
        
        Args:
            input_path: Path to input file
            output_path: Path to output USD file
            progress_callback: Optional callback(progress, message)
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            if progress_callback:
                progress_callback(0, f"Error: Input file not found: {input_path}")
            return False
        
        # Get file extension
        ext = input_path.suffix.lower()
        
        if ext not in self.supported_formats:
            if progress_callback:
                progress_callback(0, f"Error: Unsupported format: {ext}")
            return False
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Call appropriate converter
        converter_func = self.supported_formats[ext]
        return converter_func(str(input_path), str(output_path), progress_callback)
    
    def convert_fbx(self, input_path: str, output_path: str, 
                    progress_callback: Optional[Callable] = None) -> bool:
        """Convert FBX to USD"""
        if progress_callback:
            progress_callback(10, "Converting FBX to USD...")
        
        # Try multiple methods
        methods = [
            self._convert_fbx_usd_plugin,
            self._convert_fbx_usdcat,
            self._convert_fbx_python,
        ]
        
        for method in methods:
            try:
                if method(input_path, output_path, progress_callback):
                    return True
            except Exception as e:
                if progress_callback:
                    progress_callback(0, f"Method failed: {e}")
                continue
        
        if progress_callback:
            progress_callback(0, "All FBX conversion methods failed")
        return False
    
    def _convert_fbx_usd_plugin(self, input_path: str, output_path: str, 
                                 progress_callback: Optional[Callable] = None) -> bool:
        """Convert FBX using USD plugin (if available)"""
        if not USD_AVAILABLE:
            return False
        
        try:
            if progress_callback:
                progress_callback(20, "Trying USD FBX plugin...")
            
            # Try to open FBX as USD (requires FBX plugin)
            stage = Usd.Stage.Open(input_path)
            if stage:
                if progress_callback:
                    progress_callback(60, "Processing FBX data...")
                
                # Apply conversion options
                self._apply_stage_settings(stage)
                
                if progress_callback:
                    progress_callback(80, "Saving USD file...")
                
                stage.Export(str(output_path))
                
                if progress_callback:
                    progress_callback(100, "FBX conversion complete!")
                return True
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"USD plugin method failed: {e}")
        
        return False
    
    def _convert_fbx_usdcat(self, input_path: str, output_path: str,
                            progress_callback: Optional[Callable] = None) -> bool:
        """Convert FBX using usdcat CLI"""
        try:
            if progress_callback:
                progress_callback(30, "Trying usdcat...")
            
            cmd = ['usdcat', input_path, '-o', str(output_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(100, "Conversion complete!")
                return True
            else:
                if progress_callback:
                    progress_callback(0, f"usdcat error: {result.stderr}")
        except FileNotFoundError:
            if progress_callback:
                progress_callback(0, "usdcat not found")
        except subprocess.TimeoutExpired:
            if progress_callback:
                progress_callback(0, "usdcat timeout")
        
        return False
    
    def _convert_fbx_python(self, input_path: str, output_path: str,
                           progress_callback: Optional[Callable] = None) -> bool:
        """Convert FBX using Python libraries (trimesh, etc.)"""
        try:
            import trimesh
            
            if progress_callback:
                progress_callback(40, "Loading FBX with trimesh...")
            
            # Load mesh
            mesh = trimesh.load(input_path)
            
            if progress_callback:
                progress_callback(60, "Converting to USD...")
            
            # Create USD stage
            if not USD_AVAILABLE:
                return False
            
            stage = Usd.Stage.CreateNew(str(output_path))
            self._apply_stage_settings(stage)
            
            # Convert mesh
            if isinstance(mesh, trimesh.Trimesh):
                self._trimesh_to_usd(mesh, stage, '/World/Mesh')
            elif isinstance(mesh, trimesh.Scene):
                self._trimesh_scene_to_usd(mesh, stage)
            
            stage.GetRootLayer().Save()
            
            if progress_callback:
                progress_callback(100, "Conversion complete!")
            return True
        except ImportError:
            if progress_callback:
                progress_callback(0, "trimesh not installed")
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"trimesh conversion failed: {e}")
        
        return False
    
    def convert_obj(self, input_path: str, output_path: str,
                   progress_callback: Optional[Callable] = None) -> bool:
        """Convert OBJ to USD"""
        if progress_callback:
            progress_callback(10, "Converting OBJ to USD...")
        
        try:
            import trimesh
            
            if progress_callback:
                progress_callback(30, "Loading OBJ file...")
            
            # Load OBJ
            mesh = trimesh.load(input_path)
            
            if progress_callback:
                progress_callback(60, "Creating USD stage...")
            
            if not USD_AVAILABLE:
                return False
            
            stage = Usd.Stage.CreateNew(str(output_path))
            self._apply_stage_settings(stage)
            
            # Convert
            if isinstance(mesh, trimesh.Trimesh):
                self._trimesh_to_usd(mesh, stage, '/World/Mesh')
            elif isinstance(mesh, trimesh.Scene):
                self._trimesh_scene_to_usd(mesh, stage)
            
            stage.GetRootLayer().Save()
            
            if progress_callback:
                progress_callback(100, "OBJ conversion complete!")
            return True
        except ImportError:
            if progress_callback:
                progress_callback(0, "trimesh not installed. Install with: pip install trimesh")
            return False
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"OBJ conversion failed: {e}")
            return False
    
    def convert_alembic(self, input_path: str, output_path: str,
                       progress_callback: Optional[Callable] = None) -> bool:
        """
        Convert Alembic to USD with enhanced support
        
        Supports:
        - Animated data with time samples
        - Full scene hierarchy
        - Materials and properties
        - Multiple conversion methods with fallbacks
        """
        if progress_callback:
            progress_callback(10, "Converting Alembic to USD...")
        
        # Check Alembic plugin availability
        alembic_plugin_available = self._check_alembic_plugin()
        
        if progress_callback:
            if alembic_plugin_available:
                progress_callback(15, "Alembic plugin detected")
            else:
                progress_callback(15, "Alembic plugin not found, trying alternative methods...")
        
        # Method 1: Use USD native Alembic plugin (best for animated data)
        if USD_AVAILABLE and alembic_plugin_available:
            try:
                if progress_callback:
                    progress_callback(30, "Using USD Alembic plugin...")
                
                # Open Alembic file directly
                stage = Usd.Stage.Open(input_path)
                if stage:
                    if progress_callback:
                        # Get time range for progress reporting
                        start_time = stage.GetStartTimeCode()
                        end_time = stage.GetEndTimeCode()
                        if start_time != end_time:
                            progress_callback(40, f"Processing animated Alembic ({start_time}-{end_time})...")
                        else:
                            progress_callback(40, "Processing Alembic data...")
                    
                    # Apply conversion settings
                    self._apply_stage_settings(stage)
                    
                    # Handle time samples
                    if self.options.time_samples and stage.HasAuthoredTimeCodeRange():
                        if progress_callback:
                            progress_callback(60, "Exporting with time samples...")
                        # Export with time samples preserved
                        stage.Export(str(output_path))
                    else:
                        if progress_callback:
                            progress_callback(60, "Flattening to single time sample...")
                        # Flatten to single time
                        flattened_stage = Usd.Stage.CreateNew(str(output_path))
                        self._apply_stage_settings(flattened_stage)
                        UsdUtils.StageCache.Get().Insert(stage)
                        # Copy prims at default time
                        self._copy_stage_content(stage, flattened_stage, Usd.TimeCode.Default())
                        flattened_stage.GetRootLayer().Save()
                    
                    if progress_callback:
                        progress_callback(100, "Alembic conversion complete!")
                    return True
            except Exception as e:
                if progress_callback:
                    progress_callback(0, f"USD Alembic plugin failed: {e}")
                print(f"Alembic conversion error: {e}")
        
        # Method 2: Use usdcat CLI tool (reliable fallback)
        if self._convert_alembic_usdcat(input_path, output_path, progress_callback):
            return True
        
        # Method 3: Try Python Alembic library as last resort
        if self._convert_alembic_python(input_path, output_path, progress_callback):
            return True
        
        if progress_callback:
            progress_callback(0, "Alembic conversion failed. Install USD with Alembic support.")
        return False
    
    def _check_alembic_plugin(self) -> bool:
        """Check if USD Alembic plugin is available"""
        if not USD_AVAILABLE:
            return False
        
        try:
            from pxr import Plug
            
            registry = Plug.Registry()
            # Check for Alembic plugin
            alembic_plugin = registry.GetPluginWithName('usdAbc')
            
            if alembic_plugin:
                # Try to load it
                if not alembic_plugin.isLoaded:
                    try:
                        alembic_plugin.Load()
                    except:
                        pass
                return alembic_plugin.isLoaded
            
            # Check plugin paths
            plugin_paths = [
                '/usr/local/lib/usd/plugin',
                '/opt/pixar/usd/plugin',
                os.path.expanduser('~/.usd/plugin'),
            ]
            
            for path in plugin_paths:
                pluginfo = Path(path) / 'usdAbc' / 'plugInfo.json'
                if pluginfo.exists():
                    return True
                    
        except Exception as e:
            print(f"Error checking Alembic plugin: {e}")
        
        return False
    
    def _convert_alembic_usdcat(self, input_path: str, output_path: str,
                               progress_callback: Optional[Callable] = None) -> bool:
        """Convert Alembic using usdcat CLI tool"""
        try:
            if progress_callback:
                progress_callback(40, "Trying usdcat CLI tool...")
            
            cmd = ['usdcat', input_path, '-o', str(output_path)]
            
            # Add options based on conversion settings
            if not self.options.time_samples:
                cmd.append('--flattenLayerStack')
            
            # Add time range if specified
            if self.options.time_samples:
                cmd.extend(['--frame', str(self.options.start_frame)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(100, "Conversion complete!")
                return True
            else:
                if progress_callback:
                    progress_callback(0, f"usdcat error: {result.stderr[:100]}")
                print(f"usdcat error: {result.stderr}")
                return False
        except FileNotFoundError:
            if progress_callback:
                progress_callback(0, "usdcat not found in PATH")
            return False
        except subprocess.TimeoutExpired:
            if progress_callback:
                progress_callback(0, "usdcat conversion timed out")
            return False
        except Exception as e:
            print(f"usdcat conversion error: {e}")
            return False
    
    def _convert_alembic_python(self, input_path: str, output_path: str,
                               progress_callback: Optional[Callable] = None) -> bool:
        """Convert Alembic using Python Alembic library (fallback)"""
        try:
            import imath
            import alembic.Abc as Abc
            import alembic.AbcGeom as AbcGeom
            
            if progress_callback:
                progress_callback(50, "Using Python Alembic library...")
            
            if not USD_AVAILABLE:
                return False
            
            # Open Alembic archive
            archive = Abc.IArchive(str(input_path))
            if not archive.valid():
                return False
            
            # Create USD stage
            stage = Usd.Stage.CreateNew(str(output_path))
            self._apply_stage_settings(stage)
            
            # Get root object
            root = archive.getTop()
            
            if progress_callback:
                progress_callback(70, "Converting Alembic hierarchy...")
            
            # Convert Alembic objects to USD
            self._convert_alembic_object(root, stage, '/Root', progress_callback)
            
            stage.GetRootLayer().Save()
            
            if progress_callback:
                progress_callback(100, "Conversion complete!")
            return True
            
        except ImportError:
            # Python Alembic library not available
            return False
        except Exception as e:
            print(f"Python Alembic conversion error: {e}")
            return False
    
    def _convert_alembic_object(self, abc_obj, usd_stage, usd_path, progress_callback=None):
        """Recursively convert Alembic object to USD prim"""
        try:
            import alembic.AbcGeom as AbcGeom
            
            # Get object metadata
            metadata = abc_obj.getMetadata()
            name = metadata.get('name', 'Object')
            
            # Create USD prim
            prim_path = f"{usd_path}/{name}"
            prim = usd_stage.DefinePrim(prim_path)
            
            # Check object type and convert
            if AbcGeom.IPolyMesh.matches(abc_obj.getHeader()):
                # Convert mesh
                mesh = AbcGeom.IPolyMesh(abc_obj, AbcGeom.WrapExistingFlag.kNoHierarchy)
                self._convert_alembic_mesh(mesh, usd_stage, prim_path)
            elif AbcGeom.IXform.matches(abc_obj.getHeader()):
                # Convert transform
                xform = AbcGeom.IXform(abc_obj, AbcGeom.WrapExistingFlag.kNoHierarchy)
                self._convert_alembic_xform(xform, usd_stage, prim_path)
            elif AbcGeom.ICamera.matches(abc_obj.getHeader()):
                # Convert camera
                camera = AbcGeom.ICamera(abc_obj, AbcGeom.WrapExistingFlag.kNoHierarchy)
                self._convert_alembic_camera(camera, usd_stage, prim_path)
            
            # Process children
            for i in range(abc_obj.getNumChildren()):
                child = abc_obj.getChild(i)
                self._convert_alembic_object(child, usd_stage, prim_path, progress_callback)
                
        except Exception as e:
            print(f"Error converting Alembic object: {e}")
    
    def _convert_alembic_mesh(self, abc_mesh, usd_stage, usd_path):
        """Convert Alembic mesh to USD mesh"""
        try:
            import imath
            
            mesh_schema = abc_mesh.getSchema()
            usd_mesh = UsdGeom.Mesh.Define(usd_stage, usd_path)
            
            # Get positions
            positions_sample = mesh_schema.getPositionsProperty().getValue(0)
            if positions_sample:
                points = [Gf.Vec3f(p.x, p.y, p.z) for p in positions_sample]
                usd_mesh.CreatePointsAttr(points)
            
            # Get face indices
            face_indices_sample = mesh_schema.getFaceIndicesProperty().getValue(0)
            face_counts_sample = mesh_schema.getFaceCountsProperty().getValue(0)
            
            if face_indices_sample and face_counts_sample:
                usd_mesh.CreateFaceVertexIndicesAttr(list(face_indices_sample))
                usd_mesh.CreateFaceVertexCountsAttr(list(face_counts_sample))
            
            # Get normals if available
            if self.options.export_normals:
                normals_param = mesh_schema.getNormalsParam()
                if normals_param and normals_param.getNumSamples() > 0:
                    normals_sample = normals_param.getValue(0)
                    if normals_sample:
                        normals = [Gf.Vec3f(n.x, n.y, n.z) for n in normals_sample]
                        usd_mesh.CreateNormalsAttr(normals)
                        usd_mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
            
            # Get UVs if available
            if self.options.export_uvs:
                uvs_param = mesh_schema.getUVsParam()
                if uvs_param and uvs_param.getNumSamples() > 0:
                    uvs_sample = uvs_param.getValue(0)
                    if uvs_sample:
                        uvs = [Gf.Vec2f(uv.x, uv.y) for uv in uvs_sample]
                        primvar = usd_mesh.CreatePrimvar('st', Sdf.ValueTypeNames.TexCoord2fArray)
                        primvar.Set(uvs)
                        primvar.SetInterpolation(UsdGeom.Tokens.faceVarying)
                        
        except Exception as e:
            print(f"Error converting Alembic mesh: {e}")
    
    def _convert_alembic_xform(self, abc_xform, usd_stage, usd_path):
        """Convert Alembic transform to USD xform"""
        try:
            import imath
            
            xform_schema = abc_xform.getSchema()
            usd_xform = UsdGeom.Xform.Define(usd_stage, usd_path)
            
            # Get transform matrix
            xform_sample = xform_schema.getValue(0)
            matrix = xform_sample.getMatrix()
            
            # Convert to USD matrix
            usd_matrix = Gf.Matrix4d()
            for i in range(4):
                for j in range(4):
                    usd_matrix[i][j] = matrix[i][j]
            
            # Set transform
            xform_op = usd_xform.AddTransformOp()
            xform_op.Set(usd_matrix)
            
        except Exception as e:
            print(f"Error converting Alembic transform: {e}")
    
    def _convert_alembic_camera(self, abc_camera, usd_stage, usd_path):
        """Convert Alembic camera to USD camera"""
        try:
            camera_schema = abc_camera.getSchema()
            usd_camera = UsdGeom.Camera.Define(usd_stage, usd_path)
            
            # Get camera sample
            camera_sample = camera_schema.getValue(0)
            
            # Set focal length
            focal_length = camera_sample.getFocalLength()
            if focal_length:
                usd_camera.CreateFocalLengthAttr(focal_length)
            
            # Set aperture
            horizontal_aperture = camera_sample.getHorizontalAperture()
            vertical_aperture = camera_sample.getVerticalAperture()
            
            if horizontal_aperture:
                usd_camera.CreateHorizontalApertureAttr(horizontal_aperture)
            if vertical_aperture:
                usd_camera.CreateVerticalApertureAttr(vertical_aperture)
                
        except Exception as e:
            print(f"Error converting Alembic camera: {e}")
    
    def _copy_stage_content(self, source_stage, dest_stage, time_code):
        """Copy content from source stage to destination stage at specified time"""
        try:
            from pxr import UsdUtils
            
            # Get root prims
            source_root = source_stage.GetPseudoRoot()
            dest_root = dest_stage.GetPseudoRoot()
            
            # Copy each root child
            for child in source_root.GetChildren():
                self._copy_prim_recursive(child, dest_stage, dest_root.GetPath(), time_code)
                
        except Exception as e:
            print(f"Error copying stage content: {e}")
    
    def _copy_prim_recursive(self, source_prim, dest_stage, parent_path, time_code):
        """Recursively copy prim and its children"""
        try:
            # Create prim in destination
            prim_path = f"{parent_path}/{source_prim.GetName()}"
            dest_prim = dest_stage.DefinePrim(prim_path, source_prim.GetTypeName())
            
            # Copy attributes at time code
            for attr in source_prim.GetAttributes():
                if attr.HasValue():
                    try:
                        value = attr.Get(time_code)
                        dest_attr = dest_prim.CreateAttribute(attr.GetName(), attr.GetTypeName())
                        dest_attr.Set(value)
                    except:
                        pass
            
            # Copy relationships
            for rel in source_prim.GetRelationships():
                targets = rel.GetTargets()
                if targets:
                    dest_rel = dest_prim.CreateRelationship(rel.GetName())
                    dest_rel.SetTargets(targets)
            
            # Recursively copy children
            for child in source_prim.GetChildren():
                self._copy_prim_recursive(child, dest_stage, prim_path, time_code)
                
        except Exception as e:
            print(f"Error copying prim: {e}")
    
    def convert_gltf(self, input_path: str, output_path: str,
                    progress_callback: Optional[Callable] = None) -> bool:
        """Convert glTF/GLB to USD"""
        if progress_callback:
            progress_callback(10, "Converting glTF to USD...")
        
        try:
            import pygltflib
            
            if progress_callback:
                progress_callback(30, "Loading glTF file...")
            
            gltf = pygltflib.GLTF2.load(input_path)
            
            if progress_callback:
                progress_callback(60, "Creating USD stage...")
            
            if not USD_AVAILABLE:
                return False
            
            stage = Usd.Stage.CreateNew(str(output_path))
            self._apply_stage_settings(stage)
            
            # Convert glTF to USD
            self._gltf_to_usd(gltf, stage, input_path)
            
            stage.GetRootLayer().Save()
            
            if progress_callback:
                progress_callback(100, "glTF conversion complete!")
            return True
        except ImportError:
            if progress_callback:
                progress_callback(0, "pygltflib not installed. Install with: pip install pygltflib")
            return False
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"glTF conversion failed: {e}")
            return False
    
    def convert_stl(self, input_path: str, output_path: str,
                  progress_callback: Optional[Callable] = None) -> bool:
        """Convert STL to USD"""
        if progress_callback:
            progress_callback(10, "Converting STL to USD...")
        
        try:
            import trimesh
            
            if progress_callback:
                progress_callback(30, "Loading STL file...")
            
            mesh = trimesh.load(input_path)
            
            if progress_callback:
                progress_callback(60, "Creating USD stage...")
            
            if not USD_AVAILABLE:
                return False
            
            stage = Usd.Stage.CreateNew(str(output_path))
            self._apply_stage_settings(stage)
            
            if isinstance(mesh, trimesh.Trimesh):
                self._trimesh_to_usd(mesh, stage, '/World/Mesh')
            
            stage.GetRootLayer().Save()
            
            if progress_callback:
                progress_callback(100, "STL conversion complete!")
            return True
        except ImportError:
            if progress_callback:
                progress_callback(0, "trimesh not installed")
            return False
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"STL conversion failed: {e}")
            return False
    
    def convert_ply(self, input_path: str, output_path: str,
                   progress_callback: Optional[Callable] = None) -> bool:
        """Convert PLY to USD"""
        if progress_callback:
            progress_callback(10, "Converting PLY to USD...")
        
        try:
            import trimesh
            
            if progress_callback:
                progress_callback(30, "Loading PLY file...")
            
            mesh = trimesh.load(input_path)
            
            if progress_callback:
                progress_callback(60, "Creating USD stage...")
            
            if not USD_AVAILABLE:
                return False
            
            stage = Usd.Stage.CreateNew(str(output_path))
            self._apply_stage_settings(stage)
            
            if isinstance(mesh, trimesh.Trimesh):
                self._trimesh_to_usd(mesh, stage, '/World/Mesh')
            
            stage.GetRootLayer().Save()
            
            if progress_callback:
                progress_callback(100, "PLY conversion complete!")
            return True
        except ImportError:
            if progress_callback:
                progress_callback(0, "trimesh not installed")
            return False
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"PLY conversion failed: {e}")
            return False
    
    def convert_dae(self, input_path: str, output_path: str,
                   progress_callback: Optional[Callable] = None) -> bool:
        """Convert Collada DAE to USD"""
        # Similar to OBJ/STL - use trimesh
        return self.convert_obj(input_path, output_path, progress_callback)
    
    def convert_3ds(self, input_path: str, output_path: str,
                   progress_callback: Optional[Callable] = None) -> bool:
        """Convert 3DS to USD"""
        # Similar to OBJ/STL - use trimesh
        return self.convert_obj(input_path, output_path, progress_callback)
    
    def convert_blender(self, input_path: str, output_path: str,
                       progress_callback: Optional[Callable] = None) -> bool:
        """Convert Blender file to USD"""
        if progress_callback:
            progress_callback(0, "Blender conversion requires Blender installation")
        return False
    
    def _trimesh_to_usd(self, mesh, stage: Usd.Stage, prim_path: str):
        """Convert trimesh to USD mesh"""
        if not USD_AVAILABLE:
            return
        
        # Create mesh prim
        usd_mesh = UsdGeom.Mesh.Define(stage, prim_path)
        
        # Get vertices
        vertices = [Gf.Vec3f(v[0], v[1], v[2]) for v in mesh.vertices]
        usd_mesh.CreatePointsAttr(vertices)
        
        # Get faces
        face_vertex_counts = []
        face_vertex_indices = []
        
        for face in mesh.faces:
            face_vertex_counts.append(len(face))
            face_vertex_indices.extend(face)
        
        usd_mesh.CreateFaceVertexCountsAttr(face_vertex_counts)
        usd_mesh.CreateFaceVertexIndicesAttr(face_vertex_indices)
        
        # Get normals if available
        if self.options.export_normals and hasattr(mesh, 'vertex_normals'):
            normals = [Gf.Vec3f(n[0], n[1], n[2]) for n in mesh.vertex_normals]
            usd_mesh.CreateNormalsAttr(normals)
            usd_mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
        
        # Get UVs if available
        if self.options.export_uvs and hasattr(mesh, 'visual') and hasattr(mesh.visual, 'uv'):
            uvs = [Gf.Vec2f(uv[0], uv[1]) for uv in mesh.visual.uv]
            primvar = usd_mesh.CreatePrimvar('st', Sdf.ValueTypeNames.TexCoord2fArray)
            primvar.Set(uvs)
            primvar.SetInterpolation(UsdGeom.Tokens.vertex)
        
        # Apply scale and transforms
        if self.options.scale != 1.0:
            xformable = UsdGeom.Xformable(usd_mesh)
            scale_op = xformable.AddScaleOp()
            scale_op.Set(Gf.Vec3f(self.options.scale, self.options.scale, self.options.scale))
    
    def _trimesh_scene_to_usd(self, scene, stage: Usd.Stage):
        """Convert trimesh scene to USD"""
        if not USD_AVAILABLE:
            return
        
        root_path = '/World'
        root = UsdGeom.Xform.Define(stage, root_path)
        stage.SetDefaultPrim(root.GetPrim())
        
        # Convert each geometry node
        for node_name, node in scene.graph.nodes.items():
            if hasattr(node, 'geometry') and node.geometry:
                mesh_path = f"{root_path}/{node_name}"
                self._trimesh_to_usd(node.geometry, stage, mesh_path)
    
    def _gltf_to_usd(self, gltf, stage: Usd.Stage, gltf_path: str):
        """Convert glTF to USD"""
        if not USD_AVAILABLE:
            return
        
        root_path = '/World'
        root = UsdGeom.Xform.Define(stage, root_path)
        stage.SetDefaultPrim(root.GetPrim())
        
        # Convert glTF scenes
        for scene_idx, scene in enumerate(gltf.scenes or []):
            scene_path = f"{root_path}/Scene_{scene_idx}"
            scene_xform = UsdGeom.Xform.Define(stage, scene_path)
            
            # Convert nodes
            for node_idx in scene.nodes or []:
                if node_idx < len(gltf.nodes):
                    self._gltf_node_to_usd(gltf, node_idx, stage, scene_path)
    
    def _gltf_node_to_usd(self, gltf, node_idx: int, stage: Usd.Stage, parent_path: str):
        """Convert glTF node to USD"""
        if not USD_AVAILABLE or node_idx >= len(gltf.nodes):
            return
        
        node = gltf.nodes[node_idx]
        node_name = node.name or f"Node_{node_idx}"
        node_path = f"{parent_path}/{node_name}"
        
        # Create transform
        xform = UsdGeom.Xform.Define(stage, node_path)
        xformable = UsdGeom.Xformable(xform)
        
        # Apply transform
        if node.matrix:
            # glTF uses column-major, USD uses row-major
            matrix = Gf.Matrix4d(*node.matrix)
            xform_op = xformable.AddTransformOp()
            xform_op.Set(matrix)
        
        # Convert mesh if present
        if node.mesh is not None and node.mesh < len(gltf.meshes or []):
            mesh = gltf.meshes[node.mesh]
            self._gltf_mesh_to_usd(gltf, mesh, stage, node_path)
        
        # Process children
        for child_idx in node.children or []:
            self._gltf_node_to_usd(gltf, child_idx, stage, node_path)
    
    def _gltf_mesh_to_usd(self, gltf, mesh, stage: Usd.Stage, parent_path: str):
        """Convert glTF mesh to USD"""
        if not USD_AVAILABLE:
            return
        
        mesh_path = f"{parent_path}/Mesh"
        usd_mesh = UsdGeom.Mesh.Define(stage, mesh_path)
        
        # Get accessors for positions
        for primitive in mesh.primitives or []:
            if primitive.attributes and 'POSITION' in primitive.attributes:
                # This is simplified - full glTF conversion is complex
                # Would need to handle accessors, buffer views, etc.
                pass
    
    def _apply_stage_settings(self, stage: Usd.Stage):
        """Apply conversion options to USD stage"""
        if not USD_AVAILABLE:
            return
        
        # Set up axis
        up_axis = UsdGeom.Tokens.y if self.options.up_axis == 'Y' else UsdGeom.Tokens.z
        UsdGeom.SetStageUpAxis(stage, up_axis)
        
        # Set units
        UsdGeom.SetStageMetersPerUnit(stage, self.options.meters_per_unit)
        
        # Set time codes
        if self.options.time_samples:
            stage.SetStartTimeCode(self.options.start_frame)
            stage.SetEndTimeCode(self.options.end_frame)
            stage.SetFramesPerSecond(self.options.fps)
        
        # Set default prim
        root_prim = stage.GetPrimAtPath('/World')
        if root_prim:
            stage.SetDefaultPrim(root_prim)

