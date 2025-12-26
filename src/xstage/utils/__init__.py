"""
Utilities
"""

try:
    from .annotations import AnnotationManager
    from .bookmarks import BookmarkManager
    from .cache_manager import CacheManager
    from .color_space import ColorSpaceManager
    from .help_system import HelpSystem, HelpDialog
    from .light_visualization import LightVisualization
    from .performance_profiler import PerformanceProfiler
    from .pipeline_integration import PipelineIntegration
    from .progress_manager import ProgressReporter, ProgressDialogManager
    from .recent_files import RecentFilesManager
    from .theme_manager import ThemeManager, ThemeColors, ThemeMode
    from .usd_lux_support import UsdLuxExtractor
    from .validation import ValidationManager
    from .viewport_overlay import ViewportOverlay
    
    __all__ = [
        "AnnotationManager",
        "BookmarkManager",
        "CacheManager",
        "ColorSpaceManager",
        "HelpSystem",
        "HelpDialog",
        "LightVisualization",
        "PerformanceProfiler",
        "PipelineIntegration",
        "ProgressReporter",
        "ProgressDialogManager",
        "RecentFilesManager",
        "ThemeManager",
        "ThemeColors",
        "ThemeMode",
        "UsdLuxExtractor",
        "ValidationManager",
        "ViewportOverlay",
    ]
    
    # Adobe plugin installer (optional)
    try:
        from .adobe_plugin_installer import (
            AdobePluginInstaller,
            auto_install_adobe_plugins,
            ensure_adobe_plugins_available,
        )
        __all__.extend([
            "AdobePluginInstaller",
            "auto_install_adobe_plugins",
            "ensure_adobe_plugins_available",
        ])
    except ImportError:
        pass
    
except ImportError as e:
    __all__ = []
    print(f"Warning: Some utilities could not be imported: {e}")

