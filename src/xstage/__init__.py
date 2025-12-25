"""
xStage - Extended USD Viewer
Professional USD viewer with pipeline integration
"""

__version__ = "0.1.0"
__author__ = "NOX VFX & Contributors"

from .viewer import USDViewerWindow, ViewportWidget, ViewerSettings, USDStageManager
from .viewport import ViewportWidget
from .orientation import AxisOrientationWidget
from .converter import USDConverter, ConversionOptions
from .config import AppConfig

# New feature modules
from .usd_lux_support import UsdLuxExtractor
from .collections import CollectionManager
from .variants import VariantManager
from .materials import MaterialManager
from .validation import USDValidator
from .payloads import PayloadManager
from .color_space import ColorSpaceManager

__all__ = [
    "USDViewerWindow",
    "ViewportWidget",
    "ViewerSettings",
    "USDStageManager",
    "AxisOrientationWidget",
    "USDConverter",
    "ConversionOptions",
    "AppConfig",
    # New features
    "UsdLuxExtractor",
    "CollectionManager",
    "VariantManager",
    "MaterialManager",
    "USDValidator",
    "PayloadManager",
    "ColorSpaceManager",
]