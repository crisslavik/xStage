# xStage UI Improvements Roadmap
## Comparison with Omniverse & Professional DCCs

### 🎯 Priority 1: Critical UI Enhancements

#### 1. Enhanced Outliner (Like Omniverse)
**Current State:**
- Basic QTreeWidget with emoji icons
- Visibility checkboxes
- No right-click menu
- No search/filter

**Target State:**
```python
# Features to add:
- Professional icons (not emojis) using QIcon
- Right-click context menu:
  * Duplicate Prim
  * Delete Prim
  * Rename Prim
  * Create Child Prim
  * Set as Active Camera
  * Frame Selected
- Search/filter bar at top
- Type-based color coding
- Expand/collapse all
- Drag & drop reordering
- Lock/unlock toggle (eye icon)
```

**Implementation:**
- Replace emojis with QIcon from theme
- Add QLineEdit search bar above tree
- Implement QMenu for context actions
- Add QAction for common operations

#### 2. Professional Properties Panel
**Current State:**
- Basic transform controls
- Attributes shown as text

**Target State:**
```python
# Features to add:
- Tabbed interface:
  * Transform (Translate/Rotate/Scale)
  * USD Purpose (default/render/proxy/guide dropdown)
  * Variant Sets (selector UI)
  * Material Assignment (drag-drop)
  * Collections (membership editor)
  * Custom Attributes (full editor)
  * Metadata (view/edit)
- Live updates as you type
- Undo/redo support
- Validation feedback
```

#### 3. Multi-Viewport System
**Current State:**
- Single viewport

**Target State:**
```python
# Features to add:
- Quad view layout (Top/Front/Side/Perspective)
- Viewport tabs (like Maya)
- Split viewport (horizontal/vertical)
- Sync camera option
- Independent viewport settings
- Viewport presets (saved layouts)
```

#### 4. Asset Browser
**Current State:**
- File dialog only

**Target State:**
```python
# Features to add:
- Thumbnail grid view
- List view option
- Search with filters (type, date, size)
- Recent files panel
- Favorites/bookmarks
- Drag & drop to viewport
- Preview pane
- Metadata display
```

### 🎯 Priority 2: Professional Toolbar

**Current State:**
- Basic text buttons

**Target State:**
```python
# Tool groups:
1. Selection Tools:
   - Select Tool (arrow icon)
   - Lasso Select
   - Box Select

2. Transform Tools:
   - Move Tool (W)
   - Rotate Tool (E)
   - Scale Tool (R)
   - Universal Manipulator

3. Viewport Modes:
   - Shaded
   - Wireframe
   - Points
   - Bounding Box
   - Material Preview

4. View Controls:
   - Frame All
   - Frame Selected
   - Look Through Selected Camera
   - Grid Toggle
   - Axis Toggle
```

### 🎯 Priority 3: Advanced Features

#### 5. Viewport Overlays
- Grid with measurements (already have, improve)
- Selection outline
- Gizmo handles (move/rotate/scale)
- Navigation HUD (compass, axis)

#### 6. Timeline Enhancements
- Keyframe markers
- Playback range
- Time scrubbing
- Frame rate display
- Animation curves preview

#### 7. Material Preview
- Real-time material preview
- Texture viewer
- Material library browser

## 🔧 Hydra 2.0 Fixes Applied

### ✅ Fixed Issues:
1. **Scene Index Enable** - Added `SetEnableSceneIndex(True)`
2. **Storm Renderer** - Explicitly set `HdStormRendererPlugin`
3. **Camera State** - Using `SetCameraState()` API
4. **OpenGL Context** - Proper `makeCurrent()` calls
5. **Error Handling** - Better diagnostics and fallbacks

### 📋 Diagnostic Script:
Run `./scripts/diagnose_hydra.py` to check:
- USD version
- Available renderers
- OpenGL version
- Scene Index support
- Storm availability

## 📊 Implementation Timeline

### Week 1: Hydra + Core UI
- ✅ Fix Hydra 2.0 (DONE)
- Enhanced outliner with icons
- Professional properties panel

### Week 2: Multi-Viewport + Tools
- Multi-viewport system
- Professional toolbar
- Asset browser

### Week 3: Polish
- Viewport overlays
- Timeline enhancements
- Material preview

## 🎨 UI Design Principles

1. **Consistency**: Match Omniverse/Maya/Blender patterns
2. **Discoverability**: Clear icons, tooltips, shortcuts
3. **Efficiency**: Keyboard shortcuts for power users
4. **Feedback**: Visual feedback for all actions
5. **Performance**: Responsive UI even with large scenes
