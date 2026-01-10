"""
OpenColorIO (OCIO) Integration for Color-Accurate Asset Review
Handles color space detection, conversion, and management
"""

from typing import Optional, Dict, List
import os

try:
    import PyOpenColorIO as ocio
    OCIO_AVAILABLE = True
    
    # Get OCIO version
    try:
        # PyOpenColorIO 2.2.0+ has GetVersion()
        if hasattr(ocio, 'GetVersion'):
            OCIO_VERSION_INFO = ocio.GetVersion()
            OCIO_VERSION_STRING = f"{OCIO_VERSION_INFO[0]}.{OCIO_VERSION_INFO[1]}.{OCIO_VERSION_INFO[2]}"
            OCIO_VERSION_TUPLE = (OCIO_VERSION_INFO[0], OCIO_VERSION_INFO[1], OCIO_VERSION_INFO[2])
        else:
            # Fallback: try to get from module
            OCIO_VERSION_STRING = getattr(ocio, '__version__', '2.2.0')
            version_parts = OCIO_VERSION_STRING.split('.')
            OCIO_VERSION_TUPLE = tuple(int(part) for part in version_parts[:3])
    except:
        # Default to 2.2.0 if version detection fails
        OCIO_VERSION_STRING = "2.2.0"
        OCIO_VERSION_TUPLE = (2, 2, 0)
    
except ImportError:
    OCIO_AVAILABLE = False
    ocio = None
    OCIO_VERSION_STRING = None
    OCIO_VERSION_TUPLE = (0, 0, 0)

try:
    from pxr import Usd, UsdLux
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    Usd = None
    UsdLux = None


