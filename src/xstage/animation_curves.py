"""
Animation Curve Editor
Extracts and displays time-sampled attributes with keyframe visualization
Based on OpenUSD 25.11 specifications
"""

from typing import Optional, Dict, List, Tuple
from pxr import Usd, Sdf

try:
    from pxr import Usd, Sdf
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class AnimationCurveManager:
    """Manages animation curves and time-sampled attributes"""
    
    @staticmethod
    def get_animated_attributes(prim: Usd.Prim) -> List[Dict]:
        """Get all animated attributes on a prim"""
        if not USD_AVAILABLE or not prim:
            return []
        
        animated_attrs = []
        
        # Get all attributes
        for attr in prim.GetAttributes():
            if attr.GetNumTimeSamples() > 0:
                attr_info = {
                    'name': attr.GetName(),
                    'path': attr.GetPath().pathString,
                    'type': str(attr.GetTypeName()),
                    'time_samples': [],
                    'default_value': None,
                    'has_default': attr.HasAuthoredValue(),
                }
                
                # Get default value
                if attr_info['has_default']:
                    attr_info['default_value'] = attr.Get()
                
                # Get time samples
                time_samples = attr.GetTimeSamples()
                for time in time_samples:
                    value = attr.Get(time)
                    attr_info['time_samples'].append({
                        'time': time,
                        'value': value,
                    })
                
                animated_attrs.append(attr_info)
        
        return animated_attrs
    
    @staticmethod
    def get_all_animated_attributes(stage: Usd.Stage) -> List[Dict]:
        """Get all animated attributes in the stage"""
        if not USD_AVAILABLE or not stage:
            return []
        
        all_animated = []
        
        for prim in stage.Traverse():
            animated = AnimationCurveManager.get_animated_attributes(prim)
            if animated:
                all_animated.append({
                    'prim_path': prim.GetPath().pathString,
                    'attributes': animated,
                })
        
        return all_animated
    
    @staticmethod
    def get_curve_data(attr: Usd.Attribute, time_range: Tuple[float, float] = None, 
                      num_samples: int = 100) -> Dict:
        """Get curve data for an attribute"""
        if not USD_AVAILABLE or not attr:
            return {}
        
        if attr.GetNumTimeSamples() == 0:
            return {}
        
        # Get time samples
        time_samples = attr.GetTimeSamples()
        
        if time_range:
            time_samples = [t for t in time_samples if time_range[0] <= t <= time_range[1]]
        
        if not time_samples:
            return {}
        
        # Get values
        values = []
        for time in time_samples:
            value = attr.Get(time)
            values.append({
                'time': time,
                'value': value,
            })
        
        # Get interpolation info
        interpolation = attr.GetMetadata('interpolation') if attr.HasMetadata('interpolation') else None
        
        curve_data = {
            'attribute_path': attr.GetPath().pathString,
            'type': str(attr.GetTypeName()),
            'keyframes': values,
            'num_keyframes': len(values),
            'time_range': (min(time_samples), max(time_samples)),
            'interpolation': interpolation,
        }
        
        # For numeric types, calculate min/max
        if values and isinstance(values[0]['value'], (int, float)):
            numeric_values = [v['value'] for v in values]
            curve_data['value_range'] = (min(numeric_values), max(numeric_values))
        elif values and isinstance(values[0]['value'], (list, tuple)):
            # For vector types
            try:
                all_values = []
                for v in values:
                    if isinstance(v['value'], (list, tuple)):
                        all_values.extend(v['value'])
                if all_values:
                    curve_data['value_range'] = (min(all_values), max(all_values))
            except:
                pass
        
        return curve_data
    
    @staticmethod
    def set_keyframe(attr: Usd.Attribute, time: float, value) -> bool:
        """Set a keyframe on an attribute"""
        if not USD_AVAILABLE or not attr:
            return False
        
        try:
            attr.Set(value, time)
            return True
        except Exception as e:
            print(f"Error setting keyframe: {e}")
            return False
    
    @staticmethod
    def remove_keyframe(attr: Usd.Attribute, time: float) -> bool:
        """Remove a keyframe from an attribute"""
        if not USD_AVAILABLE or not attr:
            return False
        
        try:
            # Get all time samples
            time_samples = list(attr.GetTimeSamples())
            
            if time in time_samples:
                # Create new time samples without this one
                new_samples = [t for t in time_samples if t != time]
                
                # Clear and re-set
                if new_samples:
                    # Get values for remaining times
                    values = {t: attr.Get(t) for t in new_samples}
                    
                    # Clear all
                    attr.Clear()
                    
                    # Re-set values
                    for t, v in values.items():
                        attr.Set(v, t)
                else:
                    # No more keyframes, clear
                    attr.Clear()
                
                return True
        except Exception as e:
            print(f"Error removing keyframe: {e}")
            return False
        
        return False
    
    @staticmethod
    def get_interpolation_mode(attr: Usd.Attribute) -> Optional[str]:
        """Get interpolation mode for an attribute"""
        if not USD_AVAILABLE or not attr:
            return None
        
        if attr.HasMetadata('interpolation'):
            return attr.GetMetadata('interpolation')
        
        return None
    
    @staticmethod
    def set_interpolation_mode(attr: Usd.Attribute, mode: str) -> bool:
        """Set interpolation mode for an attribute"""
        if not USD_AVAILABLE or not attr:
            return False
        
        try:
            attr.SetMetadata('interpolation', mode)
            return True
        except Exception as e:
            print(f"Error setting interpolation mode: {e}")
            return False

