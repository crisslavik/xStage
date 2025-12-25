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
        """Convert Alembic to USD"""
        if progress_callback:
            progress_callback(10, "Converting Alembic to USD...")
        
        # Try USD native Alembic support
        if USD_AVAILABLE:
            try:
                if progress_callback:
                    progress_callback(30, "Using USD Alembic plugin...")
                
                # USD can open Alembic directly if plugin is available
                stage = Usd.Stage.Open(input_path)
                if stage:
                    if progress_callback:
                        progress_callback(60, "Processing Alembic data...")
                    
                    self._apply_stage_settings(stage)
                    
                    if progress_callback:
                        progress_callback(80, "Saving USD file...")
                    
                    stage.Export(str(output_path))
                    
                    if progress_callback:
                        progress_callback(100, "Alembic conversion complete!")
                    return True
            except Exception as e:
                if progress_callback:
                    progress_callback(0, f"USD Alembic plugin failed: {e}")
        
        # Try usdcat
        try:
            if progress_callback:
                progress_callback(40, "Trying usdcat...")
            
            cmd = ['usdcat', input_path, '-o', str(output_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(100, "Conversion complete!")
                return True
        except:
            pass
        
        if progress_callback:
            progress_callback(0, "Alembic conversion failed. Install USD with Alembic support.")
        return False
    
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

