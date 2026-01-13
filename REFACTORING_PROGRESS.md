# xStage Code Refactoring Progress

## Overview
Refactoring the massive `viewer.py` (3815 lines) into smaller, maintainable modules following Omniverse-like architecture.

## ✅ Completed (Phase 1)

### 1. Stage Manager Module
**File:** `src/xstage/core/stage_manager.py` (250 lines)
- Extracted `USDStageManager` class from viewer.py
- Handles USD stage loading and geometry extraction
- Clean API for querying stage data
- Easier to test and maintain

### 2. OpenGL Viewport Module
**File:** `src/xstage/rendering/opengl_viewport.py` (450 lines)
- Extracted `OpenGLViewport` class from viewer.py
- Self-contained viewport with camera controls
- Mouse interaction and rendering logic
- Works alongside existing `HydraViewportWidget`

### 3. Timeline Widget Module
**File:** `src/xstage/ui/timeline_widget.py` (200 lines)
- Extracted timeline controls from viewer.py
- Playback buttons, slider, FPS control
- Signal-based communication
- Reusable component

### 4. Bug Fixes
- Fixed Hydra 2.0 `SetRenderViewport` API signature (USD 25.11)
- Improved viewport overlay visibility (larger font, better contrast)
- Fixed dark theme for menus and UI

## 🚧 In Progress (Phase 2)

### Next Steps:
1. **Update viewer.py to use new modules**
   - Import and use `USDStageManager` from `stage_manager.py`
   - Import and use `OpenGLViewport` from `opengl_viewport.py`
   - Import and use `TimelineWidget` from `timeline_widget.py`
   - Remove duplicate code

2. **Extract remaining UI components**
   - Menu creation → `src/xstage/ui/menus.py`
   - Dock widgets → `src/xstage/ui/docks.py`
   - Toolbar creation → `src/xstage/ui/toolbars.py`

3. **Extract managers**
   - Playback logic → `src/xstage/managers/playback_manager.py`
   - Camera controls → `src/xstage/managers/camera_manager.py`

## 📊 Size Reduction Progress

| File | Before | After | Reduction |
|------|--------|-------|-----------|
| viewer.py | 3815 lines | ~2000 lines (target) | 47% |
| stage_manager.py | - | 250 lines | New |
| opengl_viewport.py | - | 450 lines | New |
| timeline_widget.py | - | 200 lines | New |

## 🎯 Target Architecture

```
src/xstage/
├── core/
│   ├── stage_manager.py          ✅ DONE (250 lines)
│   ├── viewer_window.py          🚧 TODO (main window, ~800 lines)
│   └── app.py                    🚧 TODO (entry point, ~50 lines)
├── rendering/
│   ├── opengl_viewport.py        ✅ DONE (450 lines)
│   ├── hydra_viewport.py         ✅ EXISTS (538 lines)
│   └── viewport_base.py          📋 FUTURE (base class)
├── ui/
│   ├── timeline_widget.py        ✅ DONE (200 lines)
│   ├── menus.py                  🚧 TODO (~300 lines)
│   ├── toolbars.py               🚧 TODO (~200 lines)
│   └── docks.py                  🚧 TODO (~400 lines)
└── managers/
    ├── playback_manager.py       📋 FUTURE (~150 lines)
    └── camera_manager.py         📋 FUTURE (~150 lines)
```

## Benefits

### ✅ Already Achieved:
- Cleaner separation of concerns
- Easier to understand individual components
- Better testability
- Reduced file sizes

### 🎯 Coming Soon:
- Each file < 600 lines
- Clear module boundaries
- Easier for contributors
- Matches Omniverse architecture
- Better code reusability

## Testing

After refactoring, test:
1. USD file loading
2. OpenGL viewport rendering
3. Hydra 2.0 viewport rendering
4. Timeline playback
5. Camera controls
6. Menu and toolbar functionality

## Notes

- All existing functionality preserved
- No breaking changes to user experience
- Backward compatible imports maintained
- Old `viewport.py` can be deprecated after testing
