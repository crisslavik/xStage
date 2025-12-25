"""
Annotations System
Scene annotations with drawing tools and arrow options
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

try:
    from pxr import Usd, Gf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class AnnotationType(Enum):
    """Types of annotations"""
    TEXT = "text"
    ARROW = "arrow"
    DRAWING = "drawing"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    HIGHLIGHT = "highlight"


@dataclass
class Annotation:
    """Single annotation"""
    id: str
    type: AnnotationType
    prim_path: Optional[str] = None  # Associated prim (if any)
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # 3D position
    viewport_position: Tuple[float, float] = (0.0, 0.0)  # 2D viewport position
    text: str = ""
    color: Tuple[float, float, float, float] = (1.0, 1.0, 0.0, 1.0)  # RGBA
    size: float = 1.0
    points: List[Tuple[float, float]] = field(default_factory=list)  # For drawings
    arrow_start: Optional[Tuple[float, float, float]] = None
    arrow_end: Optional[Tuple[float, float, float]] = None
    arrow_head_size: float = 0.5
    author: str = ""
    timestamp: float = 0.0
    visible: bool = True


class AnnotationManager:
    """Manages scene annotations"""
    
    def __init__(self, stage: Optional[Usd.Stage] = None):
        self.stage = stage
        self.annotations: List[Annotation] = []
        self.next_id = 1
    
    def add_annotation(self, annotation: Annotation) -> str:
        """Add an annotation"""
        if not annotation.id:
            annotation.id = f"annotation_{self.next_id}"
            self.next_id += 1
        
        self.annotations.append(annotation)
        return annotation.id
    
    def add_text_annotation(self, text: str, position: Tuple[float, float, float],
                           prim_path: Optional[str] = None,
                           color: Tuple[float, float, float, float] = (1.0, 1.0, 0.0, 1.0)) -> str:
        """Add a text annotation"""
        import time
        annotation = Annotation(
            id="",
            type=AnnotationType.TEXT,
            text=text,
            position=position,
            prim_path=prim_path,
            color=color,
            timestamp=time.time()
        )
        return self.add_annotation(annotation)
    
    def add_arrow_annotation(self, start: Tuple[float, float, float],
                           end: Tuple[float, float, float],
                           text: str = "",
                           color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 1.0),
                           head_size: float = 0.5) -> str:
        """Add an arrow annotation"""
        import time
        annotation = Annotation(
            id="",
            type=AnnotationType.ARROW,
            arrow_start=start,
            arrow_end=end,
            text=text,
            color=color,
            arrow_head_size=head_size,
            timestamp=time.time()
        )
        return self.add_annotation(annotation)
    
    def add_drawing_annotation(self, points: List[Tuple[float, float]],
                              viewport_position: Tuple[float, float],
                              color: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 1.0),
                              size: float = 2.0) -> str:
        """Add a freehand drawing annotation"""
        import time
        annotation = Annotation(
            id="",
            type=AnnotationType.DRAWING,
            points=points,
            viewport_position=viewport_position,
            color=color,
            size=size,
            timestamp=time.time()
        )
        return self.add_annotation(annotation)
    
    def add_shape_annotation(self, shape_type: AnnotationType,
                           position: Tuple[float, float, float],
                           size: Tuple[float, float],
                           color: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)) -> str:
        """Add a shape annotation (rectangle, circle, etc.)"""
        import time
        annotation = Annotation(
            id="",
            type=shape_type,
            position=position,
            color=color,
            size=size[0],  # Store width
            timestamp=time.time()
        )
        # Store height in points
        annotation.points = [(0, size[1])]
        return self.add_annotation(annotation)
    
    def remove_annotation(self, annotation_id: str) -> bool:
        """Remove an annotation"""
        for i, ann in enumerate(self.annotations):
            if ann.id == annotation_id:
                self.annotations.pop(i)
                return True
        return False
    
    def get_annotations_for_prim(self, prim_path: str) -> List[Annotation]:
        """Get all annotations for a specific prim"""
        return [ann for ann in self.annotations if ann.prim_path == prim_path]
    
    def get_visible_annotations(self) -> List[Annotation]:
        """Get all visible annotations"""
        return [ann for ann in self.annotations if ann.visible]
    
    def export_annotations(self, filepath: str) -> bool:
        """Export annotations to JSON file"""
        try:
            data = {
                'annotations': [
                    {
                        'id': ann.id,
                        'type': ann.type.value,
                        'prim_path': ann.prim_path,
                        'position': list(ann.position),
                        'viewport_position': list(ann.viewport_position),
                        'text': ann.text,
                        'color': list(ann.color),
                        'size': ann.size,
                        'points': ann.points,
                        'arrow_start': list(ann.arrow_start) if ann.arrow_start else None,
                        'arrow_end': list(ann.arrow_end) if ann.arrow_end else None,
                        'arrow_head_size': ann.arrow_head_size,
                        'author': ann.author,
                        'timestamp': ann.timestamp,
                        'visible': ann.visible,
                    }
                    for ann in self.annotations
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting annotations: {e}")
            return False
    
    def import_annotations(self, filepath: str) -> bool:
        """Import annotations from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.annotations.clear()
            
            for ann_data in data.get('annotations', []):
                annotation = Annotation(
                    id=ann_data.get('id', ''),
                    type=AnnotationType(ann_data.get('type', 'text')),
                    prim_path=ann_data.get('prim_path'),
                    position=tuple(ann_data.get('position', [0, 0, 0])),
                    viewport_position=tuple(ann_data.get('viewport_position', [0, 0])),
                    text=ann_data.get('text', ''),
                    color=tuple(ann_data.get('color', [1, 1, 0, 1])),
                    size=ann_data.get('size', 1.0),
                    points=[tuple(p) for p in ann_data.get('points', [])],
                    arrow_start=tuple(ann_data.get('arrow_start')) if ann_data.get('arrow_start') else None,
                    arrow_end=tuple(ann_data.get('arrow_end')) if ann_data.get('arrow_end') else None,
                    arrow_head_size=ann_data.get('arrow_head_size', 0.5),
                    author=ann_data.get('author', ''),
                    timestamp=ann_data.get('timestamp', 0.0),
                    visible=ann_data.get('visible', True),
                )
                self.annotations.append(annotation)
            
            return True
        except Exception as e:
            print(f"Error importing annotations: {e}")
            return False

