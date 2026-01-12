# xStage UI Improvements & Hydra 2.0 Fix

## 🔍 Current State Analysis

### ✅ What xStage Has
- Basic USD viewer with OpenGL fallback
- Scene hierarchy tree (basic)
- Properties panel (limited)
- Material editor
- Animation curve editor
- Light management
- OCIO color management
- Theme support

### ❌ What's Missing (vs Omniverse/Professional DCCs)

#### 1. **Multi-Viewport System**
- **Current**: Single viewport
- **Needed**: Quad view (Top/Front/Side/Perspective) like Blender/Maya
- **Priority**: High

#### 2. **Enhanced Outliner**
- **Current**: Basic QTreeWidget with checkboxes
- **Needed**:
  - Type icons (mesh, camera, light, xform)
  - Visibility toggle (eye icon)
  - Lock toggle
  - Color coding by prim type
  - Right-click context menu
  - Search/filter bar
  - Drag & drop reordering
- **Priority**: High

#### 3. **Professional Properties Panel**
- **Current**: Basic transform + attributes text view
- **Needed**:
  - Full USD attribute editor (like Omniverse)
  - Purpose selector (default/render/proxy/guide)
  - Variant sets UI
  - Custom attributes editor
  - Material assignment
  - Collection membership
- **Priority**: High

#### 4. **Asset Browser**
- **Current**: File dialog only
- **Needed**:
  - Thumbnail grid view
  - Drag & drop to viewport
  - Search with filters
  - Recent files panel
  - Favorites/bookmarks
- **Priority**: Medium

#### 5. **Professional Toolbar**
- **Current**: Basic buttons
- **Needed**:
  - Tool icons (Select, Move, Rotate, Scale)
  - Viewport mode buttons (Shaded/Wireframe/Points)
  - Snapping controls
  - Grid toggle
  - Axis toggle
- **Priority**: Medium

#### 6. **Viewport Tabs**
- **Current**: Single viewport
- **Needed**: Tabbed viewports (like Maya)
- **Priority**: Low

## 🔧 Hydra 2.0 Issues & Fixes

### Issue 1: Missing Scene Index Enable
**Problem**: Hydra 2.0 requires explicit Scene Index enable
**Fix**: Add `SetEnableSceneIndex(True)` in `initializeGL()`

### Issue 2: No Renderer Plugin Selection
**Problem**: Not explicitly setting Storm renderer
**Fix**: Call `SetRendererPlugin('HdStormRendererPlugin')`

### Issue 3: Camera State Not Set Properly
**Problem**: Using old Render() API without camera state
**Fix**: Use `SetCameraState()` before rendering

### Issue 4: OpenGL Context Timing
**Problem**: Engine created before GL context is ready
**Fix**: Ensure `makeCurrent()` is called first

## 📋 Implementation Priority

### Phase 1 (Critical - Week 1)
1. Fix Hydra 2.0 rendering
2. Enhanced outliner with icons
3. Multi-viewport (at least 2 views)

### Phase 2 (High Priority - Week 2)
4. Professional properties panel
5. Asset browser
6. Professional toolbar

### Phase 3 (Nice to Have - Week 3)
7. Viewport tabs
8. Advanced snapping
9. Custom viewport layouts
