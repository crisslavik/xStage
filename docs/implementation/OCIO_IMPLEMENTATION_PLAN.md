# OpenColorIO (OCIO) Integration Plan
## Color-Accurate Asset Review for xStage

This document outlines the implementation plan for OpenColorIO (OCIO) integration in xStage, focused on **asset review workflows**.

**Priority**: 🔴 **HIGHEST** - Required for color-accurate asset review  
**Effort**: 2-3 weeks  
**Focus**: Asset review (not shot/sequence review or color grading)

---

## 🎯 Goals

### **Primary Goal**
Enable color-accurate viewing of USD assets in xStage, ensuring colors match other VFX tools (Nuke, Houdini, Maya, Blender).

### **What We Need**
- ✅ Automatic color space detection from USD
- ✅ OCIO config file support (ACES, custom configs)
- ✅ Color space conversion for viewport rendering
- ✅ Color space information display
- ✅ Consistent color management across pipeline

### **What We DON'T Need** (Asset Review Focus)
- ❌ Color grading tools (not needed for asset review)
- ❌ LUT application (not needed for asset review)
- ❌ Exposure/gamma controls (not needed for asset review)
- ❌ Shot/sequence color workflows (asset review only)

---

## 📋 Implementation Plan

### **Phase 1: Dependencies & Setup (Day 1)**

1. **Add PyOpenColorIO to requirements**
   ```python
   # requirements.txt
   PyOpenColorIO>=2.2.0  # OCIO Python bindings
   ```

2. **Create OCIO Manager Module**
   ```python
   # src/xstage/utils/ocio_manager.py
   """
   OpenColorIO (OCIO) Integration for Color-Accurate Asset Review
   """
   ```

---

### **Phase 2: OCIO Manager Implementation (Days 2-5)**

#### **2.1 Core OCIO Manager Class**

```python
# src/xstage/utils/ocio_manager.py

from typing import Optional, Dict, Tuple
import numpy as np

try:
    import PyOpenColorIO as ocio
    OCIO_AVAILABLE = True
except ImportError:
    OCIO_AVAILABLE = False
    ocio = None

from pxr import Usd, UsdLux


class OCIOManager:
    """Manages OpenColorIO color management for asset review"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize OCIO manager
        
        Args:
            config_path: Path to OCIO config file (None = use default/ACES)
        """
        self.ocio_available = OCIO_AVAILABLE
        self.config = None
        self.processor = None
        
        if not self.ocio_available:
            print("Warning: PyOpenColorIO not available. Install with: pip install PyOpenColorIO")
            return
        
        # Load OCIO config
        self.load_config(config_path)
    
    def load_config(self, config_path: Optional[str] = None) -> bool:
        """Load OCIO config file"""
        if not self.ocio_available:
            return False
        
        try:
            if config_path:
                self.config = ocio.Config.CreateFromFile(config_path)
            else:
                # Try to use default config (from OCIO env var or ACES)
                try:
                    # Check OCIO environment variable
                    import os
                    ocio_env = os.getenv('OCIO')
                    if ocio_env and os.path.exists(ocio_env):
                        self.config = ocio.Config.CreateFromFile(ocio_env)
                    else:
                        # Fallback to ACES 1.2
                        self.config = ocio.Config.CreateFromConfig("aces_1.2")
                except:
                    # Last resort: create minimal config
                    self.config = ocio.Config.CreateRaw()
            
            return True
        except Exception as e:
            print(f"Error loading OCIO config: {e}")
            return False
    
    def get_color_space_from_usd(self, prim: Usd.Prim) -> Optional[str]:
        """Get color space from USD prim using ColorSpaceAPI"""
        if not USD_AVAILABLE:
            return None
        
        try:
            color_space_api = UsdLux.ColorSpaceAPI(prim)
            if color_space_api:
                # Get explicit color space
                color_space = color_space_api.GetColorSpaceAttr()
                if color_space:
                    return color_space.Get()
                
                # Get inherited color space
                inherited = color_space_api.GetInheritedColorSpaceAttr()
                if inherited:
                    return inherited.Get()
        except Exception as e:
            print(f"Error getting color space from USD: {e}")
        
        return None
    
    def get_default_color_space(self, stage: Usd.Stage) -> Optional[str]:
        """Get default color space from USD stage"""
        if not USD_AVAILABLE:
            return None
        
        try:
            root_prim = stage.GetPseudoRoot()
            return self.get_color_space_from_usd(root_prim)
        except Exception as e:
            print(f"Error getting default color space: {e}")
            return None
    
    def create_processor(self, from_space: str, to_space: str) -> Optional[ocio.CPUProcessor]:
        """Create OCIO processor for color space conversion"""
        if not self.ocio_available or not self.config:
            return None
        
        try:
            # Create processor for conversion
            processor = self.config.getProcessor(from_space, to_space)
            return processor.getDefaultCPUProcessor()
        except Exception as e:
            print(f"Error creating OCIO processor: {e}")
            return None
    
    def convert_color_space(self, image: np.ndarray, 
                          from_space: str, to_space: str) -> np.ndarray:
        """
        Convert image between color spaces
        
        Args:
            image: Image array (H, W, 3 or H, W, 4)
            from_space: Source color space name
            to_space: Target color space name
        
        Returns:
            Converted image array
        """
        if not self.ocio_available:
            return image
        
        try:
            processor = self.create_processor(from_space, to_space)
            if not processor:
                return image
            
            # Apply color transform
            # Note: This is a simplified version - actual implementation
            # would need to handle different image formats and data types
            result = processor.applyRGB(image)
            return result
        except Exception as e:
            print(f"Error converting color space: {e}")
            return image
    
    def get_display_color_space(self) -> str:
        """Get display color space (for viewport)"""
        if not self.ocio_available or not self.config:
            return "sRGB"  # Fallback
        
        try:
            # Get default display/view
            display = self.config.getDefaultDisplay()
            view = self.config.getDefaultView(display)
            return self.config.getDisplayViewColorSpaceName(display, view)
        except:
            return "sRGB"  # Fallback
    
    def get_available_color_spaces(self) -> list:
        """Get list of available color spaces"""
        if not self.ocio_available or not self.config:
            return []
        
        try:
            return [cs.getName() for cs in self.config.getColorSpaces()]
        except:
            return []
```

