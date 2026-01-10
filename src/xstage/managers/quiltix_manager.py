"""
QuiltiX MaterialX Editor Integration
Manages QuiltiX external launch and integration
"""

import os
import subprocess
from typing import Optional, Dict
from pathlib import Path

try:
    from pxr import Usd
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class QuiltiXManager:
    """Manages QuiltiX MaterialX editor integration"""
    
    def __init__(self):
        self.quiltix_available = self._check_quiltix_available()
        self.quiltix_process = None
    
    def _check_quiltix_available(self) -> bool:
        """Check if QuiltiX is available"""
        try:
            import quiltix
            return True
        except ImportError:
            # Check if quiltix command is available
            try:
                result = subprocess.run(
                    ['quiltix', '--version'],
                    capture_output=True,
                    timeout=2
                )
                return result.returncode == 0
            except:
                return False
    
    def is_available(self) -> bool:
        """Check if QuiltiX is available"""
        return self.quiltix_available
    
    def launch_quiltix(self, usd_filepath: Optional[str] = None, 
                      material_prim_path: Optional[str] = None) -> bool:
        """
        Launch QuiltiX with USD file
        
        Args:
            usd_filepath: Path to USD file (optional, uses current stage if None)
            material_prim_path: Path to specific material prim (optional)
        
        Returns:
            True if launched successfully
        """
        if not self.quiltix_available:
            return False
        
        try:
            # Prepare environment
            env = os.environ.copy()
            
            # Set up Hydra plugin path if available
            hydra_plugin_path = self._get_hydra_plugin_path()
            if hydra_plugin_path:
                existing_path = env.get('PXR_PLUGINPATH_NAME', '')
                if existing_path:
                    env['PXR_PLUGINPATH_NAME'] = f"{existing_path}:{hydra_plugin_path}"
                else:
                    env['PXR_PLUGINPATH_NAME'] = hydra_plugin_path
            
            # Set up MaterialX library paths if available
            mtlx_lib_path = self._get_materialx_library_path()
            if mtlx_lib_path:
                existing_path = env.get('PXR_MTLX_STDLIB_SEARCH_PATHS', '')
                if existing_path:
                    env['PXR_MTLX_STDLIB_SEARCH_PATHS'] = f"{existing_path}:{mtlx_lib_path}"
                else:
                    env['PXR_MTLX_STDLIB_SEARCH_PATHS'] = mtlx_lib_path
            
            # Build command
            cmd = ['quiltix']
            
            if usd_filepath:
                cmd.append(usd_filepath)
            
            if material_prim_path:
                cmd.extend(['--material', material_prim_path])
            
            # Launch QuiltiX
            self.quiltix_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return True
        except Exception as e:
            print(f"Error launching QuiltiX: {e}")
            return False
    
    def launch_quiltix_for_material(self, stage: Optional[Usd.Stage], 
                                   material_prim_path: str) -> bool:
        """
        Launch QuiltiX for a specific material
        
        Args:
            stage: USD stage
            material_prim_path: Path to material prim
        
        Returns:
            True if launched successfully
        """
        if not stage:
            return False
        
        # Get USD file path
        root_layer = stage.GetRootLayer()
        if not root_layer:
            return False
        
        usd_filepath = root_layer.identifier
        if not usd_filepath or not os.path.exists(usd_filepath):
            return False
        
        return self.launch_quiltix(usd_filepath, material_prim_path)
    
    def _get_hydra_plugin_path(self) -> Optional[str]:
        """Get Hydra plugin path"""
        # Try common locations
        common_paths = [
            '/usr/local/usd/plugin',
            '/opt/usd/plugin',
            os.path.expanduser('~/usd/plugin'),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Check environment variable
        return os.environ.get('PXR_PLUGINPATH_NAME', None)
    
    def _get_materialx_library_path(self) -> Optional[str]:
        """Get MaterialX library path"""
        # Try common locations
        common_paths = [
            '/usr/local/materialx/libraries',
            '/opt/materialx/libraries',
            os.path.expanduser('~/materialx/libraries'),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Check environment variable
        return os.environ.get('PXR_MTLX_STDLIB_SEARCH_PATHS', None)
    
    def get_quiltix_info(self) -> Dict[str, any]:
        """Get QuiltiX availability and configuration info"""
        return {
            'available': self.is_available(),
            'hydra_plugin_path': self._get_hydra_plugin_path(),
            'materialx_library_path': self._get_materialx_library_path(),
        }

