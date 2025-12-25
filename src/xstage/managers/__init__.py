"""
Feature managers
"""

try:
    from .animation_curves import AnimationCurveManager
    from .batch_operations import BatchOperationManager
    from .camera_manager import CameraManager
    from .collections import CollectionManager
    from .coordinate_systems import CoordinateSystemManager
    from .layer_composition import LayerCompositionManager
    from .materials import MaterialManager
    from .namespace_editing import NamespaceEditor
    from .openexec_support import OpenExecManager
    from .payloads import PayloadManager
    from .prim_selection import PrimSelectionManager
    from .scene_comparison import SceneComparator
    from .scene_search import SceneSearchManager
    from .stage_variables import StageVariableManager
    from .undo_redo import UndoRedoManager
    from .variants import VariantManager
    
    __all__ = [
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
    ]
except ImportError as e:
    __all__ = []
    print(f"Warning: Some managers could not be imported: {e}")

