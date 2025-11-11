import numpy as np
import cv2
import trimesh
import open3d as o3d
from PIL import Image
import json
import os

class SceneGenerator:
    def __init__(self):
        """Initialize 3D scene generation tools"""
        self.mesh_resolution = 0.01
        self.texture_size = 512
    
    def generate_3d_scene(self, image_path, depth_map, image_analysis, extend_background=False):
        """Generate 3D scene from image and depth map"""
        try:
            # Load image
            image = cv2.imread(image_path)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Create point cloud
            points, colors = self._create_point_cloud(image_rgb, depth_map, image_analysis)
            
            # Generate mesh from point cloud
            mesh_data = self._generate_mesh(points, colors)
            
            # Add background if requested
            if extend_background:
                mesh_data = self._extend_background(mesh_data, image_analysis)
            
            # Add lighting information
            mesh_data['lighting'] = self._extract_lighting_info(image_analysis)
            
            # Calculate scene complexity
            mesh_data['complexity_score'] = self._calculate_complexity(mesh_data)
            mesh_data['quality_score'] = self._calculate_scene_quality(mesh_data, image_analysis)
            
            return mesh_data
            
        except Exception as e:
            print(f"Error in scene generation: {e}")
            return {'error': str(e), 'quality_score': 0.5}
    
    def _create_point_cloud(self, image, depth_map, image_analysis):
        """Create 3D point cloud from image and depth"""
        h, w = depth_map.shape
        
        # Get camera parameters from analysis
        camera_info = image_analysis.get('camera', {})
        fx = camera_info.get('estimated_focal_length', w * 0.7)
        fy = fx  # Assume square pixels
        cx, cy = w / 2, h / 2
        
        # Create coordinate grids
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        
        # Convert to 3D coordinates
        z = depth_map * 5.0  # Scale depth
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy
        
        # Stack coordinates
        points_3d = np.stack([x, y, z], axis=-1)
        points = points_3d.reshape(-1, 3)
        colors = image.reshape(-1, 3) / 255.0
        
        # Filter valid points
        valid_mask = (z.reshape(-1) > 0.1) & (z.reshape(-1) < 20.0)
        points = points[valid_mask]
        colors = colors[valid_mask]
        
        return points, colors
    
    def _generate_mesh(self, points, colors):
        """Generate mesh from point cloud"""
        try:
            # Create Open3D point cloud
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points)
            pcd.colors = o3d.utility.Vector3dVector(colors)
            
            # Estimate normals
            pcd.estimate_normals()
            
            # Poisson surface reconstruction
            mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                pcd, depth=9, width=0, scale=1.1, linear_fit=False
            )
            
            # Convert to trimesh for easier manipulation
            vertices = np.asarray(mesh.vertices)
            faces = np.asarray(mesh.triangles)
            vertex_colors = np.asarray(mesh.vertex_colors)
            
            # Create trimesh object
            trimesh_obj = trimesh.Trimesh(
                vertices=vertices,
                faces=faces,
                vertex_colors=vertex_colors
            )
            
            # Simplify mesh if too complex
            if len(faces) > 50000:
                trimesh_obj = trimesh_obj.simplify_quadric_decimation(25000)
            
            mesh_data = {
                'vertices': trimesh_obj.vertices.tolist(),
                'faces': trimesh_obj.faces.tolist(),
                'vertex_colors': trimesh_obj.visual.vertex_colors[:, :3].tolist() if hasattr(trimesh_obj.visual, 'vertex_colors') else [],
                'vertex_count': len(trimesh_obj.vertices),
                'face_count': len(trimesh_obj.faces),
                'bounds': trimesh_obj.bounds.tolist(),
                'center': trimesh_obj.center_mass.tolist()
            }
            
            return mesh_data
            
        except Exception as e:
            print(f"Mesh generation error: {e}")
            # Fallback to simple mesh
            return self._create_simple_mesh(points, colors)
    
    def _create_simple_mesh(self, points, colors):
        """Create simple mesh as fallback"""
        # Subsample points for performance
        if len(points) > 10000:
            indices = np.random.choice(len(points), 10000, replace=False)
            points = points[indices]
            colors = colors[indices]
        
        # Create simple triangulation (Delaunay in 2D projection)
        points_2d = points[:, :2]  # Project to XY plane
        
        try:
            from scipy.spatial import Delaunay
            tri = Delaunay(points_2d)
            faces = tri.simplices
        except:
            # Even simpler fallback - create grid-based faces
            faces = []
            n_points = len(points)
            grid_size = int(np.sqrt(n_points))
            
            for i in range(grid_size - 1):
                for j in range(grid_size - 1):
                    if i * grid_size + j + grid_size + 1 < n_points:
                        # Create two triangles for each grid cell
                        faces.append([
                            i * grid_size + j,
                            i * grid_size + j + 1,
                            (i + 1) * grid_size + j
                        ])
                        faces.append([
                            i * grid_size + j + 1,
                            (i + 1) * grid_size + j + 1,
                            (i + 1) * grid_size + j
                        ])
            
            faces = np.array(faces)
        
        return {
            'vertices': points.tolist(),
            'faces': faces.tolist(),
            'vertex_colors': (colors * 255).astype(int).tolist(),
            'vertex_count': len(points),
            'face_count': len(faces),
            'bounds': [points.min(axis=0).tolist(), points.max(axis=0).tolist()],
            'center': points.mean(axis=0).tolist()
        }
    
    def _extend_background(self, mesh_data, image_analysis):
        """Extend background using AI inpainting techniques"""
        # This is a placeholder for background extension
        # In a full implementation, you would use generative models
        # to extend the scene beyond the original image boundaries
        
        vertices = np.array(mesh_data['vertices'])
        
        # Simple background extension - create a ground plane
        bounds = np.array(mesh_data['bounds'])
        center = np.array(mesh_data['center'])
        
        # Create ground plane vertices
        ground_y = bounds[0][1] - 1.0  # Below the scene
        ground_size = max(bounds[1][0] - bounds[0][0], bounds[1][2] - bounds[0][2]) * 2
        
        ground_vertices = [
            [center[0] - ground_size/2, ground_y, center[2] - ground_size/2],
            [center[0] + ground_size/2, ground_y, center[2] - ground_size/2],
            [center[0] + ground_size/2, ground_y, center[2] + ground_size/2],
            [center[0] - ground_size/2, ground_y, center[2] + ground_size/2]
        ]
        
        # Ground plane faces
        ground_faces = [
            [len(vertices), len(vertices) + 1, len(vertices) + 2],
            [len(vertices), len(vertices) + 2, len(vertices) + 3]
        ]
        
        # Ground plane colors (neutral gray)
        ground_colors = [[128, 128, 128]] * 4
        
        # Add to mesh data
        mesh_data['vertices'].extend(ground_vertices)
        mesh_data['faces'].extend([[f[0] + len(vertices), f[1] + len(vertices), f[2] + len(vertices)] for f in ground_faces])
        mesh_data['vertex_colors'].extend(ground_colors)
        mesh_data['vertex_count'] += 4
        mesh_data['face_count'] += 2
        
        return mesh_data
    
    def _extract_lighting_info(self, image_analysis):
        """Extract lighting information for 3D scene"""
        lighting_data = image_analysis.get('lighting', {})
        
        # Convert to 3D lighting parameters
        light_direction = lighting_data.get('estimated_light_direction', {'x': 0, 'y': -1})
        
        # Normalize and convert to 3D
        light_dir_3d = [
            light_direction['x'],
            -1.0,  # Assume light comes from above
            light_direction['y']
        ]
        
        # Normalize
        length = np.sqrt(sum(x**2 for x in light_dir_3d))
        if length > 0:
            light_dir_3d = [x / length for x in light_dir_3d]
        
        return {
            'direction': light_dir_3d,
            'intensity': min(1.0, lighting_data.get('mean_luminance', 128) / 255.0),
            'ambient': 0.3,
            'shadow_strength': lighting_data.get('shadow_ratio', 0.2)
        }
    
    def optimize_lighting(self, mesh_data, image_analysis):
        """Optimize lighting for better 3D appearance"""
        # This would implement advanced lighting optimization
        # For now, we'll just enhance the existing lighting data
        
        lighting = mesh_data.get('lighting', {})
        
        # Enhance lighting based on image analysis
        quality_score = image_analysis.get('quality_score', 0.8)
        
        # Adjust lighting intensity based on image quality
        lighting['intensity'] = min(1.0, lighting.get('intensity', 0.8) * (0.5 + quality_score * 0.5))
        
        # Adjust ambient lighting
        lighting['ambient'] = max(0.1, min(0.5, lighting.get('ambient', 0.3) * quality_score))
        
        mesh_data['lighting'] = lighting
        return mesh_data
    
    def _calculate_complexity(self, mesh_data):
        """Calculate scene complexity score"""
        vertex_count = mesh_data.get('vertex_count', 0)
        face_count = mesh_data.get('face_count', 0)
        
        # Normalize complexity (0-1 scale)
        vertex_complexity = min(1.0, vertex_count / 50000)
        face_complexity = min(1.0, face_count / 100000)
        
        return (vertex_complexity + face_complexity) / 2
    
    def _calculate_scene_quality(self, mesh_data, image_analysis):
        """Calculate overall scene quality"""
        image_quality = image_analysis.get('quality_score', 0.8)
        mesh_complexity = mesh_data.get('complexity_score', 0.5)
        
        # Combine factors
        quality = (image_quality * 0.6 + mesh_complexity * 0.4)
        
        return min(1.0, quality)