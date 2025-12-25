# Code Organization Plan
## Reorganizing xStage Source Code

Current structure has all Python files in `src/xstage/` (40+ files). This plan proposes a better organization.

---

## 📁 Proposed Structure

```
src/xstage/
├── __init__.py                 # Main exports
├── config.py                   # Configuration
│
├── core/                       # Core functionality
│   ├── __init__.py
│   ├── viewer.py              # Main viewer window
│   ├── stage_manager.py       # USD stage management
│   └── viewport.py            # Base viewport
│
├── rendering/                  # Rendering systems
│   ├── __init__.py
│   ├── hydra_viewport.py      # Hydra 2.0 rendering
│   └── opengl_viewport.py     # OpenGL fallback
│
├── ui/                        # UI widgets and dialogs
│   ├── __init__.py
│   ├── widgets/               # Reusable widgets
│   │   ├── __init__.py
│   │   ├── orientation.py     # Axis orientation widget
│   │   └── timeline.py        # Timeline widget
│   │
│   └── editors/               # Editor widgets
│       ├── __init__.py
│       ├── animation_curve_ui.py
│       ├── camera_manager_ui.py
│       ├── collection_editor_ui.py
│       ├── layer_composition_ui.py
│       ├── material_editor_ui.py
│       ├── openexec_ui.py
│       ├── prim_selection_ui.py
│       ├── primvar_editor_ui.py
│       ├── render_settings_editor_ui.py
│       ├── scene_comparison_ui.py
│       ├── scene_search_ui.py
│       └── stage_variables_ui.py
│
├── managers/                  # Feature managers
│   ├── __init__.py
│   ├── animation_curves.py
│   ├── batch_operations.py
│   ├── camera_manager.py
│   ├── collections.py
│   ├── coordinate_systems.py
│   ├── layer_composition.py
│   ├── materials.py
│   ├── namespace_editing.py
│   ├── openexec_support.py
│   ├── payloads.py
│   ├── prim_selection.py
│   ├── scene_comparison.py
│   ├── scene_search.py
│   ├── stage_variables.py
│   ├── undo_redo.py
│   └── variants.py
│
├── converters/                # Format conversion
│   ├── __init__.py
│   ├── converter.py           # Main converter
│   ├── converter_ui.py        # Converter UI
│   └── adobe_converter.py     # Adobe-specific
│
├── utils/                     # Utilities
│   ├── __init__.py
│   ├── color_space.py
│   ├── help_system.py
│   ├── light_visualization.py
│   ├── performance_profiler.py
│   ├── pipeline_integration.py
│   ├── progress_manager.py
│   ├── usd_lux_support.py
│   └── validation.py
│
└── plugins/                   # Plugin system (future)
    ├── __init__.py
    └── base.py
```

---

## 🔄 Migration Plan

### Phase 1: Create New Structure
1. Create new directories
2. Move files to appropriate locations
3. Update imports in `__init__.py` files

### Phase 2: Update Imports
1. Update all internal imports
2. Update external imports
3. Test that everything still works

### Phase 3: Cleanup
1. Remove old files
2. Update documentation
3. Update tests

---

## 📝 Import Updates Needed

### Before:
```python
from xstage.viewer import USDViewerWindow
from xstage.hydra_viewport import HydraViewportWidget
from xstage.materials import MaterialManager
```

### After:
```python
from xstage.core.viewer import USDViewerWindow
from xstage.rendering.hydra_viewport import HydraViewportWidget
from xstage.managers.materials import MaterialManager
```

---

## ✅ Benefits

1. **Better Organization** - Related files grouped together
2. **Easier Navigation** - Clear structure, easier to find files
3. **Scalability** - Easy to add new features in right place
4. **Maintainability** - Clear separation of concerns
5. **Professional** - Industry-standard structure

---

## ⚠️ Considerations

1. **Backward Compatibility** - May need to maintain old imports temporarily
2. **Testing** - All tests need to be updated
3. **Documentation** - API docs need updating
4. **Migration Time** - Estimated 1-2 days

---

## 🎯 Recommendation

**Yes, reorganize!** The current flat structure with 40+ files is hard to navigate. The proposed structure:
- Groups related functionality
- Makes codebase more maintainable
- Follows Python best practices
- Scales better for future growth

**Suggested Timeline**: 
- Plan: 1 day
- Implementation: 1-2 days
- Testing: 1 day
- **Total: 3-4 days**

---

*This reorganization will make xStage more professional and maintainable.*

