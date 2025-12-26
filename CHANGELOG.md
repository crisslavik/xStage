# Changelog
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
- **Blender MaterialX Support**: Added Blender shader type for future-proof material compatibility (beta)

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

