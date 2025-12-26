"""
Enhanced USD Converter with Adobe USD Fileformat Plugins
Supports native FBX, OBJ, glTF, STL, PLY, and Substance (SBSAR) formats

Adobe USD Fileformat Plugins provide native reading support for:
- FBX (Filmbox) - Primary focus, full scene support
- OBJ (Wavefront) - Enhanced with material support
- glTF/GLB - Enhanced with PBR materials
- STL (Stereolithography) - Native support
- PLY (Polygon File Format) - Native support
- Substance (SBSAR) - Adobe's proprietary material format

See: https://github.com/adobe/USD-Fileformat-plugins
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

from converter import ConversionOptions, USDConverter as BaseConverter

try:
    from pxr import Usd, UsdGeom, Gf, Sdf, UsdShade, UsdUtils
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class AdobeUSDConverter(BaseConverter):
    """
    Enhanced USD converter using Adobe's USD fileformat plugins
    Provides native FBX support without external dependencies
    Automatically installs plugins to xStage directory if not available
    """
    
    def __init__(self, options: ConversionOptions, auto_install=True):
        super().__init__(options)
        self.auto_install = auto_install
        self.adobe_plugins_available = self.check_adobe_plugins()
        
        # Auto-install if not available and auto_install is enabled
        if not self.adobe_plugins_available and self.auto_install:
            self._try_auto_install()
    
    def _try_auto_install(self):
        """Try to automatically install Adobe plugins"""
        try:
            from ..utils.adobe_plugin_installer import ensure_adobe_plugins_available
            if ensure_adobe_plugins_available():
                # Recheck after installation
                self.adobe_plugins_available = self.check_adobe_plugins()
        except Exception as e:
            print(f"Auto-installation failed: {e}")
            print("You can manually install Adobe plugins or disable auto-install.")
        
    def check_adobe_plugins(self) -> bool:
        """Check if Adobe USD fileformat plugins are available"""
        if not USD_AVAILABLE:
            return False
            
        try:
            # Setup xStage plugin path first
            try:
                from ..utils.adobe_plugin_installer import AdobePluginInstaller
                installer = AdobePluginInstaller()
                installer.setup_plugin_path()
            except:
                pass
            
            # Check if FBX plugin is registered
            from pxr import Plug
            
            plugin_registry = Plug.Registry()
            fbx_plugin = plugin_registry.GetPluginWithName('usdFbx')
            
            if fbx_plugin:
                if not fbx_plugin.isLoaded:
                    try:
                        fbx_plugin.Load()
                    except:
                        pass
                if fbx_plugin.isLoaded:
                    return True
                
            # Try to find plugins in standard locations
            plugin_paths = [
                '/usr/local/lib/usd/plugins',
                '/opt/pixar/usd/plugins',
                '/opt/adobe/usd/plugins',
                os.path.expanduser('~/.usd/plugins'),
            ]
            
            # Also check xStage plugin directory
            try:
                from ..utils.adobe_plugin_installer import AdobePluginInstaller
                installer = AdobePluginInstaller()
                xstage_plugin_path = installer.get_xstage_plugin_path()
                plugin_paths.insert(0, str(xstage_plugin_path))
            except:
                pass
            
            for path in plugin_paths:
                if Path(path).exists():
                    pluginfo_path = Path(path) / 'plugInfo.json'
                    if pluginfo_path.exists():
                        return True
                    # Check for plugin subdirectories
                    for plugin_name in ['usdFbx', 'usdObj', 'usdGltf']:
                        plugin_dir = Path(path) / plugin_name
                        if plugin_dir.exists() and (plugin_dir / 'plugInfo.json').exists():
                            return True
                        
        except Exception as e:
            print(f"Error checking Adobe plugins: {e}")
            
        return False
        
    def convert_fbx(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """
        Convert FBX to USD using Adobe's fileformat plugin
        Falls back to external tools if plugin not available
        """
        if progress_callback:
            progress_callback(10, "Converting FBX to USD...")
            
        # Try Adobe native plugin first
        if self.adobe_plugins_available:
            return self._convert_fbx_native(input_path, output_path, progress_callback)
        
        # Try FBX2USD command-line tool
        if self._check_fbx2usd():
            return self._convert_fbx_cli(input_path, output_path, progress_callback)
            
        # Try Autodesk FBX Python SDK
        try:
            return self._convert_fbx_sdk(input_path, output_path, progress_callback)
        except ImportError:
            pass
            
        # Fall back to external tools
        return super().convert_fbx(input_path, output_path, progress_callback)
        
    def _convert_fbx_native(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """Convert FBX using Adobe USD fileformat plugin (native USD reading)"""
        try:
            if progress_callback:
                progress_callback(20, "Using Adobe USD plugin for FBX...")
                
            # Simply open the FBX file as USD (plugin handles conversion)
            # The fileformat plugin makes FBX appear as native USD
            stage = Usd.Stage.Open(input_path)
            
            if not stage:
                raise RuntimeError("Failed to open FBX with USD plugin")
                
            if progress_callback:
                progress_callback(60, "Processing FBX data...")
                
            # Apply conversion options
            self._apply_stage_settings(stage)
            
            if progress_callback:
                progress_callback(80, "Saving USD file...")
                
            # Export to USD format
            stage.Export(output_path)
            
            if progress_callback:
                progress_callback(100, "FBX conversion complete!")
                
            return True
            
        except Exception as e:
            print(f"Adobe plugin conversion failed: {e}")
            return False
            
    def _convert_fbx_cli(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """Convert FBX using fbx2usd command-line tool"""
        try:
            if progress_callback:
                progress_callback(20, "Using fbx2usd CLI tool...")
                
            cmd = [
                'fbx2usd',
                input_path,
                output_path,
                '--up-axis', self.options.up_axis.lower(),
                '--meters-per-unit', str(self.options.meters_per_unit),
            ]
            
            if self.options.export_materials:
                cmd.append('--materials')
            if self.options.export_normals:
                cmd.append('--normals')
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(100, "FBX conversion complete!")
                return True
            else:
                print(f"fbx2usd error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("fbx2usd not found in PATH")
            return False
            
    def _convert_fbx_sdk(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """Convert FBX using Autodesk FBX Python SDK"""
        try:
            import fbx
            
            if progress_callback:
                progress_callback(20, "Using FBX Python SDK...")
                
            # Initialize FBX SDK
            manager = fbx.FbxManager.Create()
            ios = fbx.FbxIOSettings.Create(manager, fbx.IOSROOT)
            manager.SetIOSettings(ios)
            
            # Import FBX
            importer = fbx.FbxImporter.Create(manager, "")
            if not importer.Initialize(input_path, -1, manager.GetIOSettings()):
                raise RuntimeError(f"FBX import failed: {importer.GetStatus().GetErrorString()}")
                
            scene = fbx.FbxScene.Create(manager, "fbxScene")
            importer.Import(scene)
            importer.Destroy()
            
            if progress_callback:
                progress_callback(50, "Converting FBX scene to USD...")
                
            # Create USD stage
            stage = Usd.Stage.CreateNew(output_path)
            self._apply_stage_settings(stage)
            
            # Convert FBX scene to USD
            self._fbx_scene_to_usd(scene, stage, progress_callback)
            
            # Save
            stage.GetRootLayer().Save()
            
            if progress_callback:
                progress_callback(100, "FBX conversion complete!")
                
            manager.Destroy()
            return True
            
        except ImportError:
            raise ImportError("FBX Python SDK not installed")
            
    def _fbx_scene_to_usd(self, fbx_scene, usd_stage, progress_callback=None):
        """Convert FBX scene to USD stage"""
        # Create root
        root = UsdGeom.Xform.Define(usd_stage, '/Root')
        usd_stage.SetDefaultPrim(root.GetPrim())
        
        # Process FBX hierarchy
        root_node = fbx_scene.GetRootNode()
        self._process_fbx_node(root_node, usd_stage, '/Root', progress_callback)
        
    def _process_fbx_node(self, fbx_node, usd_stage, parent_path, progress_callback=None):
        """Recursively process FBX nodes"""
        import fbx
        
        node_name = fbx_node.GetName()
        if not node_name:
            node_name = "Node"
            
        # Create USD prim path
        node_path = f"{parent_path}/{node_name}"
        
        # Get node attribute
        node_attr = fbx_node.GetNodeAttribute()
        
        if node_attr:
            attr_type = node_attr.GetAttributeType()
            
            if attr_type == fbx.FbxNodeAttribute.eMesh:
                self._convert_fbx_mesh(fbx_node, usd_stage, node_path)
            elif attr_type == fbx.FbxNodeAttribute.eCamera:
                self._convert_fbx_camera(fbx_node, usd_stage, node_path)
            elif attr_type == fbx.FbxNodeAttribute.eLight:
                self._convert_fbx_light(fbx_node, usd_stage, node_path)
            else:
                # Create transform
                UsdGeom.Xform.Define(usd_stage, node_path)
        else:
            # Create transform for empty nodes
            UsdGeom.Xform.Define(usd_stage, node_path)
            
        # Set transform
        self._set_fbx_transform(fbx_node, usd_stage, node_path)
        
        # Process children
        for i in range(fbx_node.GetChildCount()):
            child = fbx_node.GetChild(i)
            self._process_fbx_node(child, usd_stage, node_path, progress_callback)
            
    def _convert_fbx_mesh(self, fbx_node, usd_stage, usd_path):
        """Convert FBX mesh to USD"""
        import fbx
        
        fbx_mesh = fbx_node.GetNodeAttribute()
        
        # Create USD mesh
        usd_mesh = UsdGeom.Mesh.Define(usd_stage, usd_path)
        
        # Get vertices
        control_points = fbx_mesh.GetControlPoints()
        vertices = [Gf.Vec3f(cp[0], cp[1], cp[2]) for cp in control_points]
        usd_mesh.CreatePointsAttr(vertices)
        
        # Get polygons
        polygon_count = fbx_mesh.GetPolygonCount()
        face_vertex_counts = []
        face_vertex_indices = []
        
        for i in range(polygon_count):
            polygon_size = fbx_mesh.GetPolygonSize(i)
            face_vertex_counts.append(polygon_size)
            
            for j in range(polygon_size):
                vertex_index = fbx_mesh.GetPolygonVertex(i, j)
                face_vertex_indices.append(vertex_index)
                
        usd_mesh.CreateFaceVertexCountsAttr(face_vertex_counts)
        usd_mesh.CreateFaceVertexIndicesAttr(face_vertex_indices)
        
        # Get normals if available
        if self.options.export_normals:
            element_normal = fbx_mesh.GetElementNormal()
            if element_normal:
                normals = []
                for i in range(polygon_count):
                    for j in range(fbx_mesh.GetPolygonSize(i)):
                        normal_index = element_normal.GetIndexArray().GetAt(i * fbx_mesh.GetPolygonSize(i) + j)
                        normal = element_normal.GetDirectArray().GetAt(normal_index)
                        normals.append(Gf.Vec3f(normal[0], normal[1], normal[2]))
                        
                usd_mesh.CreateNormalsAttr(normals)
                usd_mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
                
        # Get UVs if available
        if self.options.export_uvs:
            element_uv = fbx_mesh.GetElementUV()
            if element_uv:
                uvs = []
                for i in range(polygon_count):
                    for j in range(fbx_mesh.GetPolygonSize(i)):
                        uv_index = element_uv.GetIndexArray().GetAt(i * fbx_mesh.GetPolygonSize(i) + j)
                        uv = element_uv.GetDirectArray().GetAt(uv_index)
                        uvs.append(Gf.Vec2f(uv[0], uv[1]))
                        
                primvar = usd_mesh.CreatePrimvar('st', Sdf.ValueTypeNames.TexCoord2fArray)
                primvar.Set(uvs)
                primvar.SetInterpolation(UsdGeom.Tokens.faceVarying)
                
    def _convert_fbx_camera(self, fbx_node, usd_stage, usd_path):
        """Convert FBX camera to USD"""
        import fbx
        
        fbx_camera = fbx_node.GetNodeAttribute()
        usd_camera = UsdGeom.Camera.Define(usd_stage, usd_path)
        
        # Set camera properties
        usd_camera.CreateFocalLengthAttr(fbx_camera.FocalLength.Get())
        
        aperture_width = fbx_camera.GetApertureWidth()
        aperture_height = fbx_camera.GetApertureHeight()
        usd_camera.CreateHorizontalApertureAttr(aperture_width)
        usd_camera.CreateVerticalApertureAttr(aperture_height)
        
    def _convert_fbx_light(self, fbx_node, usd_stage, usd_path):
        """Convert FBX light to USD"""
        import fbx
        
        fbx_light = fbx_node.GetNodeAttribute()
        light_type = fbx_light.LightType.Get()
        
        # Map FBX light types to USD
        if light_type == fbx.FbxLight.ePoint:
            usd_light = UsdGeom.SphereLight.Define(usd_stage, usd_path)
        elif light_type == fbx.FbxLight.eDirectional:
            usd_light = UsdGeom.DistantLight.Define(usd_stage, usd_path)
        elif light_type == fbx.FbxLight.eSpot:
            usd_light = UsdGeom.DiskLight.Define(usd_stage, usd_path)
        else:
            usd_light = UsdGeom.SphereLight.Define(usd_stage, usd_path)
            
        # Set intensity
        color = fbx_light.Color.Get()
        intensity = fbx_light.Intensity.Get()
        
    def _set_fbx_transform(self, fbx_node, usd_stage, usd_path):
        """Set USD transform from FBX node"""
        import fbx
        
        # Get global transform
        transform = fbx_node.EvaluateGlobalTransform()
        
        # Convert to USD matrix
        matrix = Gf.Matrix4d()
        for i in range(4):
            for j in range(4):
                matrix[i][j] = transform.Get(i, j)
                
        # Set transform on USD prim
        xformable = UsdGeom.Xformable(usd_stage.GetPrimAtPath(usd_path))
        if xformable:
            xform_op = xformable.AddTransformOp()
            xform_op.Set(matrix)
            
    def convert_alembic(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """
        Enhanced Alembic to USD conversion
        Uses USD's native Alembic support with better options
        """
        if progress_callback:
            progress_callback(10, "Converting Alembic to USD...")
            
        try:
            # Method 1: Use USD's built-in Alembic reader (best for animated data)
            if self._convert_alembic_native(input_path, output_path, progress_callback):
                return True
                
            # Method 2: Use usdcat for direct conversion
            if self._convert_alembic_usdcat(input_path, output_path, progress_callback):
                return True
                
            # Method 3: Reference method (fallback)
            return super().convert_alembic(input_path, output_path, progress_callback)
            
        except Exception as e:
            print(f"Alembic conversion error: {e}")
            return False
            
    def _convert_alembic_native(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """
        Convert Alembic using USD's native Alembic plugin (usdAbc)
        Enhanced with better time sample handling and error recovery
        """
        try:
            if progress_callback:
                progress_callback(30, "Reading Alembic with USD plugin...")
                
            # Check plugin availability first
            from pxr import Plug
            registry = Plug.Registry()
            alembic_plugin = registry.GetPluginWithName('usdAbc')
            
            if not alembic_plugin:
                if progress_callback:
                    progress_callback(0, "USD Alembic plugin (usdAbc) not found")
                return False
            
            # Load plugin if not already loaded
            if not alembic_plugin.isLoaded:
                try:
                    alembic_plugin.Load()
                except Exception as e:
                    if progress_callback:
                        progress_callback(0, f"Failed to load Alembic plugin: {e}")
                    return False
                
            # USD can directly open Alembic files if the plugin is available
            source_stage = Usd.Stage.Open(input_path)
            
            if not source_stage:
                if progress_callback:
                    progress_callback(0, "Failed to open Alembic file")
                return False
            
            # Get time range for progress reporting
            start_time = source_stage.GetStartTimeCode()
            end_time = source_stage.GetEndTimeCode()
            has_animation = start_time != end_time
            
            if progress_callback:
                if has_animation:
                    progress_callback(50, f"Processing animated Alembic (frames {start_time}-{end_time})...")
                else:
                    progress_callback(50, "Processing Alembic data...")
                
            # Create output stage
            dest_stage = Usd.Stage.CreateNew(output_path)
            self._apply_stage_settings(dest_stage)
            
            # Handle time samples based on options
            if self.options.time_samples and has_animation:
                if progress_callback:
                    progress_callback(70, "Exporting with time samples...")
                
                # Export with time samples preserved
                # Use reference method to preserve animation
                dest_stage.GetRootLayer().subLayerPaths.append(source_stage.GetRootLayer().identifier)
                
                # Set time range
                dest_stage.SetStartTimeCode(start_time)
                dest_stage.SetEndTimeCode(end_time)
                dest_stage.SetFramesPerSecond(self.options.fps)
                
                # Export/flatten based on preference
                if self.options.preserve_hierarchy:
                    dest_stage.GetRootLayer().Save()
                else:
                    # Flatten to single layer
                    flattened = UsdUtils.StageCache.Get().Insert(dest_stage)
                    flattened.Export(output_path)
            else:
                if progress_callback:
                    progress_callback(70, "Flattening to single time sample...")
                
                # Flatten to default time
                self._copy_stage_content(source_stage, dest_stage, Usd.TimeCode.Default())
                dest_stage.GetRootLayer().Save()
                
            if progress_callback:
                progress_callback(100, "Alembic conversion complete!")
                
            return True
            
        except Exception as e:
            print(f"Native Alembic conversion failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def _convert_alembic_usdcat(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """Convert Alembic using usdcat CLI tool"""
        try:
            if progress_callback:
                progress_callback(40, "Using usdcat for conversion...")
                
            cmd = ['usdcat', input_path, '-o', output_path]
            
            # Add flattening option
            if not self.options.time_samples:
                cmd.extend(['--flattenLayerStack'])
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(100, "Conversion complete!")
                return True
            else:
                print(f"usdcat error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("usdcat not found in PATH")
            return False
            
    def _apply_stage_settings(self, stage: Usd.Stage):
        """Apply conversion options to USD stage"""
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
            
    def _check_fbx2usd(self) -> bool:
        """Check if fbx2usd CLI tool is available"""
        try:
            result = subprocess.run(['fbx2usd', '--version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def install_adobe_plugins():
    """
    Helper function to install Adobe USD fileformat plugins
    """
    print("Adobe USD Fileformat Plugins Installation Guide")
    print("=" * 60)
    print()
    print("Option 1: Build from source (Recommended)")
    print("-" * 60)
    print("""
    git clone https://github.com/adobe/USD-Fileformat-plugins.git
    cd USD-Fileformat-plugins
    mkdir build && cd build
    
    cmake -DUSD_ROOT=/usr/local/USD \\
          -DCMAKE_INSTALL_PREFIX=/usr/local/USD \\
          ..
    
    make -j$(nproc)
    sudo make install
    """)
    
    print()
    print("Option 2: Use pre-built packages (if available)")
    print("-" * 60)
    print("""
    # Check Adobe's releases page for pre-built packages
    # https://github.com/adobe/USD-Fileformat-plugins/releases
    """)
    
    print()
    print("Option 3: Install FBX Python SDK")
    print("-" * 60)
    print("""
    # Download from Autodesk:
    # https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-2
    
    # Extract and install
    chmod +x fbx202020_fbxpythonsdk_linux
    ./fbx202020_fbxpythonsdk_linux /usr/local/fbx
    
    # Add to Python path
    export PYTHONPATH=/usr/local/fbx/lib/Python37_x64:$PYTHONPATH
    """)
    
    print()
    print("After installation, restart the USD Viewer.")
    print()


if __name__ == "__main__":
    # Check what's available
    converter = AdobeUSDConverter(ConversionOptions())
    
    print("USD Converter Status:")
    print(f"  USD Available: {USD_AVAILABLE}")
    print(f"  Adobe Plugins: {converter.adobe_plugins_available}")
    print(f"  fbx2usd CLI: {converter._check_fbx2usd()}")
    print()
    
    if not converter.adobe_plugins_available:
        print("Adobe USD plugins not found.")
        install_adobe_plugins()