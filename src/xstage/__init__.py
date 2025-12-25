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
from .converter_ui import ConverterDialog
from .config import AppConfig

# New feature modules
from .usd_lux_support import UsdLuxExtractor
from .collections import CollectionManager
from .variants import VariantManager
from .materials import MaterialManager
from .validation import USDValidator
from .payloads import PayloadManager
from .color_space import ColorSpaceManager

# High priority feature modules
from .hydra_viewport import HydraViewportWidget
from .layer_composition import LayerCompositionManager
from .layer_composition_ui import LayerCompositionWidget
from .animation_curves import AnimationCurveManager
from .animation_curve_ui import AnimationCurveEditorWidget
from .material_editor_ui import MaterialEditorWidget
from .scene_search import SceneSearchManager
from .scene_search_ui import SceneSearchWidget

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
    # High priority features
    "HydraViewportWidget",
    "LayerCompositionManager",
    "LayerCompositionWidget",
    "AnimationCurveManager",
    "AnimationCurveEditorWidget",
    "MaterialEditorWidget",
    "SceneSearchManager",
    "SceneSearchWidget",
    # Medium priority features
    "CameraManager",
    "CameraManagerWidget",
    "PrimSelectionManager",
    "PrimPropertiesWidget",
    "LightVisualization",
    "CollectionEditorWidget",
    "PrimvarEditorWidget",
    "RenderSettingsEditorWidget",
    "CoordinateSystemManager",
    "NamespaceEditor",
    "StageVariableManager",
    "StageVariablesWidget",
    # Converter and pipeline
    "USDConverter",
    "ConversionOptions",
    "ConverterDialog",
    "PipelineIntegration",
    # Advanced features
    "MultiViewportWidget",
    "UndoRedoManager",
    "SceneComparator",
    "SceneComparisonWidget",
    "BatchOperationManager",
    "PerformanceProfiler",
    "HelpSystem",
    "ProgressReporter",
    # OpenExec
    "OpenExecManager",
    "OpenExecWidget",
]