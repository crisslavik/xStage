# Migration Notes - Code Reorganization

## Overview
The xStage codebase has been reorganized into a modular structure for better maintainability and scalability.

## New Structure

```
src/xstage/
├── core/              # Core viewer and stage management
├── rendering/         # Rendering systems (Hydra, OpenGL)
├── ui/                # UI components
│   ├── widgets/       # Reusable widgets
│   └── editors/      # Editor UI widgets
├── managers/          # Feature managers
├── converters/        # Format conversion
├── utils/             # Utilities and helpers
└── plugins/           # Plugin system (future)
```

## Import Changes

### Before
```python
from xstage.viewer import USDViewerWindow
from xstage.hydra_viewport import HydraViewportWidget
from xstage.materials import MaterialManager
```

### After
```python
from xstage.core.viewer import USDViewerWindow
from xstage.rendering.hydra_viewport import HydraViewportWidget
from xstage.managers.materials import MaterialManager
```

## Entry Point
The console script entry point has been updated:
- **Before**: `xstage.viewer:main`
- **After**: `xstage.core.viewer:main`

## Backward Compatibility
The main `xstage.__init__.py` still exports all major classes, so existing code using:
```python
from xstage import USDViewerWindow
```
will continue to work.

## Migration Checklist
- [x] Files moved to new structure
- [x] All imports updated
- [x] Entry points updated
- [x] __init__.py files created
- [ ] Documentation updated (in progress)
- [ ] Tests updated (if needed)

## Benefits
1. **Better Organization** - Related files grouped together
2. **Easier Navigation** - Clear separation of concerns
3. **Scalability** - Easy to add new features
4. **Maintainability** - Easier to find and modify code