---

### **Phase 3: Viewport Integration (Days 6-10)**

#### **3.1 Integrate OCIO with Viewport Rendering**

```python
# src/xstage/core/viewer.py (additions)

from ..utils.ocio_manager import OCIOManager

class USDViewerWindow:
    def __init__(self):
        # ... existing code ...
        
        # Initialize OCIO manager
        self.ocio_manager = OCIOManager()
        self.current_color_space = None
        self.display_color_space = None
        
        # Get display color space
        if self.ocio_manager.ocio_available:
            self.display_color_space = self.ocio_manager.get_display_color_space()
    
    def load_usd_file(self, filepath: str):
        """Load USD file and detect color space"""
        # ... existing load code ...
        
        # Detect color space from USD
        if self.ocio_manager.ocio_available and self.stage_manager.stage:
            self.current_color_space = self.ocio_manager.get_default_color_space(
                self.stage_manager.stage
            )
            
            # If no color space in USD, use scene linear (common default)
            if not self.current_color_space:
                self.current_color_space = "scene-linear Rec.709-sRGB"
    
    def render_viewport(self):
        """Render viewport with OCIO color management"""
        # ... existing render code ...
        
        # Apply OCIO color transform if needed
        if (self.ocio_manager.ocio_available and 
            self.current_color_space and 
            self.display_color_space):
            
            # Convert from asset color space to display color space
            # (This would be integrated into the actual rendering pipeline)
            pass
```

---

### **Phase 4: UI Integration (Days 11-12)**

#### **4.1 Color Space Info Display**

```python
# Add to viewport overlay or info panel

def update_color_space_info(self):
    """Update color space information display"""
    if not self.ocio_manager.ocio_available:
        return
    
    info = {
        'asset_color_space': self.current_color_space or 'Unknown',
        'display_color_space': self.display_color_space or 'Unknown',
        'ocio_config': self.ocio_manager.config.getName() if self.ocio_manager.config else 'None'
    }
    
    # Display in viewport overlay or info panel
    self.viewport_overlay.set_color_space_info(info)
```

