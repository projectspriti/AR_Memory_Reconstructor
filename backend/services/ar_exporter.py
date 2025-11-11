import numpy as np
import json
import os
import base64
from PIL import Image, ImageDraw
import trimesh
import struct

class ARExporter:
    def __init__(self):
        """Initialize AR export tools"""
        self.supported_formats = ['glb', 'gltf', 'obj', 'usdz']
    
    def export_ar_scene(self, scene_data, output_path):
        """Export 3D scene to AR-compatible format"""
        try:
            # Create trimesh object from scene data
            mesh = self._create_trimesh_from_scene(scene_data)
            
            # Export to GLB format (most compatible with AR)
            if output_path.endswith('.glb'):
                mesh.export(output_path, file_type='glb')
            elif output_path.endswith('.gltf'):
                mesh.export(output_path, file_type='gltf')
            elif output_path.endswith('.obj'):
                mesh.export(output_path, file_type='obj')
            else:
                # Default to GLB
                output_path = output_path.rsplit('.', 1)[0] + '.glb'
                mesh.export(output_path, file_type='glb')
            
            return output_path
            
        except Exception as e:
            print(f"AR export error: {e}")
            # Fallback to simple export
            return self._export_simple_format(scene_data, output_path)
    
    def _create_trimesh_from_scene(self, scene_data):
        """Create trimesh object from scene data"""
        vertices = np.array(scene_data['vertices'])
        faces = np.array(scene_data['faces'])
        
        # Create mesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Add colors if available
        if 'vertex_colors' in scene_data and scene_data['vertex_colors']:
            vertex_colors = np.array(scene_data['vertex_colors'])
            if vertex_colors.max() > 1.0:
                vertex_colors = vertex_colors / 255.0
            
            # Ensure RGBA format
            if vertex_colors.shape[1] == 3:
                alpha = np.ones((vertex_colors.shape[0], 1))
                vertex_colors = np.hstack([vertex_colors, alpha])
            
            mesh.visual.vertex_colors = vertex_colors
        
        # Add lighting information as metadata
        if 'lighting' in scene_data:
            mesh.metadata['lighting'] = scene_data['lighting']
        
        return mesh
    
    def _export_simple_format(self, scene_data, output_path):
        """Simple fallback export format"""
        # Export as JSON with embedded geometry
        export_data = {
            'format': 'ar_memory_scene',
            'version': '1.0',
            'geometry': {
                'vertices': scene_data['vertices'],
                'faces': scene_data['faces'],
                'vertex_colors': scene_data.get('vertex_colors', [])
            },
            'lighting': scene_data.get('lighting', {}),
            'metadata': {
                'vertex_count': scene_data.get('vertex_count', 0),
                'face_count': scene_data.get('face_count', 0),
                'bounds': scene_data.get('bounds', []),
                'center': scene_data.get('center', [0, 0, 0])
            }
        }
        
        json_path = output_path.rsplit('.', 1)[0] + '.json'
        with open(json_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return json_path
    
    def generate_preview(self, scene_data, output_path):
        """Generate preview image of the 3D scene"""
        try:
            # Create a simple rendered preview
            mesh = self._create_trimesh_from_scene(scene_data)
            
            # Render scene to image
            scene = trimesh.Scene(mesh)
            
            # Set up camera
            bounds = np.array(scene_data.get('bounds', [[-1, -1, -1], [1, 1, 1]]))
            center = np.array(scene_data.get('center', [0, 0, 0]))
            
            # Calculate camera distance
            scene_size = np.linalg.norm(bounds[1] - bounds[0])
            camera_distance = scene_size * 2
            
            # Position camera
            camera_pos = center + np.array([camera_distance, camera_distance, camera_distance])
            scene.camera.look_at([center], camera_pos)
            
            # Render
            try:
                # Try to render with pyrender
                rendered = scene.save_image(resolution=[512, 512])
                
                # Save rendered image
                if isinstance(rendered, bytes):
                    with open(output_path, 'wb') as f:
                        f.write(rendered)
                else:
                    rendered.save(output_path)
                
            except:
                # Fallback to simple preview generation
                self._generate_simple_preview(scene_data, output_path)
            
            return output_path
            
        except Exception as e:
            print(f"Preview generation error: {e}")
            return self._generate_simple_preview(scene_data, output_path)
    
    def _generate_simple_preview(self, scene_data, output_path):
        """Generate simple preview image"""
        # Create a simple wireframe preview
        img_size = 512
        img = Image.new('RGB', (img_size, img_size), color='white')
        draw = ImageDraw.Draw(img)
        
        vertices = np.array(scene_data['vertices'])
        faces = np.array(scene_data['faces'])
        
        if len(vertices) == 0:
            # Draw placeholder
            draw.rectangle([img_size//4, img_size//4, 3*img_size//4, 3*img_size//4], 
                          outline='gray', fill='lightgray')
            draw.text((img_size//2-50, img_size//2), "3D Scene Preview", fill='black')
        else:
            # Project 3D points to 2D
            bounds = np.array(scene_data.get('bounds', [vertices.min(axis=0), vertices.max(axis=0)]))
            center = bounds.mean(axis=0)
            scale = img_size * 0.8 / max(bounds[1] - bounds[0])
            
            # Simple orthographic projection (top-down view)
            projected = vertices[:, [0, 2]]  # X-Z plane
            projected = (projected - center[[0, 2]]) * scale + img_size // 2
            
            # Draw wireframe
            for face in faces:
                if len(face) >= 3 and all(i < len(projected) for i in face):
                    points = [tuple(projected[i]) for i in face[:3]]
                    try:
                        draw.polygon(points, outline='blue', fill=None)
                    except:
                        pass
        
        img.save(output_path, 'JPEG', quality=85)
        return output_path
    
    def create_ar_metadata(self, scene_data):
        """Create AR-specific metadata"""
        metadata = {
            'ar_format_version': '1.0',
            'scene_type': 'memory_reconstruction',
            'recommended_scale': 1.0,
            'anchor_type': 'horizontal_plane',
            'lighting_estimation': True,
            'occlusion_enabled': True,
            'physics_enabled': False,
            'interaction_enabled': True
        }
        
        # Add scene-specific parameters
        bounds = scene_data.get('bounds', [])
        if bounds:
            scene_size = np.linalg.norm(np.array(bounds[1]) - np.array(bounds[0]))
            metadata['recommended_scale'] = min(2.0, max(0.1, 1.0 / scene_size))
        
        # Add lighting information
        lighting = scene_data.get('lighting', {})
        if lighting:
            metadata['lighting'] = {
                'use_environment_lighting': True,
                'light_intensity': lighting.get('intensity', 0.8),
                'shadow_intensity': lighting.get('shadow_strength', 0.3)
            }
        
        return metadata
    
    def export_for_web_ar(self, scene_data, output_dir):
        """Export scene for web-based AR (WebXR)"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Export GLB for web
            glb_path = os.path.join(output_dir, 'scene.glb')
            self.export_ar_scene(scene_data, glb_path)
            
            # Create web AR configuration
            ar_config = {
                'model_url': 'scene.glb',
                'scale': 1.0,
                'position': [0, 0, 0],
                'rotation': [0, 0, 0],
                'lighting': scene_data.get('lighting', {}),
                'metadata': self.create_ar_metadata(scene_data)
            }
            
            config_path = os.path.join(output_dir, 'ar_config.json')
            with open(config_path, 'w') as f:
                json.dump(ar_config, f, indent=2)
            
            # Create simple HTML viewer
            html_content = self._create_web_ar_viewer(ar_config)
            html_path = os.path.join(output_dir, 'viewer.html')
            with open(html_path, 'w') as f:
                f.write(html_content)
            
            return {
                'glb_path': glb_path,
                'config_path': config_path,
                'viewer_path': html_path
            }
            
        except Exception as e:
            print(f"Web AR export error: {e}")
            return None
    
    def _create_web_ar_viewer(self, ar_config):
        """Create simple HTML AR viewer"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AR Memory Viewer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://aframe.io/releases/1.4.0/aframe.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/AR-js-org/AR.js/aframe/build/aframe-ar.js"></script>
</head>
<body style="margin: 0; font-family: Arial;">
    <a-scene
        embedded
        arjs="sourceType: webcam; debugUIEnabled: false;"
        vr-mode-ui="enabled: false"
        renderer="logarithmicDepthBuffer: true;"
        loading-screen="enabled: false">
        
        <a-marker preset="hiro">
            <a-entity
                gltf-model="url({model_url})"
                scale="{scale} {scale} {scale}"
                position="{position[0]} {position[1]} {position[2]}"
                rotation="{rotation[0]} {rotation[1]} {rotation[2]}">
            </a-entity>
        </a-marker>
        
        <a-entity camera></a-entity>
    </a-scene>
    
    <div style="position: fixed; top: 10px; left: 10px; color: white; background: rgba(0,0,0,0.7); padding: 10px; border-radius: 5px;">
        <h3>AR Memory Viewer</h3>
        <p>Point camera at Hiro marker to view your memory</p>
    </div>
</body>
</html>
        """.format(
            model_url=ar_config['model_url'],
            scale=ar_config['scale'],
            position=ar_config['position'],
            rotation=ar_config['rotation']
        )
        
        return html_template