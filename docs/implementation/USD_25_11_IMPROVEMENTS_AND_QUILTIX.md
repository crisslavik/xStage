# USD 25.11 Improvements & QuiltiX Integration Plan
## Enhancing xStage with Latest USD Features and MaterialX Editor

This document outlines improvements based on **USD 25.11** features and **QuiltiX** integration for enhanced lighting, camera, and material workflows.

**Last Updated**: After viewport metrics implementation  
**USD Version**: 25.11  
**Reference**: [OpenUSD Release Documentation](https://openusd.org/release/index.html)

---

## 🎯 USD 25.11 Features to Implement

### **1. Enhanced Light Features** 🔴 **HIGH PRIORITY**

#### **Current Status:**
- ✅ Basic light extraction (UsdLux support)
- ✅ Light type detection (Distant, Sphere, Rect, etc.)
- ✅ Basic properties (intensity, color, exposure)
- ⚠️ Light linking (extracted but not interactive)
- ❌ Look-through lights
- ❌ Interactive light manipulation
- ❌ Light visualization in viewport

#### **USD 25.11 Enhancements to Add:**

**1.1 Light Linking UI** 🔴
- **What**: Interactive UI for light linking (which lights affect which objects)
- **Implementation**: 
  ```python
  # src/xstage/managers/light_linking_manager.py
  class LightLinkingManager:
      def get_light_links(self, light_prim):
          # Get LightListAPI relationships
          light_list_api = UsdLux.LightListAPI(light_prim)
          return light_list_api.GetLightFilterLinkRel().GetTargets()
      
      def set_light_link(self, light_prim, target_prim, enable=True):
          # Add/remove light links
          pass
  ```
- **UI**: Light linking panel showing light-object relationships
- **Effort**: 1-2 weeks

**1.2 Look-Through Lights** 🟡
- **What**: View scene from light's perspective (like Maya)
- **Implementation**: Use light transform as camera view
- **UI**: "Look Through Light" option in light context menu
- **Effort**: 3-5 days

**1.3 Interactive Light Manipulation** 🟡
- **What**: Real-time light editing in viewport
- **Features**:
  - Gizmo for light position/orientation
  - Sliders for intensity, color, exposure
  - Color temperature picker
  - Real-time preview
- **Effort**: 2-3 weeks

**1.4 Enhanced Light Visualization** 🟡
- **What**: Visual representation of lights in viewport
- **Features**:
  - Light icons (sphere, rect, disk, etc.)
  - Light direction indicators
  - Cone angles for spot lights
  - Intensity visualization
- **Effort**: 1-2 weeks

**1.5 Light Filter Support** 🟡
- **What**: Support for UsdLux.LightFilter
- **Features**:
  - Light filter extraction
  - Filter property editing
  - Filter visualization
- **Effort**: 1 week

---

### **2. Enhanced Camera Features** 🔴 **HIGH PRIORITY**

#### **Current Status:**
- ✅ Basic camera extraction
- ✅ Camera switching
- ✅ Camera property editing
- ⚠️ Basic camera properties (focal length, aperture, etc.)
- ❌ Advanced camera features (depth of field, motion blur, etc.)
- ❌ Camera animation preview
- ❌ Stereo camera support

#### **USD 25.11 Enhancements to Add:**

**2.1 Depth of Field (DOF)** 🔴
- **What**: Interactive depth of field controls
- **USD 25.11 Support**: `UsdGeom.Camera` has `focusDistance` and `fStop`
- **Implementation**:
  ```python
  # Enhance CameraManager
  def set_depth_of_field(self, camera_prim, focus_distance, f_stop):
      camera = UsdGeom.Camera(camera_prim)
      camera.GetFocusDistanceAttr().Set(focus_distance)
      camera.GetFStopAttr().Set(f_stop)
  ```
- **UI**: DOF controls in camera editor
- **Viewport**: Visual DOF preview (optional)
- **Effort**: 1 week

**2.2 Motion Blur Support** 🟡
- **What**: Camera motion blur settings
- **USD 25.11 Support**: `UsdRender.RenderSettings` has motion blur controls
- **Features**:
  - Shutter open/close times
  - Motion blur preview
- **Effort**: 1 week

**2.3 Stereo Camera Support** 🟡
- **What**: Support for stereo camera rigs
- **USD 25.11 Support**: Stereo camera metadata
- **Features**:
  - Left/right eye switching
  - Stereo camera detection
  - Inter-ocular distance controls
- **Effort**: 1-2 weeks

**2.4 Camera Animation Preview** 🟡
- **What**: Preview camera animation in viewport
- **Features**:
  - Camera path visualization
  - Keyframe display
  - Animation scrubbing
- **Effort**: 1 week

**2.5 Advanced Camera Properties** 🟡
- **What**: Additional camera features from USD 25.11
- **Features**:
  - Clipping planes (near/far)
  - Projection type (perspective/orthographic)
  - Overscan
  - Shutter controls
- **Effort**: 3-5 days

---

### **3. MaterialX & Shader Enhancements** 🔴 **HIGH PRIORITY**

#### **Current Status:**
- ✅ MaterialX Standard Surface support
- ✅ Material extraction and editing
- ✅ Material preview widget
- ⚠️ Basic material editing
- ❌ Advanced MaterialX node editing
- ❌ Shader network visualization
- ❌ Material library

#### **USD 25.11 Enhancements to Add:**

**3.1 Enhanced MaterialX Node Support** 🔴
- **What**: Full MaterialX node graph editing
- **USD 25.11 Support**: Enhanced MaterialX schemas
- **Features**:
  - Node graph editor
  - Node property editing
  - Node connections
  - MaterialX node library
- **Effort**: 2-3 weeks

**3.2 Shader Network Visualization** 🟡
- **What**: Visual representation of shader networks
- **Features**:
  - Node graph view
  - Connection visualization
  - Node search/filter
- **Effort**: 1-2 weeks

**3.3 Material Library** 🟡
- **What**: Library of reusable materials
- **Features**:
  - Material browser
  - Material thumbnails
  - Material import/export
  - Material categories
- **Effort**: 1-2 weeks

---

### **4. Render Settings & AOVs** 🟡 **MEDIUM PRIORITY**

#### **Current Status:**
- ✅ Basic render settings extraction
- ✅ AOV visualization UI
- ⚠️ Render settings editing
- ❌ Multi-pass render support
- ❌ Render product configuration

#### **USD 25.11 Enhancements to Add:**

**4.1 RenderSettings Enhancement** 🟡
- **What**: Full UsdRender.RenderSettings support
- **USD 25.11 Support**: Enhanced RenderSettings schema
- **Features**:
  - Render product configuration
  - Multi-pass render setup
  - RenderVar management
  - Render pass configuration
- **Effort**: 1-2 weeks

**4.2 AOV Export** 🟡
- **What**: Export AOVs to images
- **Features**:
  - AOV selection
  - Export format selection
  - Batch export
- **Effort**: 1 week

---

## 🎨 QuiltiX Integration

### **What is QuiltiX?**

**QuiltiX** is an open-source MaterialX editor designed for creating and editing materials for USD assets. It features:
- **Hydra-based viewport** - Uses Hydra renderers for preview
- **MaterialX node editing** - Visual node-based material editor
- **Production renderer support** - Works with Arnold, Karma, etc.
- **Pipeline integration** - Designed for studio pipelines

**References:**
- [QuiltiX on PyPI](https://pypi.org/project/quiltix/)
- [QuiltiX Documentation](https://prism-pipeline.com/quiltix/)

---

### **Integration Complexity: 🟡 MEDIUM**

#### **Why It's Feasible:**

1. **Python-Based** ✅
   - QuiltiX is Python-based (like xStage)
   - Easy to integrate as a module or subprocess

2. **Hydra Support** ✅
   - QuiltiX uses Hydra (xStage already supports Hydra)
   - Can share Hydra renderer configuration

3. **USD/MaterialX Integration** ✅
   - QuiltiX works with USD stages
   - MaterialX support is already in xStage
   - Compatible data formats

4. **Designed for Integration** ✅
   - QuiltiX is built to be integrated
   - Uses environment variables for configuration
   - Can be embedded or launched separately

---

### **Integration Approaches**

#### **Option 1: Embedded Integration** 🟡 **RECOMMENDED**

**How it works:**
- Embed QuiltiX as a dock widget in xStage
- Share USD stage with QuiltiX
- Synchronize material changes

**Implementation:**
```python
# src/xstage/ui/editors/quiltix_editor_ui.py
from quiltix import QuiltiXEditor

class QuiltiXEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.quiltix_editor = QuiltiXEditor()
        # Embed QuiltiX UI
        self.quiltix_widget = self.quiltix_editor.get_widget()
        
    def set_stage(self, stage):
        # Share USD stage with QuiltiX
        self.quiltix_editor.set_stage(stage)
```

**Pros:**
- ✅ Seamless integration
- ✅ Shared USD stage
- ✅ Real-time material updates
- ✅ Single application

**Cons:**
- ⚠️ Requires QuiltiX API for embedding
- ⚠️ May need QuiltiX modifications

**Effort**: 2-3 weeks

---

#### **Option 2: External Launch** 🟢 **EASIEST**

**How it works:**
- Launch QuiltiX as separate process
- Pass USD file path
- Use file watching for synchronization

**Implementation:**
```python
# src/xstage/managers/quiltix_manager.py
import subprocess
import os

class QuiltiXManager:
    def launch_quiltix(self, usd_filepath):
        # Launch QuiltiX with USD file
        env = os.environ.copy()
        env['PXR_PLUGINPATH_NAME'] = self.get_hydra_plugin_path()
        subprocess.Popen(['quiltix', usd_filepath], env=env)
```

**Pros:**
- ✅ Simple implementation
- ✅ No QuiltiX modifications needed
- ✅ Independent processes
- ✅ Easy to maintain

**Cons:**
- ⚠️ Separate window
- ⚠️ Manual synchronization
- ⚠️ Less integrated experience

**Effort**: 3-5 days

---

#### **Option 3: Hybrid Approach** 🟡 **BALANCED**

**How it works:**
- Launch QuiltiX in embedded mode if possible
- Fallback to external launch if embedding fails
- Use IPC (Inter-Process Communication) for synchronization

**Implementation:**
```python
class QuiltiXManager:
    def __init__(self):
        self.embedded_mode = self._check_embedding_support()
    
    def open_material_editor(self, material_prim):
        if self.embedded_mode:
            return self._launch_embedded(material_prim)
        else:
            return self._launch_external(material_prim)
```

**Pros:**
- ✅ Best of both worlds
- ✅ Fallback option
- ✅ Flexible

**Cons:**
- ⚠️ More complex
- ⚠️ Two code paths

**Effort**: 1-2 weeks

---

### **QuiltiX Integration Requirements**

#### **Dependencies:**
```python
# requirements.txt
quiltix>=1.0.0  # QuiltiX MaterialX editor
```

#### **Environment Variables:**
```python
# Setup for QuiltiX
os.environ['PXR_PLUGINPATH_NAME'] = '/path/to/hydra/plugins'
os.environ['PXR_MTLX_STDLIB_SEARCH_PATHS'] = '/path/to/materialx/libraries'
```

#### **Hydra Renderer Configuration:**
- QuiltiX needs Hydra renderer plugins
- xStage already supports Hydra
- Can share renderer configuration

---

### **QuiltiX Integration Steps**

#### **Phase 1: Basic Integration (1 week)**
1. ✅ Add QuiltiX to requirements
2. ✅ Create QuiltiXManager
3. ✅ Add "Open in QuiltiX" menu option
4. ✅ Launch QuiltiX with USD file
5. ✅ Test basic functionality

#### **Phase 2: Enhanced Integration (1-2 weeks)**
1. ✅ Embed QuiltiX widget (if possible)
2. ✅ Share USD stage
3. ✅ Material change synchronization
4. ✅ Material selection sync

#### **Phase 3: Advanced Features (1-2 weeks)**
1. ✅ Material library integration
2. ✅ Material preview sync
3. ✅ Batch material editing
4. ✅ Material export/import

---

### **QuiltiX Integration Challenges**

#### **1. Embedding QuiltiX UI**
- **Challenge**: QuiltiX may not have embedding API
- **Solution**: Use external launch or request embedding API

#### **2. Stage Synchronization**
- **Challenge**: Keeping USD stage in sync between xStage and QuiltiX
- **Solution**: File watching or shared memory

#### **3. Hydra Renderer Configuration**
- **Challenge**: Ensuring both use same Hydra renderer
- **Solution**: Share environment variables and plugin paths

#### **4. Material Selection**
- **Challenge**: Syncing selected material between apps
- **Solution**: Use USD stage metadata or file-based communication

---

## 📋 Implementation Priority

### **Priority 1: High Impact (4-6 weeks)**
1. **Light Linking UI** (1-2 weeks) 🔴
2. **Look-Through Lights** (3-5 days) 🔴
3. **Depth of Field** (1 week) 🔴
4. **QuiltiX Basic Integration** (1 week) 🔴

### **Priority 2: Medium Impact (3-4 weeks)**
5. **Interactive Light Manipulation** (2-3 weeks) 🟡
6. **Enhanced Light Visualization** (1-2 weeks) 🟡
7. **Camera Animation Preview** (1 week) 🟡
8. **QuiltiX Enhanced Integration** (1-2 weeks) 🟡

### **Priority 3: Nice to Have (2-3 weeks)**
9. **Light Filter Support** (1 week) 🟢
10. **Stereo Camera Support** (1-2 weeks) 🟢
11. **Material Library** (1-2 weeks) 🟢
12. **QuiltiX Advanced Features** (1-2 weeks) 🟢

---

## 🎯 Recommended Implementation Plan

### **Phase 1: Core Enhancements (Weeks 1-4)**
- Light Linking UI
- Look-Through Lights
- Depth of Field
- QuiltiX Basic Integration

### **Phase 2: Interactive Features (Weeks 5-8)**
- Interactive Light Manipulation
- Enhanced Light Visualization
- Camera Animation Preview
- QuiltiX Enhanced Integration

### **Phase 3: Advanced Features (Weeks 9-12)**
- Light Filter Support
- Stereo Camera Support
- Material Library
- QuiltiX Advanced Features

---

## 📚 USD 25.11 Reference Features

Based on [OpenUSD 25.11 Documentation](https://openusd.org/release/index.html):

### **Light Features (UsdLux):**
- ✅ Light Linking (LightListAPI)
- ✅ Shadow API (ShadowAPI)
- ✅ Shaping API (ShapingAPI)
- ✅ Light Filters (LightFilter)
- ✅ Mesh Lights (MeshLightAPI)
- ✅ Volume Lights (VolumeLightAPI)

### **Camera Features (UsdGeom.Camera):**
- ✅ Depth of Field (focusDistance, fStop)
- ✅ Clipping Planes (nearClipPlane, farClipPlane)
- ✅ Projection Types (perspective, orthographic)
- ✅ Aperture Controls (horizontalAperture, verticalAperture)
- ✅ Shutter Controls (shutterOpen, shutterClose)

### **Render Features (UsdRender):**
- ✅ RenderSettings
- ✅ RenderProduct
- ✅ RenderPass
- ✅ RenderVar (AOVs)
- ✅ Multi-pass rendering

---

## 🚀 Quick Wins (High Impact, Low Effort)

1. **Look-Through Lights** (3-5 days)
   - Simple camera view from light position
   - High visual impact

2. **Depth of Field UI** (1 week)
   - Add DOF controls to camera editor
   - Uses existing USD 25.11 support

3. **QuiltiX External Launch** (3-5 days)
   - Simple subprocess launch
   - Immediate material editing capability

---

## 💡 Conclusion

### **USD 25.11 Improvements:**
- **Light features** are the highest priority
- **Camera enhancements** add significant value
- **MaterialX improvements** complement QuiltiX integration

### **QuiltiX Integration:**
- **Feasibility**: 🟡 **MEDIUM** - Definitely doable
- **Complexity**: Moderate (Python-based, designed for integration)
- **Recommended Approach**: Start with external launch, move to embedded if possible
- **Timeline**: 1-2 weeks for basic, 3-4 weeks for full integration

### **Benefits:**
- ✅ Professional material editing (QuiltiX)
- ✅ Enhanced lighting workflows
- ✅ Better camera controls
- ✅ Industry-standard tools
- ✅ Production-ready features

---

## 📖 References

- **OpenUSD 25.11**: https://openusd.org/release/index.html
- **QuiltiX**: https://pypi.org/project/quiltix/
- **QuiltiX Documentation**: https://prism-pipeline.com/quiltix/
- **USD UsdLux**: https://openusd.org/release/api/usd_lux_page_front.html
- **USD UsdGeom.Camera**: https://openusd.org/release/api/class_usd_geom_camera.html
- **USD UsdRender**: https://openusd.org/release/api/usd_render_page_front.html

---

*This document will be updated as features are implemented.*