#### **4.2 Color Space Selector (Optional)**

```python
# Add to viewport settings or preferences

def create_color_space_ui(self):
    """Create color space selection UI"""
    if not self.ocio_manager.ocio_available:
        return None
    
    # Color space dropdown
    color_spaces = self.ocio_manager.get_available_color_spaces()
    color_space_combo = QComboBox()
    color_space_combo.addItems(color_spaces)
    
    # Set current color space
    if self.current_color_space in color_spaces:
        color_space_combo.setCurrentText(self.current_color_space)
    
    return color_space_combo
```

---

### **Phase 5: Testing & Validation (Days 13-15)**

#### **5.1 Test Cases**

1. **ACES Config**
   - Load USD with ACES color space
   - Verify colors match Nuke/Houdini
   - Test scene-linear to display conversion

2. **Custom OCIO Config**
   - Load custom OCIO config
   - Verify color spaces available
   - Test color space conversion

3. **USD Color Space Detection**
   - USD file with ColorSpaceAPI
   - USD file without ColorSpaceAPI (fallback)
   - Multiple prims with different color spaces

4. **Viewport Rendering**
   - Verify colors match other tools
   - Test with different color spaces
   - Verify no color shifts

#### **5.2 Validation Checklist**

- ✅ OCIO config loads correctly
- ✅ Color space detected from USD
- ✅ Color space conversion works
- ✅ Viewport displays accurate colors
- ✅ Colors match Nuke/Houdini/Maya/Blender
- ✅ Fallback works when OCIO unavailable
- ✅ Performance acceptable (no slowdown)

---

## 🔧 Technical Details

### **OCIO Integration Points**

1. **USD Color Space Detection**
   - Use `UsdLux.ColorSpaceAPI` to read color space from USD
   - Support explicit and inherited color spaces
   - Fallback to scene-linear if not specified

2. **Viewport Rendering**
   - Apply OCIO transform during rendering
   - Convert from asset color space to display color space
   - Maintain performance (GPU acceleration if possible)

3. **Color Space Display**
   - Show current color space in viewport overlay
   - Display OCIO config info
   - Optional: color space selector UI

### **Dependencies**

```python
# requirements.txt
PyOpenColorIO>=2.2.0  # OCIO Python bindings

# Optional: For better performance
# numpy>=1.20.0  # Already required
```

### **Configuration**

```python
# Support OCIO environment variable
# OCIO=/path/to/config.ocio

# Or use ACES default
# OCIO config will auto-detect ACES if available
```

---

## 📊 Success Criteria

### **Must Have**
- ✅ OCIO config loads correctly
- ✅ Color space detected from USD
- ✅ Viewport displays accurate colors
- ✅ Colors match other VFX tools
- ✅ No performance degradation

### **Nice to Have**
- ✅ Color space selector UI
- ✅ OCIO config selector
- ✅ Color space info in overlay
- ✅ Multiple OCIO config support

---

## 🚀 Implementation Steps

1. **Week 1: Core Implementation**
   - Add PyOpenColorIO dependency
   - Implement OCIOManager
   - Basic color space detection from USD
   - OCIO config loading

2. **Week 2: Integration**
   - Integrate with viewport rendering
   - Color space conversion
   - UI for color space display
   - Testing with ACES

3. **Week 3: Polish & Testing**
   - Performance optimization
   - UI polish
   - Documentation
   - Final testing

---

## 📚 References

- **OpenColorIO**: https://opencolorio.org/
- **PyOpenColorIO**: https://github.com/AcademySoftwareFoundation/OpenColorIO
- **ACES**: https://www.oscars.org/science-technology/aces
- **USD ColorSpaceAPI**: https://openusd.org/release/api/class_usd_lux_color_space_a_p_i.html

---

*This implementation plan focuses on asset review workflows. Color grading, LUT application, and shot/sequence workflows are not included.*

