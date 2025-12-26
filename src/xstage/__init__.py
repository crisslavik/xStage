"""
xStage - Extended USD Viewer for Production Pipelines
"""

# Core
from .core import (
    USDViewerWindow,
    ViewerSettings,
    USDStageManager,
    ViewportWidget,
)

# Rendering
from .rendering import (
    HydraViewportWidget,
)

# UI
from .ui.widgets import (
    AxisOrientationWidget,
)

from .ui.editors import (
    AnimationCurveEditorWidget,
    AnnotationsWidget,
    CameraManagerWidget,
    CollectionEditorWidget,
    ConverterDialog,
    LayerCompositionWidget,
    MaterialEditorWidget,
    OpenExecWidget,
    PrimPropertiesWidget,
    PrimvarEditorWidget,
    RenderSettingsEditorWidget,
    SceneComparisonWidget,
    SceneSearchWidget,
    StageVariablesWidget,
)

# Managers
from .managers import (
    AnimationCurveManager,
    BatchOperationManager,
    CameraManager,
    CollectionManager,
    CoordinateSystemManager,
    LayerCompositionManager,
    MaterialManager,
    NamespaceEditor,
    OpenExecManager,
    PayloadManager,
    PrimSelectionManager,
    SceneComparator,
    SceneSearchManager,
    StageVariableManager,
    UndoRedoManager,
    VariantManager,
)

# Converters
from .converters import (
    USDConverter,
    ConversionOptions,
    ConverterDialog as ConverterDialogClass,
)

# Utils
from .utils import (
    AnnotationManager,
    BookmarkManager,
    CacheManager,
    ColorSpaceManager,
    HelpSystem,
    HelpDialog,
    LightVisualization,
    PerformanceProfiler,
    PipelineIntegration,
    ProgressReporter,
    ProgressDialogManager,
    RecentFilesManager,
    ThemeManager,
    ThemeColors,
    ThemeMode,
    UsdLuxExtractor,
    ValidationManager,
    ViewportOverlay,
)

# Adobe Plugin Installer (optional)
try:
    from .utils.adobe_plugin_installer import (
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

# Config
from .config import AppConfig

# Multi-viewport
from .multi_viewport import MultiViewportWidget

__all__ = [
    # Core
    "USDViewerWindow",
    "ViewerSettings",
    "USDStageManager",
    "ViewportWidget",
    # Rendering
    "HydraViewportWidget",
    # UI Widgets
    "AxisOrientationWidget",
    # UI Editors
    "AnimationCurveEditorWidget",
    "AnnotationsWidget",
    "AOVVisualizationWidget",
    "CameraManagerWidget",
    "CollectionEditorWidget",
    "ConverterDialog",
    "LayerCompositionWidget",
    "MaterialEditorWidget",
    "OpenExecWidget",
    "PrimPropertiesWidget",
    "PrimvarEditorWidget",
    "RenderSettingsEditorWidget",
    "SceneComparisonWidget",
    "SceneSearchWidget",
    "StageVariablesWidget",
    # UI Widgets
    "MaterialPreviewWidget",
    "TexturePreviewWidget",
    # Managers
    "AnimationCurveManager",
    "AOVManager",
    "AOVInfo",
    "AOVDisplayMode",
    "BatchOperationManager",
    "CameraManager",
    "CollectionManager",
    "CoordinateSystemManager",
    "InstancingManager",
    "InstanceInfo",
    "InstanceMode",
    "LayerCompositionManager",
    "LODManager",
    "LODLevel",
    "LODMode",
    "MaterialManager",
    "NamespaceEditor",
    "OpenExecManager",
    "PayloadManager",
    "PrimSelectionManager",
    "SceneComparator",
    "SceneSearchManager",
    "SelectionSetManager",
    "SelectionSet",
    "SelectionSetOperation",
    "StageVariableManager",
    "UndoRedoManager",
    "VariantManager",
    # Converters
    "USDConverter",
    "ConversionOptions",
    # Utils
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
    # Config
    "AppConfig",
    # Multi-viewport
    "MultiViewportWidget",
]
