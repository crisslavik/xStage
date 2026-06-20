"""
USD Version Detection and Compatibility
Provides version detection and feature flags for USD compatibility
"""

try:
    from pxr import Usd
    USD_AVAILABLE = True
    
    # Try to get USD version
    try:
        import pxr
        # Check for version attribute
        USD_VERSION_STRING = getattr(pxr, '__version__', None)
        
        if USD_VERSION_STRING:
            # Parse version string (e.g., "25.11.0" -> (25, 11, 0))
            version_parts = USD_VERSION_STRING.split('.')
            USD_VERSION_TUPLE = tuple(int(part) for part in version_parts[:3])
        else:
            # Fallback: try to detect from Usd module
            # USD 25.11+ has certain features we can check
            USD_VERSION_TUPLE = (0, 0, 0)
            
            # Try to detect version by checking for version-specific features
            if hasattr(Usd, 'GetVersion'):
                try:
                    version_info = Usd.GetVersion()
                    if version_info:
                        USD_VERSION_TUPLE = (version_info[0], version_info[1], version_info[2] if len(version_info) > 2 else 0)
                except Exception:
                    pass
            
            # If still unknown, check for known features
            if USD_VERSION_TUPLE == (0, 0, 0):
                try:
                    from pxr import UsdLux
                    # LightListAPI was added in USD 25.11
                    if hasattr(UsdLux, 'LightListAPI'):
                        USD_VERSION_TUPLE = (25, 11, 0)  # Assume at least 25.11
                    else:
                        USD_VERSION_TUPLE = (23, 11, 0)  # Assume older version
                except Exception:
                    USD_VERSION_TUPLE = (23, 11, 0)  # Conservative default
    
    except Exception as e:
        # If version detection fails, use conservative defaults
        USD_VERSION_TUPLE = (23, 11, 0)
        USD_VERSION_STRING = "unknown"
    
    # Feature detection flags
    USD_FEATURES = {
        # Light linking (LightListAPI) - USD 25.11+
        'light_linking': USD_VERSION_TUPLE >= (25, 11),
        
        # Depth of field (focusDistance, fStop) - USD 25.11+
        'dof': USD_VERSION_TUPLE >= (25, 11),
        
        # Enhanced UsdLux support - USD 25.11+
        'enhanced_usd_lux': USD_VERSION_TUPLE >= (25, 11),
        
        # MaterialX support - USD 23.11+
        'materialx': USD_VERSION_TUPLE >= (23, 11),
        
        # Hydra 2.0 - USD 23.11+
        'hydra2': USD_VERSION_TUPLE >= (23, 11),
        
        # OpenExec support - USD 24.08+
        'openexec': USD_VERSION_TUPLE >= (24, 8),
    }
    
    # Version comparison helpers
    def USD_VERSION_AT_LEAST(major: int, minor: int = 0, patch: int = 0) -> bool:
        """Check if USD version is at least the specified version"""
        return USD_VERSION_TUPLE >= (major, minor, patch)
    
    def USD_VERSION_BETWEEN(min_version: tuple, max_version: tuple) -> bool:
        """Check if USD version is between two versions"""
        return min_version <= USD_VERSION_TUPLE < max_version

except ImportError:
    USD_AVAILABLE = False
    USD_VERSION_STRING = None
    USD_VERSION_TUPLE = (0, 0, 0)
    USD_FEATURES = {
        'light_linking': False,
        'dof': False,
        'enhanced_usd_lux': False,
        'materialx': False,
        'hydra2': False,
        'openexec': False,
    }
    
    def USD_VERSION_AT_LEAST(major: int, minor: int = 0, patch: int = 0) -> bool:
        return False
    
    def USD_VERSION_BETWEEN(min_version: tuple, max_version: tuple) -> bool:
        return False


def get_usd_version_info() -> dict:
    """
    Get comprehensive USD version information
    
    Returns:
        Dictionary with version info and feature flags
    """
    return {
        'available': USD_AVAILABLE,
        'version_string': USD_VERSION_STRING if USD_AVAILABLE else None,
        'version_tuple': USD_VERSION_TUPLE if USD_AVAILABLE else (0, 0, 0),
        'features': USD_FEATURES.copy() if USD_AVAILABLE else {},
    }


def check_feature(feature_name: str) -> bool:
    """
    Check if a specific USD feature is available
    
    Args:
        feature_name: Name of feature to check
        
    Returns:
        True if feature is available, False otherwise
    """
    return USD_FEATURES.get(feature_name, False) if USD_AVAILABLE else False

