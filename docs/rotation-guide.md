# Axis Rotation & Orientation Guide

## Overview

The advanced axis orientation system handles **all common import issues**:
- ✅ Flipped axes (X, Y, or Z inverted)
- ✅ Wrong up-axis (Y-up vs Z-up)
- ✅ Wrong handedness (right vs left)
- ✅ **Arbitrary rotations** (90°, 180°, or any custom angle)

## Common Use Cases

### 1. Model Lying on Its Side (90° Rotation)

**Problem:** OBJ import is lying flat instead of standing up

**Solution:**
```
Rotation Tab → Rotate X → 90°
```

Or use preset:
```
Presets Tab → "Lying Down (X 90°)"
```

**What happens:** Rotates model 90° around X axis to stand it upright

---

### 2. Model Facing Wrong Direction

**Problem:** Model facing backwards or sideways

**Solutions:**

**180° turn around:**
```
Rotation Tab → Rotate Y → 180°
```

**90° turn left/right:**
```
Rotation Tab → Rotate Y → 90°  (or -90°)
```

**Quick buttons:** Click `90°`, `180°`, `-90°` for instant rotation

---

### 3. Y-up to Z-up Conversion + Rotation

**Problem:** Houdini export (Z-up) needs 90° rotation for correct orientation

**Solution:**
```
Basic Tab → Up Axis → "Z-up (Houdini, 3ds Max)"
Rotation Tab → Rotate Y → 90°
```

Or use preset:
```
Presets Tab → "Y→Z + 90°"
```

---

### 4. Custom Angle (Not 90° or 180°)

**Problem:** Model needs 45° or 135° rotation

**Solution:**
```
Rotation Tab → Rotate Y → Use slider or type "45" in spinbox
```

**Slider ranges:** -180° to +180° with tick marks at 90° intervals

---

### 5. Multiple Rotations Combined

**Problem:** Need rotation on multiple axes

**Example:** Rotate 90° around X, then 45° around Y

**Solution:**
```
Rotation Tab:
  Rotate X → 90°
  Rotate Y → 45°
  Rotate Z → 0°
```

**Rotation order:** X → Y → Z (standard)

---

## UI Layout

### Tab 1: Basic
```
┌─────────────────────────────┐
│ Flip Axes                   │
│  □ Flip X (Left ↔ Right)   │
│  □ Flip Y (Up ↔ Down)      │
│  □ Flip Z (Front ↔ Back)   │
├─────────────────────────────┤
│ Up Axis                     │
│  [Y-up (OpenGL, Maya) ▼]   │
├─────────────────────────────┤
│ Handedness                  │
│  [Right-handed (OpenGL) ▼] │
└─────────────────────────────┘
```

### Tab 2: Rotation
```
┌─────────────────────────────────────┐
│ Rotate X (Pitch)                    │
│  Angle: [═══════●═══════] [0.0° ]  │
│  [-90°] [-45°] [0°] [45°] [90°] [180°] │
├─────────────────────────────────────┤
│ Rotate Y (Yaw)                      │
│  Angle: [═══════●═══════] [0.0° ]  │
│  [-90°] [-45°] [0°] [45°] [90°] [180°] │
├─────────────────────────────────────┤
│ Rotate Z (Roll)                     │
│  Angle: [═══════●═══════] [0.0° ]  │
│  [-90°] [-45°] [0°] [45°] [90°] [180°] │
└─────────────────────────────────────┘
```

### Tab 3: Presets
```
┌─────────────────────────────┐
│ Software Presets            │
│ [OpenGL/Maya] [Houdini/Max] │
│ [Blender] [Unity] [Unreal]  │
├─────────────────────────────┤
│ Common Rotation Fixes       │
│ [Y 90° CW]  [Y 90° CCW]    │
│ [Y 180°]    [X 90° CW]     │
│ [X 90° CCW] [X 180°]       │
│ [Z 90° CW]  [Z 90° CCW]    │
│ [Z 180°]                   │
├─────────────────────────────┤
│ Common Import Issues        │
│ [Lying Down (X 90°)]       │
│ [Lying Down (Z 90°)]       │
│ [Upside Down]              │
│ [Backwards]                │
│ [Y→Z + 90°]                │
└─────────────────────────────┘
```

---

## Transform Order

The complete transformation is applied in this order:

1. **Flip** (scale by -1 on selected axes)
2. **Rotate X** (pitch)
3. **Rotate Y** (yaw)
4. **Rotate Z** (roll)
5. **Up Axis Conversion** (Y↔Z swap if needed)
6. **Handedness** (Z flip if left-handed)

This ensures predictable results for any combination.

---

## Practical Examples

### Example 1: CAD Import (Wrong Orientation)

**Scenario:** CAD file imported lying down and facing backwards

**Steps:**
1. Go to Rotation tab
2. Click `90°` under Rotate X
3. Click `180°` under Rotate Y
4. Done!

