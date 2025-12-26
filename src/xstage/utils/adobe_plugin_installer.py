"""
Adobe USD Fileformat Plugins Auto-Installer
Automatically downloads and installs Adobe plugins to xStage's isolated directory
Does not affect system-wide USD installation or other software
"""

import os
import sys
import subprocess
import shutil
import platform
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
import urllib.request
import tarfile
import zipfile

try:
    from pxr import Plug
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class AdobePluginInstaller:
    """
    Automatically installs Adobe USD Fileformat Plugins to xStage's isolated directory
    """
    
    # Adobe plugins repository
    ADOBE_REPO_URL = "https://github.com/adobe/USD-Fileformat-plugins"
    ADOBE_RELEASES_URL = "https://api.github.com/repos/adobe/USD-Fileformat-plugins/releases/latest"
    
    def __init__(self):
        """Initialize installer with xStage's plugin directory"""
        self.xstage_home = Path.home() / ".xstage"
        self.plugins_dir = self.xstage_home / "plugins"
        self.adobe_plugins_dir = self.plugins_dir / "adobe-usd-plugins"
        self.source_dir = self.xstage_home / "src" / "adobe-usd-plugins"
        
        # Ensure directories exist
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.adobe_plugins_dir.mkdir(parents=True, exist_ok=True)
        
    def get_xstage_plugin_path(self) -> Path:
        """Get the path where xStage stores its plugins"""
        return self.adobe_plugins_dir
    
    def is_installed(self) -> bool:
        """Check if Adobe plugins are already installed in xStage directory"""
        # Check for plugInfo.json or plugin libraries
        pluginfo = self.adobe_plugins_dir / "plugInfo.json"
        if pluginfo.exists():
            return True
        
        # Check for plugin subdirectories (usdFbx, usdObj, etc.)
        plugin_names = ['usdFbx', 'usdObj', 'usdGltf', 'usdStl']
        for plugin_name in plugin_names:
            plugin_dir = self.adobe_plugins_dir / plugin_name
            if plugin_dir.exists() and (plugin_dir / "plugInfo.json").exists():
                return True
        
        return False
    
    def check_system_plugins(self) -> bool:
        """Check if Adobe plugins are available system-wide"""
        if not USD_AVAILABLE:
            return False
        
        try:
            registry = Plug.Registry()
            fbx_plugin = registry.GetPluginWithName('usdFbx')
            return fbx_plugin is not None and fbx_plugin.isLoaded
        except:
            return False
    
    def setup_plugin_path(self):
        """Set up USD plugin path environment variable for xStage only"""
        plugin_path = str(self.adobe_plugins_dir)
        
        # Get current plugin path (if any)
        current_path = os.environ.get('PXR_PLUGINPATH_NAME', '')
        
        # Add xStage plugin path if not already there
        if plugin_path not in current_path:
            if current_path:
                os.environ['PXR_PLUGINPATH_NAME'] = f"{plugin_path}:{current_path}"
            else:
                os.environ['PXR_PLUGINPATH_NAME'] = plugin_path
        
        # Also try alternative environment variable
        alt_path = os.environ.get('PXR_PLUGINPATH', '')
        if plugin_path not in alt_path:
            if alt_path:
                os.environ['PXR_PLUGINPATH'] = f"{plugin_path}:{alt_path}"
            else:
                os.environ['PXR_PLUGINPATH'] = plugin_path
    
    def get_latest_release_info(self) -> Optional[Dict]:
        """Get latest release information from GitHub API"""
        try:
            with urllib.request.urlopen(self.ADOBE_RELEASES_URL, timeout=10) as response:
                data = json.loads(response.read())
                return data
        except Exception as e:
            print(f"Could not fetch release info: {e}")
            return None
    
    def download_prebuilt_binary(self, release_info: Dict) -> Optional[Path]:
        """Download pre-built binary if available for current platform"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map platform to asset name patterns
        platform_patterns = {
            'linux': ['linux', 'ubuntu', 'rhel'],
            'darwin': ['macos', 'darwin', 'osx'],
            'windows': ['windows', 'win']
        }
        
        assets = release_info.get('assets', [])
        for asset in assets:
            name = asset.get('name', '').lower()
            url = asset.get('browser_download_url', '')
            
            # Check if asset matches platform
            for pattern in platform_patterns.get(system, []):
                if pattern in name:
                    # Download the asset
                    download_path = self.xstage_home / "downloads" / asset['name']
                    download_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    print(f"Downloading {asset['name']}...")
                    try:
                        urllib.request.urlretrieve(url, download_path)
                        return download_path
                    except Exception as e:
                        print(f"Download failed: {e}")
                        return None
        
        return None
    
    def install_from_source(self, progress_callback=None) -> bool:
        """
        Install Adobe plugins by building from source
        This is the most reliable method but requires build tools
        """
        if progress_callback:
            progress_callback(10, "Cloning Adobe USD Fileformat Plugins repository...")
        
        # Clone repository if not exists
        if not self.source_dir.exists():
            try:
                subprocess.run(
                    ['git', 'clone', '--depth', '1', self.ADOBE_REPO_URL, str(self.source_dir)],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Failed to clone repository: {e}")
                return False
            except FileNotFoundError:
                print("Git not found. Please install git to build from source.")
                return False
        
        if progress_callback:
            progress_callback(30, "Building Adobe plugins...")
        
        # Find USD installation
        usd_root = self._find_usd_root()
        if not usd_root:
            print("USD installation not found. Please set USD_ROOT environment variable.")
            return False
        
        # Build plugins
        build_dir = self.source_dir / "build"
        build_dir.mkdir(exist_ok=True)
        
        try:
            # Configure with CMake
            cmake_cmd = [
                'cmake',
                f'-DUSD_ROOT={usd_root}',
                f'-DCMAKE_INSTALL_PREFIX={self.adobe_plugins_dir}',
                '-DCMAKE_BUILD_TYPE=Release',
                str(self.source_dir)
            ]
            
            if progress_callback:
                progress_callback(40, "Configuring build...")
            
            result = subprocess.run(
                cmake_cmd,
                cwd=str(build_dir),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"CMake configuration failed: {result.stderr}")
                return False
            
            # Build
            if progress_callback:
                progress_callback(60, "Compiling plugins...")
            
            result = subprocess.run(
                ['cmake', '--build', '.', '--config', 'Release', '-j'],
                cwd=str(build_dir),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Build failed: {result.stderr}")
                return False
            
            # Install to xStage directory
            if progress_callback:
                progress_callback(90, "Installing plugins to xStage directory...")
            
            result = subprocess.run(
                ['cmake', '--install', '.', '--config', 'Release'],
                cwd=str(build_dir),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Installation failed: {result.stderr}")
                return False
            
            if progress_callback:
                progress_callback(100, "Adobe plugins installed successfully!")
            
            return True
            
        except FileNotFoundError as e:
            print(f"Build tool not found: {e}")
            print("Please install CMake and a C++ compiler to build from source.")
            return False
        except Exception as e:
            print(f"Build error: {e}")
            return False
    
    def _find_usd_root(self) -> Optional[str]:
        """Find USD installation root"""
        # Check environment variable
        usd_root = os.environ.get('USD_ROOT')
        if usd_root and Path(usd_root).exists():
            return usd_root
        
        # Check common installation paths
        common_paths = [
            '/usr/local/USD',
            '/opt/pixar/USD',
            '/opt/usd',
            Path.home() / 'USD',
        ]
        
        for path in common_paths:
            path_obj = Path(path)
            if path_obj.exists():
                # Check for USD installation
                if (path_obj / "lib" / "libusd.so").exists() or \
                   (path_obj / "lib" / "libusd.dylib").exists() or \
                   (path_obj / "lib" / "usd.lib").exists():
                    return str(path_obj)
        
        # Try to find via Python
        try:
            import pxr
            pxr_path = Path(pxr.__file__).parent.parent
            # Go up to find USD root
            for parent in pxr_path.parents:
                if (parent / "lib" / "libusd.so").exists() or \
                   (parent / "lib" / "libusd.dylib").exists():
                    return str(parent)
        except:
            pass
        
        return None
    
    def install(self, progress_callback=None, prefer_binary=True) -> bool:
        """
        Install Adobe plugins automatically
        
        Args:
            progress_callback: Optional callback(progress, message)
            prefer_binary: Try to download pre-built binary first
        
        Returns:
            True if installation successful
        """
        # Check if already installed
        if self.is_installed():
            print("Adobe plugins already installed in xStage directory.")
            self.setup_plugin_path()
            return True
        
        # Check if system plugins available (don't install if already available)
        if self.check_system_plugins():
            print("Adobe plugins already available system-wide. Using system plugins.")
            return True
        
        print("Adobe USD Fileformat Plugins not found. Installing to xStage directory...")
        
        # Try to download pre-built binary first
        if prefer_binary:
            release_info = self.get_latest_release_info()
            if release_info:
                binary_path = self.download_prebuilt_binary(release_info)
                if binary_path:
                    if self._extract_binary(binary_path):
                        self.setup_plugin_path()
                        return True
        
        # Fall back to building from source
        print("Pre-built binary not available. Building from source...")
        if self.install_from_source(progress_callback):
            self.setup_plugin_path()
            return True
        
        print("Installation failed. You can manually install Adobe plugins.")
        print(f"See: {self.ADOBE_REPO_URL}")
        return False
    
    def _extract_binary(self, archive_path: Path) -> bool:
        """Extract downloaded binary archive"""
        try:
            print(f"Extracting {archive_path.name}...")
            
            if archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(self.adobe_plugins_dir)
            elif archive_path.suffix in ['.tar', '.tar.gz', '.tgz']:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(self.adobe_plugins_dir)
            else:
                print(f"Unknown archive format: {archive_path.suffix}")
                return False
            
            # Clean up
            archive_path.unlink()
            return True
            
        except Exception as e:
            print(f"Extraction failed: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify that plugins are properly installed and can be loaded"""
        self.setup_plugin_path()
        
        if not USD_AVAILABLE:
            return False
        
        try:
            # Force plugin registry to reload
            registry = Plug.Registry()
            
            # Check for FBX plugin
            fbx_plugin = registry.GetPluginWithName('usdFbx')
            if fbx_plugin:
                if not fbx_plugin.isLoaded:
                    fbx_plugin.Load()
                return fbx_plugin.isLoaded
            
            return False
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def uninstall(self):
        """Remove installed plugins"""
        if self.adobe_plugins_dir.exists():
            shutil.rmtree(self.adobe_plugins_dir)
            print("Adobe plugins uninstalled from xStage directory.")
        
        if self.source_dir.exists():
            shutil.rmtree(self.source_dir)
            print("Source code removed.")


def auto_install_adobe_plugins(progress_callback=None) -> bool:
    """
    Convenience function to auto-install Adobe plugins
    """
    installer = AdobePluginInstaller()
    return installer.install(progress_callback=progress_callback)


def ensure_adobe_plugins_available() -> bool:
    """
    Ensure Adobe plugins are available (install if needed)
    Returns True if plugins are available (either system-wide or installed)
    """
    installer = AdobePluginInstaller()
    
    # Check system plugins first
    if installer.check_system_plugins():
        return True
    
    # Check xStage installation
    if installer.is_installed():
        installer.setup_plugin_path()
        return installer.verify_installation()
    
    # Try to install
    print("Adobe plugins not found. Attempting automatic installation...")
    if installer.install():
        return installer.verify_installation()
    
    return False

