"""
Feature managers
"""

try:
    from .animation_curves import AnimationCurveManager
    from .aov_manager import AOVManager, AOVInfo, AOVDisplayMode
    from .batch_operations import BatchOperationManager
    from .camera_manager import CameraManager
    from .collections import CollectionManager
    from .coordinate_systems import CoordinateSystemManager
    from .instancing_manager import InstancingManager, InstanceInfo, InstanceMode
    from .layer_composition import LayerCompositionManager
    from .lod_manager import LODManager, LODLevel, LODMode
    from .materials import MaterialManager
    from .namespace_editing import NamespaceEditor
    from .openexec_support import OpenExecManager
    from .payloads import PayloadManager
    from .prim_selection import PrimSelectionManager
    from .scene_comparison import SceneComparator
    from .scene_search import SceneSearchManager
    from .selection_sets import SelectionSetManager, SelectionSet, SelectionSetOperation
    from .stage_variables import StageVariableManager
    from .undo_redo import UndoRedoManager
    from .variants import VariantManager
    
    __all__ = [
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
    ]
except ImportError as e:
    __all__ = []
    print(f"Warning: Some managers could not be imported: {e}")

