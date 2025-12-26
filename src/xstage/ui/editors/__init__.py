"""
Editor UI widgets
"""

# Import all editor widgets
try:
    from .animation_curve_ui import AnimationCurveEditorWidget
    from .annotations_ui import AnnotationsWidget
    from .aov_visualization_ui import AOVVisualizationWidget
    from .camera_manager_ui import CameraManagerWidget
    from .collection_editor_ui import CollectionEditorWidget
    from .converter_ui import ConverterDialog
    from .layer_composition_ui import LayerCompositionWidget
    from .material_editor_ui import MaterialEditorWidget
    from .openexec_ui import OpenExecWidget
    from .prim_selection_ui import PrimPropertiesWidget
    from .primvar_editor_ui import PrimvarEditorWidget
    from .render_settings_editor_ui import RenderSettingsEditorWidget
    from .scene_comparison_ui import SceneComparisonWidget
    from .scene_search_ui import SceneSearchWidget
    from .stage_variables_ui import StageVariablesWidget
    
    __all__ = [
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
    ]
except ImportError as e:
    __all__ = []
    print(f"Warning: Some UI widgets could not be imported: {e}")

