"""
Scene Metrics Calculator
Calculates performance and complexity metrics for asset review
"""

from typing import Dict, List, Optional
import os

try:
    from pxr import Usd, UsdShade, UsdLux
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False


class SceneMetricsCalculator:
    """Calculates scene performance and complexity metrics"""
    
    @staticmethod
    def calculate_polygon_counts(geometry_data: Dict) -> Dict:
        """
        Calculate polygon counts per object and total
        
        Args:
            geometry_data: Geometry data from USDStageManager
        
        Returns:
            Dictionary with polygon count information
        """
        meshes = geometry_data.get('meshes', [])
        
        polygon_counts = {
            'total_polygons': 0,
            'total_objects': len(meshes),
            'objects': []
        }
        
        for mesh in meshes:
            face_vertex_counts = mesh.get('face_vertex_counts', [])
            polygon_count = len(face_vertex_counts)
            
            polygon_counts['total_polygons'] += polygon_count
            polygon_counts['objects'].append({
                'name': mesh.get('name', 'Unknown'),
                'polygons': polygon_count,
                'vertices': len(mesh.get('points', []))
            })
        
        return polygon_counts
    
    @staticmethod
    def estimate_texture_memory(stage: Optional[object], geometry_data: Dict) -> Dict:
        """
        Estimate texture memory usage from materials
        
        Args:
            stage: USD stage
            geometry_data: Geometry data from USDStageManager
        
        Returns:
            Dictionary with texture memory estimates
        """
        if not USD_AVAILABLE or not stage:
            return {
                'total_memory_mb': 0.0,
                'texture_count': 0,
                'textures': []
            }
        
        textures = []
        total_memory = 0.0
        
        try:
            # Get materials
            materials = geometry_data.get('materials', [])
            
            for material_data in materials:
                material_path = material_data.get('path')
                if not material_path:
                    continue
                
                prim = stage.GetPrimAtPath(material_path)
                if not prim:
                    continue
                
                # Get material shader inputs
                material = UsdShade.Material(prim)
                surface_output = material.GetSurfaceOutput()
                
                if surface_output:
                    # Get connected shader
                    source = surface_output.GetConnectedSource()
                    if source:
                        shader_prim = stage.GetPrimAtPath(source[0].GetPath())
                        if shader_prim:
                            shader = UsdShade.Shader(shader_prim)
                            
                            # Check common texture inputs
                            texture_inputs = [
                                'diffuseColor', 'baseColor', 'albedo',
                                'normal', 'normalMap', 'bumpMap',
                                'roughness', 'metallic', 'specular',
                                'emissiveColor', 'emissionColor',
                                'opacity', 'opacityThreshold',
                                'displacement', 'height'
                            ]
                            
                            for input_name in texture_inputs:
                                input_attr = shader.GetInput(input_name)
                                if input_attr:
                                    # Check if it's a texture file
                                    value = input_attr.Get()
                                    if value and isinstance(value, str):
                                        # Check if it's a file path
                                        if os.path.exists(value) or value.startswith('/') or '://' in value:
                                            # Estimate texture size (assume 4MB per texture as default)
                                            # This is a rough estimate - actual size depends on resolution
                                            estimated_size = 4.0  # MB
                                            total_memory += estimated_size
                                            
                                            textures.append({
                                                'name': os.path.basename(value) if '/' in value else value,
                                                'path': value,
                                                'material': str(material_path),
                                                'input': input_name,
                                                'estimated_size_mb': estimated_size
                                            })
        except Exception as e:
            print(f"Error estimating texture memory: {e}")
        
        return {
            'total_memory_mb': total_memory,
            'texture_count': len(textures),
            'textures': textures
        }
    
    @staticmethod
    def estimate_draw_calls(geometry_data: Dict) -> Dict:
        """
        Estimate draw calls based on geometry
        
        Args:
            geometry_data: Geometry data from USDStageManager
        
        Returns:
            Dictionary with draw call estimates
        """
        meshes = geometry_data.get('meshes', [])
        
        # Each mesh is typically one draw call
        # But we can estimate based on material changes
        draw_calls = {
            'estimated_draw_calls': len(meshes),
            'mesh_count': len(meshes),
            'material_count': len(geometry_data.get('materials', [])),
            'note': 'Each mesh typically requires one draw call'
        }
        
        # More accurate: count unique material/mesh combinations
        # For now, we'll use mesh count as a baseline
        # In a real renderer, this would be more complex
        
        return draw_calls
    
    @staticmethod
    def get_file_size_breakdown(filepath: str) -> Dict:
        """
        Get USD file size breakdown
        
        Args:
            filepath: Path to USD file
        
        Returns:
            Dictionary with file size information
        """
        if not filepath or not os.path.exists(filepath):
            return {
                'total_size_mb': 0.0,
                'file_size_mb': 0.0,
                'note': 'File not found'
            }
        
        try:
            file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
            
            # For USD files, we can check for references/payloads
            # This is a simplified version
            breakdown = {
                'total_size_mb': file_size,
                'file_size_mb': file_size,
                'references_mb': 0.0,
                'payloads_mb': 0.0,
                'note': 'Includes main file only (references/payloads not calculated)'
            }
            
            # TODO: Could traverse stage to get referenced file sizes
            # This would require loading all references/payloads
            
            return breakdown
        except Exception as e:
            return {
                'total_size_mb': 0.0,
                'file_size_mb': 0.0,
                'note': f'Error: {e}'
            }
    
    @staticmethod
    def calculate_complexity_score(geometry_data: Dict, polygon_counts: Dict, 
                                   texture_memory: Dict, draw_calls: Dict) -> Dict:
        """
        Calculate scene complexity score
        
        Args:
            geometry_data: Geometry data
            polygon_counts: Polygon count information
            texture_memory: Texture memory information
            draw_calls: Draw call information
        
        Returns:
            Dictionary with complexity score and breakdown
        """
        # Complexity factors
        polygon_factor = polygon_counts.get('total_polygons', 0) / 100000.0  # Normalize to 100k
        object_factor = polygon_counts.get('total_objects', 0) / 100.0  # Normalize to 100 objects
        texture_factor = texture_memory.get('total_memory_mb', 0.0) / 100.0  # Normalize to 100MB
        draw_call_factor = draw_calls.get('estimated_draw_calls', 0) / 50.0  # Normalize to 50 draw calls
        
        # Weighted complexity score (0-100)
        complexity_score = min(100.0, (
            polygon_factor * 40.0 +  # Polygons: 40% weight
            object_factor * 20.0 +   # Objects: 20% weight
            texture_factor * 20.0 +  # Textures: 20% weight
            draw_call_factor * 20.0  # Draw calls: 20% weight
        ))
        
        # Determine complexity level
        if complexity_score < 20:
            level = "Low"
            color = "green"
        elif complexity_score < 50:
            level = "Medium"
            color = "yellow"
        elif complexity_score < 80:
            level = "High"
            color = "orange"
        else:
            level = "Very High"
            color = "red"
        
        return {
            'score': complexity_score,
            'level': level,
            'color': color,
            'breakdown': {
                'polygon_factor': polygon_factor * 100,
                'object_factor': object_factor * 100,
                'texture_factor': texture_factor * 100,
                'draw_call_factor': draw_call_factor * 100
            }
        }
    
    @staticmethod
    def calculate_all_metrics(stage: Optional[object], geometry_data: Dict, 
                             filepath: Optional[str] = None) -> Dict:
        """
        Calculate all scene metrics
        
        Args:
            stage: USD stage
            geometry_data: Geometry data from USDStageManager
            filepath: Path to USD file (optional)
        
        Returns:
            Dictionary with all calculated metrics
        """
        polygon_counts = SceneMetricsCalculator.calculate_polygon_counts(geometry_data)
        texture_memory = SceneMetricsCalculator.estimate_texture_memory(stage, geometry_data)
        draw_calls = SceneMetricsCalculator.estimate_draw_calls(geometry_data)
        file_size = SceneMetricsCalculator.get_file_size_breakdown(filepath) if filepath else {}
        complexity = SceneMetricsCalculator.calculate_complexity_score(
            geometry_data, polygon_counts, texture_memory, draw_calls
        )
        
        return {
            'polygon_counts': polygon_counts,
            'texture_memory': texture_memory,
            'draw_calls': draw_calls,
            'file_size': file_size,
            'complexity': complexity
        }

