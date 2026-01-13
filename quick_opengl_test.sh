#!/bin/bash
# Quick OpenGL test for xStage

echo "=== Quick OpenGL Test ==="

# Test basic OpenGL with Python
python3 -c "
import sys
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    from OpenGL.GL import *
    print('✓ Qt and PyOpenGL imports successful')
    
    # Test basic OpenGL calls
    app = QApplication([])
    
    class TestWidget(QOpenGLWidget):
        def initializeGL(self):
            print('✓ OpenGL context created')
            try:
                version = glGetString(GL_VERSION)
                print(f'✓ OpenGL version: {version}')
                glClearColor(0.2, 0.2, 0.2, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                print('✓ Basic OpenGL operations successful')
            except Exception as e:
                print(f'✗ OpenGL error: {e}')
    
    widget = TestWidget()
    widget.show()
    app.processEvents()
    widget.close()
    print('✓ OpenGL test completed successfully')
    
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'✗ Error: {e}')
    sys.exit(1)
"

echo ""
echo "If this test passes, the basic OpenGL setup should work."
echo "If it fails, you may need to install OpenGL drivers:"
echo "  sudo apt-get install libgl1-mesa-glx mesa-utils"
