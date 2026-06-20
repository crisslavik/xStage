# Changelog

## [Unreleased]

### Added
- **Logging infrastructure** (`src/xstage/logging_config.py`): centralized
  `get_logger()` / idempotent `configure_logging()` with env-driven level
  (`$XSTAGE_LOG_LEVEL`), optional file output, and root-logger-safe behavior so
  xStage is a good citizen when imported into host DCCs.
- **Command-line interface**: `xstage` now accepts a USD file argument plus
  `--version`, `--log-level`, `--log-file`, and `--platform`.
- **Engineering audit** (`AUDIT.md`): prioritized findings and roadmap.
- **Tests**: `tests/conftest.py` (session `QApplication` fixture) and
  `tests/test_infrastructure.py` (logging + CLI). Suite now 33 passed / 4
  skipped, up from a fully-broken state.
- **USD Version Detection**: Runtime USD version detection and feature flags
  - New module: `src/xstage/utils/usd_version.py`
  - Feature flags for version-specific features (light_linking, dof, etc.)
  - Helper functions: `USD_VERSION_AT_LEAST()`, `check_feature()`
  - Integrated into core modules for better maintainability

### Fixed
- Test suite was completely unrunnable (`tests/__init__.py` contained a shell
  command; widget tests aborted the process with no `QApplication`).
- `converters/adobe_converter.py` used a broken absolute import that silently
  removed `AdobeUSDConverter` from the public API.
- CI did not install `libEGL.so.1`, so PySide6 failed to import on the runner.
- `main()` force-overrode `QT_QPA_PLATFORM=xcb` (breaking Wayland/headless); it
  now respects the environment and `--platform`.

### Changed
- All 53 bare `except:` clauses converted to `except Exception:` so they no
  longer swallow `KeyboardInterrupt`/`SystemExit`.
- pytest configuration consolidated into `pytest.ini` (removed the duplicate
  `[tool.pytest.ini_options]` block that pytest was ignoring).
- Added `[project.optional-dependencies].dev` for `pip install -e .[dev]`.
- **Documentation Cleanup**: Removed 4 outdated/redundant documentation files
  - Removed `docs/xmaterial-support.md` (redundant with materialx-support.md)
  - Removed `DOCUMENTATION_CONSOLIDATION.md` (outdated)
  - Removed `CODE_ORGANIZATION_PLAN.md` (outdated)
  - Removed `MIGRATION_NOTES.md` (outdated)
  - Updated `DOCUMENTATION_INDEX.md` to reflect current structure

### Improved
- **Maintainability**: Added USD version detection for easier future updates
- **Code Organization**: Integrated version detection into light_linking_manager
- **Documentation**: Cleaner, more organized documentation structure

---
## xStage USD Viewer & Converter

All notable changes to xStage will be documented in this file.

---

## [Unreleased] - Phase 1-3 Implementation & CI Improvements

### Fixed
- **CI Workflow**: Fixed matrix configuration error (`runs-on: ${{ matrix.os }}` → `runs-on: ubuntu-22.04`)
- **CI Workflow**: Added comprehensive timeouts to prevent "operation was canceled" errors
- **CI Workflow**: Added Xvfb (X Virtual Framebuffer) for headless GUI testing
- **CI Workflow**: Improved error handling with `continue-on-error` and fallbacks
- **CI Workflow**: Optimized dependency installation (split into core/optional/dev stages)
- **CI Workflow**: Added pip caching and better progress logging
- **Tests**: Fixed all import paths to match new code structure (`xstage.core.viewer`, etc.)
- **Tests**: Expanded test suite (753 lines across 5 test files)
- **Tests**: Added tests for converters, managers, and utilities

### Added - Phase 1: Polish
- **Theme System**: Dark, Light, and High Contrast themes with persistence
- **Viewport Overlays**: FPS counter, statistics, memory usage, selection info
- **Selection Sets**: Save/load named selection groups with operations

### Added - Phase 2: Performance
- **Smart Caching**: Geometry, bounds, transform, and material caching
- **LOD System**: Automatic Level of Detail detection and switching
- **Instancing Optimization**: Instance detection and memory optimization

### Added - Phase 3: Visual Features
- **AOV Visualization**: Render Var extraction and preview UI
- **Texture/Material Preview**: Preview textures and materials on 3D geometry

### Added - Material Support
- **Blender MaterialX Support**: Added Blender shader type for MaterialX Standard Surface compatibility (stable)
- **Nuke 17 MaterialX Support**: Added Nuke 17 shader type for MaterialX Standard Surface compatibility (beta)

### Changed
- Updated viewer to integrate all new features
- Enhanced viewport with overlay support
- Improved performance with caching and LOD

### Fixed
- Viewport resize handling for overlays
- Theme application across all widgets

---

## [0.1.0] - Initial Release

### Added
- Core USD viewer with Hydra 2.0 rendering
- Format converter (8+ formats)
- Layer composition visualization
- Animation curve editor
- Material editor
- Scene search and filtering
- Camera management
- Prim selection and manipulation
- Collection editor
- Primvar editor
- Render settings editor
- Multi-viewport support
- Undo/redo system
- Scene comparison
- Batch operations
- Performance profiling
- OpenExec support
- Pipeline integration
- Annotations with drawing tools
- Recent files tracking
- Bookmarks
- Help system

---

## Version History

- **0.1.0**: Initial release with 26 core features
- **Unreleased**: Phase 1-3 implementation (8 new features)

---

*For detailed feature descriptions, see ADDED_FEATURES.md*