**Result:** Model now upright and facing forward

---

### Example 2: Scanned Model (Inverted Y)

**Scenario:** 3D scan has Y axis flipped

**Steps:**
1. Go to Basic tab
2. Check "Flip Y axis (Up ↔ Down)"
3. Done!

**Result:** Model right-side up

---

### Example 3: Game Engine Export (Y-up to Z-up)

**Scenario:** Unity asset (Y-up) needs to work in Unreal (Z-up)

**Steps:**
1. Go to Presets tab
2. Click "Y→Z + 90°"
3. Done!

**Result:** Correct orientation for Unreal

---

### Example 4: Fine-Tuning

**Scenario:** Model almost correct but needs slight adjustment

**Steps:**
1. Go to Rotation tab
2. Use slider or type exact angle: `37.5°`
3. Real-time preview updates
4. Adjust until perfect

**Result:** Precisely oriented model

---

## Command Line Usage (Future)

```bash
# Rotate Y by 90 degrees
xstage model.obj --rotate-y 90

# Multiple rotations
xstage model.fbx --rotate-x 90 --rotate-y 180

# Combine with other fixes
xstage import.obj --flip-y --rotate-y 90 --up-axis Z --scale 0.01

# Use preset
xstage broken.fbx --preset "Lying Down (X 90°)"
```

---

## Python API Usage

```python
from xstage import Viewer
from xstage.orientation import AxisOrientation

# Create viewer
viewer = Viewer()

# Set orientation
orientation = AxisOrientation()
orientation.set_rotation_y(90)  # 90° around Y
orientation.set_flip_x(True)    # Flip X
orientation.set_up_axis('Z')    # Z-up

# Apply to viewer
viewer.set_orientation(orientation)

# Or use matrix directly
matrix = orientation.get_transform_matrix()
viewer.apply_transform(matrix)
```

---

## Troubleshooting

### Issue: Model disappears after rotation

**Cause:** Rotated outside view frustum

**Solution:** Press `F` to frame all (auto-fit to view)

---

### Issue: Rotation doesn't look right

**Cause:** Wrong rotation order or axis

**Solutions:**
1. Click "Reset All" button
2. Try different axis (X vs Y vs Z)
3. Use preset buttons to test

---

### Issue: Need opposite rotation

**Cause:** Positive angle when negative needed (or vice versa)

**Solution:** 
- If 90° wrong direction → try -90°
- If 180° → stays same (180° = -180°)

---

## Quick Reference

| Problem | Solution |
|---------|----------|
| Lying flat | Rotate X: 90° |
| Upside down | Flip Y or Rotate X: 180° |
| Facing backwards | Rotate Y: 180° |
| Facing left/right | Rotate Y: ±90° |
| Tilted | Rotate Z: adjust angle |
| Y-up → Z-up | Basic tab: Up Axis → Z-up |
| Mirrored | Flip appropriate axis |
| CAD import issues | Try presets first! |

---

## Technical Details

### Rotation Matrices

**Rotate X (Pitch):**
```
[1    0       0    ]
[0  cos(θ) -sin(θ)]
[0  sin(θ)  cos(θ)]
```

**Rotate Y (Yaw):**
```
[ cos(θ)  0  sin(θ)]
[   0     1    0   ]
[-sin(θ)  0  cos(θ)]
```

**Rotate Z (Roll):**
```
[cos(θ) -sin(θ)  0]
[sin(θ)  cos(θ)  0]
[  0       0     1]
```

### Gimbal Lock

Using XYZ rotation order can cause gimbal lock at ±90° on Y.

**If you experience gimbal lock:**
- Use presets instead of manual rotation
- Or adjust rotation order (future feature)

---

## Best Practices

1. **Try presets first** - Most issues covered
2. **Use quick buttons** - Faster than typing
3. **Test with F key** - Frame all after each change
4. **Reset if confused** - Start fresh
5. **Document your fix** - Save preset for similar models

---

## Integration with xStage

### Viewport Integration

The orientation widget is docked on the right side:

```
┌────────────────┬──────────────┐
│                │ Scene Scale  │
│                ├──────────────┤
│   Viewport     │ Axis Orient  │
│                │  [Basic]     │
│                │  [Rotation]  │
│                │  [Presets]   │
└────────────────┴──────────────┘
```

### Auto-Save Settings

Orientation settings are saved per file:
```
~/.xstage/orientations/
  model_name.obj.json
  character.fbx.json
```

Next time you open the same file, orientation is remembered!

---

## Advanced Features (Coming Soon)

- [ ] Rotation order selection (XYZ, ZYX, etc.)
- [ ] Euler vs Quaternion
- [ ] Animation curve rotation
- [ ] Batch apply to multiple files
- [ ] Save custom presets
- [ ] Share presets with team

---

This makes xStage the **most flexible USD viewer** for handling import orientation issues! 🎯