class OCIOManager:
    """Manages OpenColorIO color management for asset review"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize OCIO manager
        
        Args:
            config_path: Path to OCIO config file (None = use default/ACES)
        """
        self.ocio_available = OCIO_AVAILABLE
        self.config = None
        self.config_path = config_path
        
        if not self.ocio_available:
            print("Warning: PyOpenColorIO not available. Install with: pip install PyOpenColorIO")
            return
        
        # Load OCIO config
        self.load_config(config_path)
    
    def load_config(self, config_path: Optional[str] = None) -> bool:
        """
        Load OCIO config file
        
        Args:
            config_path: Path to OCIO config file (None = use default/ACES)
        
        Returns:
            True if config loaded successfully
        """
        if not self.ocio_available:
            return False
        
        try:
            if config_path:
                if os.path.exists(config_path):
                    self.config = ocio.Config.CreateFromFile(config_path)
                    self.config_path = config_path
                    return True
                else:
                    print(f"Warning: OCIO config file not found: {config_path}")
            
            # Try to use default config (from OCIO env var or ACES)
            ocio_env = os.getenv('OCIO')
            if ocio_env and os.path.exists(ocio_env):
                self.config = ocio.Config.CreateFromFile(ocio_env)
                self.config_path = ocio_env
                return True
            
            # Try to use ACES 1.2 (if available)
            try:
                # Try ACES 1.2 config
                self.config = ocio.Config.CreateFromConfig("aces_1.2")
                self.config_path = "aces_1.2"
                return True
            except:
                pass
            
            # Try ACES 1.3 (if available)
            try:
                self.config = ocio.Config.CreateFromConfig("aces_1.3")
                self.config_path = "aces_1.3"
                return True
            except:
                pass
            
            # Last resort: create minimal config
            self.config = ocio.Config.CreateRaw()
            self.config_path = "raw"
            print("Warning: Using raw OCIO config. Colors may not be accurate.")
            return True
            
        except Exception as e:
            print(f"Error loading OCIO config: {e}")
            self.config = None
            return False
    
    def get_color_space_from_usd(self, prim) -> Optional[str]:
        """
        Get color space from USD prim using ColorSpaceAPI
        
        Args:
            prim: USD prim to check
        
        Returns:
            Color space name or None
        """
        if not USD_AVAILABLE or not prim:
            return None
        
        try:
            color_space_api = UsdLux.ColorSpaceAPI(prim)
            if not color_space_api:
                return None
            
            # Get explicit color space
            color_space_attr = color_space_api.GetColorSpaceAttr()
            if color_space_attr:
                color_space = color_space_attr.Get()
                if color_space:
                    return color_space
            
            # Get inherited color space
            inherited_attr = color_space_api.GetInheritedColorSpaceAttr()
            if inherited_attr:
                inherited = inherited_attr.Get()
                if inherited:
                    return inherited
        except Exception as e:
            print(f"Error getting color space from USD: {e}")
        
        return None
    
    def get_default_color_space(self, stage) -> Optional[str]:
        """
        Get default color space from USD stage
        
        Args:
            stage: USD stage to check
        
        Returns:
            Default color space name or None
        """
        if not USD_AVAILABLE or not stage:
            return None
        
        try:
            root_prim = stage.GetPseudoRoot()
            return self.get_color_space_from_usd(root_prim)
        except Exception as e:
            print(f"Error getting default color space: {e}")
            return None
    
    def create_processor(self, from_space: str, to_space: str) -> Optional[object]:
        """
        Create OCIO processor for color space conversion
        
        Args:
            from_space: Source color space name
            to_space: Target color space name
        
        Returns:
            OCIO CPUProcessor or None
        """
        if not self.ocio_available or not self.config:
            return None
        
        try:
            # Create processor for conversion
            processor = self.config.getProcessor(from_space, to_space)
            return processor.getDefaultCPUProcessor()
        except Exception as e:
            print(f"Error creating OCIO processor ({from_space} -> {to_space}): {e}")
            return None
    
    def get_display_color_space(self) -> str:
        """
        Get display color space (for viewport)
        
        Returns:
            Display color space name (default: sRGB)
        """
        if not self.ocio_available or not self.config:
            return "sRGB"  # Fallback
        
        try:
            # Get default display/view
            display = self.config.getDefaultDisplay()
            view = self.config.getDefaultView(display)
            return self.config.getDisplayViewColorSpaceName(display, view)
        except Exception as e:
            print(f"Error getting display color space: {e}")
            return "sRGB"  # Fallback
    
    def get_available_color_spaces(self) -> List[str]:
        """
        Get list of available color spaces
        
        Returns:
            List of color space names
        """
        if not self.ocio_available or not self.config:
            return []
        
        try:
            return [cs.getName() for cs in self.config.getColorSpaces()]
        except Exception as e:
            print(f"Error getting available color spaces: {e}")
            return []
    
    def get_config_name(self) -> str:
        """
        Get OCIO config name
        
        Returns:
            Config name or "None"
        """
        if not self.ocio_available or not self.config:
            return "None"
        
        try:
            return self.config.getName() or self.config_path or "Unknown"
        except:
            return self.config_path or "Unknown"
    
    def is_available(self) -> bool:
        """
        Check if OCIO is available
        
        Returns:
            True if OCIO is available
        """
        return self.ocio_available and self.config is not None
    
    def get_version_info(self) -> Dict:
        """
        Get OCIO version information
        
        Returns:
            Dictionary with version info
        """
        return {
            'available': self.ocio_available,
            'version_string': OCIO_VERSION_STRING if OCIO_AVAILABLE else None,
            'version_tuple': OCIO_VERSION_TUPLE if OCIO_AVAILABLE else (0, 0, 0),
            'python_bindings': 'PyOpenColorIO>=2.2.0',
        }
    
    def get_color_space_info(self, stage) -> Dict[str, any]:
        """
        Get comprehensive color space information for a stage
        
        Args:
            stage: USD stage to analyze
        
        Returns:
            Dictionary with color space information
        """
        info = {
            'ocio_available': self.is_available(),
            'config_name': self.get_config_name(),
            'ocio_version': OCIO_VERSION_STRING if OCIO_AVAILABLE else None,
            'asset_color_space': None,
            'display_color_space': self.get_display_color_space(),
            'available_color_spaces': []
        }
        
        if not self.is_available():
            return info
        
        # Get asset color space from USD
        if stage:
            asset_color_space = self.get_default_color_space(stage)
            if asset_color_space:
                info['asset_color_space'] = asset_color_space
            else:
                # Default to scene-linear if not specified
                info['asset_color_space'] = "scene-linear Rec.709-sRGB"
        
        # Get available color spaces (limit to first 20 for performance)
        available = self.get_available_color_spaces()
        info['available_color_spaces'] = available[:20]
        
        return info

