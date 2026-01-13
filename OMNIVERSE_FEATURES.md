# xStage: Open Source USD Viewer (Omniverse Alternative)

## 🎯 Vision
Create an open-source alternative to NVIDIA Omniverse for USD file viewing, editing, and collaboration - accessible to everyone without proprietary restrictions.

## ✅ Current Features (Similar to Omniverse)

### Core USD Support
- ✅ **USD Stage Loading** - Open .usd, .usda, .usdc files
- ✅ **Timeline Playback** - Scrub through animated USD files
- ✅ **Hierarchy Browser** - Navigate USD prim hierarchy
- ✅ **Property Inspector** - View and edit prim attributes
- ✅ **Layer Composition** - View and manage USD layers/sublayers

### Rendering
- ✅ **Dual Rendering Paths**:
  - **Hydra 2.0** (Storm) - GPU-accelerated rendering with materials
  - **OpenGL Fallback** - Basic geometry visualization
- ✅ **Camera Controls** - Orbit, pan, zoom, orthographic views
- ✅ **Multiple Viewports** - Top, Front, Left, Right, Perspective
- ✅ **Grid & Axis** - Scene orientation helpers

### Materials & Shading
- ✅ **Material Preview** - Basic material visualization
- ✅ **Wireframe Mode** - Toggle between shaded/wireframe
- ✅ **Lighting** - Basic scene lighting

### Performance
- ✅ **Payload Management** - Load/unload heavy assets
- ✅ **FPS Counter** - Performance monitoring
- ✅ **Scene Bounds** - Auto-framing to geometry

## 🚀 Roadmap: Omniverse-Like Features

### Phase 1: Core Rendering (Next 2-3 months)
- [ ] **MDL Material Support** - NVIDIA Material Definition Language
- [ ] **PBR Rendering** - Physically-based materials
- [ ] **HDR Environment Maps** - Image-based lighting
- [ ] **Shadow Mapping** - Real-time shadows
- [ ] **Ambient Occlusion** - Enhanced depth perception
- [ ] **Post-Processing** - Bloom, tone mapping, color grading

### Phase 2: Advanced USD Features (3-6 months)
- [ ] **Variant Sets UI** - Interactive variant switching
- [ ] **Collection Management** - Organize scene elements
- [ ] **Reference/Payload Browser** - Manage external references
- [ ] **Prim Creation Tools** - Add meshes, lights, cameras
- [ ] **Transform Gizmos** - Interactive translate/rotate/scale
- [ ] **USD Authoring** - Edit and save USD files
- [ ] **Undo/Redo System** - Non-destructive editing

### Phase 3: Collaboration (6-9 months)
- [ ] **Live Sync** - Multi-user collaboration (like Omniverse Nucleus)
- [ ] **Version Control Integration** - Git/Perforce support
- [ ] **Comments & Annotations** - Review and feedback tools
- [ ] **Session Management** - Join/leave collaborative sessions
- [ ] **Conflict Resolution** - Handle concurrent edits

### Phase 4: Production Tools (9-12 months)
- [ ] **Animation Tools** - Keyframe editing, curves
- [ ] **Rigging Support** - UsdSkel visualization
- [ ] **Particle Systems** - Point instancing
- [ ] **Volume Rendering** - OpenVDB support
- [ ] **Render Settings** - Configure render passes
- [ ] **Export Pipeline** - FBX, glTF, Alembic export
- [ ] **Python Scripting** - Automation and extensions

### Phase 5: Enterprise Features (12+ months)
- [ ] **Asset Browser** - Library management
- [ ] **Thumbnail Generation** - Quick asset preview
- [ ] **Search & Filter** - Find assets quickly
- [ ] **Metadata Management** - Custom properties
- [ ] **Render Farm Integration** - Distributed rendering
- [ ] **Cloud Storage** - S3, Azure, GCP support
- [ ] **Authentication** - User management
- [ ] **Audit Logging** - Track changes

## 🔧 Technical Architecture

### Rendering Stack
```
┌─────────────────────────────────────┐
│         xStage Application          │
├─────────────────────────────────────┤
│  Hydra 2.0 (Storm)  │  OpenGL       │
├─────────────────────────────────────┤
│         USD (OpenUSD)               │
├─────────────────────────────────────┤
│  PySide6 (Qt)  │  Python 3.10+      │
└─────────────────────────────────────┘
```

### Key Technologies
- **OpenUSD** - Universal Scene Description
- **Hydra 2.0** - High-performance rendering
- **PySide6** - Modern Qt bindings
- **OpenGL 4.1+** - Graphics API
- **Python 3.10+** - Application logic

## 📊 Comparison with Omniverse

| Feature | Omniverse | xStage | Status |
|---------|-----------|--------|--------|
| USD Support | ✅ Full | ✅ Full | Complete |
| Hydra Rendering | ✅ Storm/Karma | ✅ Storm | Complete |
| Material Support | ✅ MDL | ⚠️ Basic | In Progress |
| Collaboration | ✅ Nucleus | ❌ Planned | Phase 3 |
| RTX Rendering | ✅ Yes | ❌ No | Not Planned |
| Physics | ✅ PhysX | ❌ No | Not Planned |
| AI Tools | ✅ Yes | ❌ No | Not Planned |
| Open Source | ❌ No | ✅ Yes | ✅ |
| Cost | 💰 Enterprise | 🆓 Free | ✅ |
| Linux Support | ✅ Yes | ✅ Yes | ✅ |
| Windows Support | ✅ Yes | ⚠️ Partial | In Progress |
| macOS Support | ❌ No | ✅ Yes | ✅ |

## 🎨 Design Philosophy

### Unlike Omniverse, xStage focuses on:
1. **Open Source** - Community-driven development
2. **Lightweight** - No heavy NVIDIA dependencies
3. **Cross-Platform** - Linux, macOS, Windows
4. **VFX Pipeline** - Studio-friendly workflows
5. **Extensibility** - Python API for customization

### Not Competing with Omniverse on:
1. **RTX Rendering** - Requires NVIDIA hardware
2. **Physics Simulation** - PhysX is proprietary
3. **AI Features** - Requires specialized hardware
4. **Enterprise Support** - Community-based support

## 🤝 Contributing

We welcome contributions! Areas where help is needed:
- **Hydra Rendering** - Material system improvements
- **USD Authoring** - Edit and save capabilities
- **Performance** - Optimization for large scenes
- **Documentation** - User guides and tutorials
- **Testing** - Cross-platform validation
- **UI/UX** - Interface improvements

## 📝 License
MIT License - Free for commercial and personal use

## 🔗 Resources
- [OpenUSD Documentation](https://openusd.org)
- [Hydra Rendering](https://graphics.pixar.com/usd/docs/USD-Glossary.html#USDGlossary-Hydra)
- [NVIDIA Omniverse](https://www.nvidia.com/en-us/omniverse/) (for comparison)

## 💡 Use Cases

### VFX Studios
- Review animated sequences
- Check USD asset structure
- Validate scene composition
- Collaborate on shots

### Game Development
- Preview USD assets
- Convert to game formats
- Validate materials
- Check performance

### Architecture/Design
- Visualize 3D models
- Review materials
- Present to clients
- Export renders

### Education
- Learn USD pipeline
- Teach 3D workflows
- Free alternative to expensive tools
- Open source for modification

---

**Status**: Active Development  
**Version**: 0.9.0 (Beta)  
**Target**: Production-ready 1.0 by Q3 2026
