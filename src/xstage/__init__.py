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
try:
    from .ui.widgets import (
        AxisOrientationWidget,
    )
except ImportError:
    # AxisOrientationWidget is optional
    AxisOrientationWidget = None

from .ui.editors import (
    AnimationCurveEditorWidget,
    AnnotationsWidget,
    CameraManagerWidget,
    CollectionEditorWidget,
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
# ConverterDialog is optional
try:
    from .ui.editors import ConverterDialog
except ImportError:
    ConverterDialog = None

# Managers
from .managers import (
    AnimationCurveManager,
    BatchOperationManager,
    CameraManager,
    CollectionManager,
    CoordinateSystemManager,
    LayerCompositionManager,
    MaterialManager,
    OpenExecManager,
    PayloadManager,
    PrimSelectionManager,
    QuiltiXManager,
    SceneComparator,
    SceneSearchManager,
    StageVariableManager,
    UndoRedoManager,
    VariantManager,
)
# NamespaceEditor is optional
try:
    from .managers import NamespaceEditor
except ImportError:
    NamespaceEditor = None

# Converters
from .converters import (
    USDConverter,
    ConversionOptions,
)
# ConverterDialogClass is an alias for ConverterDialog
ConverterDialogClass = ConverterDialog

# Utils
from .utils import (
    AnnotationManager,
    BookmarkManager,
    CacheManager,
    ColorSpaceManager,
    HelpSystem,
    HelpDialog,
    LightVisualization,
    OCIOManager,
    PerformanceProfiler,
    PipelineIntegration,
    ProgressReporter,
    ProgressDialogManager,
    RecentFilesManager,
    SceneMetricsCalculator,
    ThemeManager,
    ThemeColors,
    ThemeMode,
    UsdLuxExtractor,
    ValidationManager,
    ViewportOverlay,
)

# Config (optional - config.py may be empty)
try:
    from .config import AppConfig
except ImportError:
    AppConfig = None

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
]
# Add optional components to __all__ only if they exist
if AxisOrientationWidget is not None:
    __all__.append("AxisOrientationWidget")
if NamespaceEditor is not None:
    __all__.append("NamespaceEditor")
if ConverterDialog is not None:
    __all__.append("ConverterDialog")
if AppConfig is not None:
    __all__.append("AppConfig")
__all__.extend([
    # UI Editors
    "AnimationCurveEditorWidget",
    "AnnotationsWidget",
    "AOVVisualizationWidget",
    "CameraManagerWidget",
    "CollectionEditorWidget",
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
    "OpenExecManager",
    "PayloadManager",
    "PrimSelectionManager",
    "QuiltiXManager",
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
    "OCIOManager",
    "PerformanceProfiler",
    "PipelineIntegration",
    "ProgressReporter",
    "ProgressDialogManager",
    "RecentFilesManager",
    "SceneMetricsCalculator",
    "ThemeManager",
    "ThemeColors",
    "ThemeMode",
    "UsdLuxExtractor",
    "ValidationManager",
    "ViewportOverlay",
    # Multi-viewport
    "MultiViewportWidget",
])

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
