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
    ColorSpaceManager,
    HelpSystem,
    HelpDialog,
    LightVisualization,
    PerformanceProfiler,
    PipelineIntegration,
    ProgressReporter,
    ProgressDialogManager,
    RecentFilesManager,
    UsdLuxExtractor,
    ValidationManager,
)

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
    # Managers
    "AnimationCurveManager",
    "BatchOperationManager",
    "CameraManager",
    "CollectionManager",
    "CoordinateSystemManager",
    "LayerCompositionManager",
    "MaterialManager",
    "NamespaceEditor",
    "OpenExecManager",
    "PayloadManager",
    "PrimSelectionManager",
    "SceneComparator",
    "SceneSearchManager",
    "StageVariableManager",
    "UndoRedoManager",
    "VariantManager",
    # Converters
    "USDConverter",
    "ConversionOptions",
    # Utils
    "AnnotationManager",
    "BookmarkManager",
    "ColorSpaceManager",
    "HelpSystem",
    "HelpDialog",
    "LightVisualization",
    "PerformanceProfiler",
    "PipelineIntegration",
    "ProgressReporter",
    "ProgressDialogManager",
    "RecentFilesManager",
    "UsdLuxExtractor",
    "ValidationManager",
    # Config
    "AppConfig",
    # Multi-viewport
    "MultiViewportWidget",
]
