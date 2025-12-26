"""
Format conversion
"""

from .converter import USDConverter, ConversionOptions
from .material_creator import MaterialCreator, MaterialShaderType
from .material_validator import MaterialValidator, MaterialIssue

try:
    from .converter_ui import ConverterDialog
    from .adobe_converter import AdobeUSDConverter
    __all__ = [
        "USDConverter",
        "ConversionOptions",
        "MaterialCreator",
        "MaterialShaderType",
        "MaterialValidator",
        "MaterialIssue",
        "AdobeUSDConverter",
        "ConverterDialog",
    ]
except ImportError:
    try:
        from .adobe_converter import AdobeUSDConverter
        __all__ = [
            "USDConverter",
            "ConversionOptions",
            "MaterialCreator",
            "MaterialShaderType",
            "MaterialValidator",
            "MaterialIssue",
            "AdobeUSDConverter",
        ]
    except ImportError:
        __all__ = [
            "USDConverter",
            "ConversionOptions",
            "MaterialCreator",
            "MaterialShaderType",
            "MaterialValidator",
            "MaterialIssue",
        ]

