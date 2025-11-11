import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
import requests
from transformers import pipeline
import os

class DepthEstimator:
    def __init__(self):
        """Initialize depth estimation models"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize MiDaS depth estimation model
        try:
            self.depth_model = pipeline(
                "depth-estimation",
                model="Intel/dpt-large",
                device=0 if torch.cuda.is_available() else -1
            )
        except:
            try:
                self.depth_model = pipeline(
                    "depth-estimation", 
                    model="Intel/dpt-hybrid-midas",
                    device=0 if torch.cuda.is_available() else -1
                )
            except:
                self.depth_model = None
                print("Warning: Depth estimation model not available")
    
    def estimate_depth(self, image_path, enhanced=True):
        """Estimate depth map from single image"""
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            if self.depth_model is None:
                # Fallback to simple depth estimation
                return self._simple_depth_estimation(image_path)
            
            # Run depth estimation
            depth_result = self.depth_model(image)
            depth_map = np.array(depth_result['depth'])
            
            if enhanced:
                depth_map = self._enhance_depth_map(depth_map, image_path)
            
            # Normalize depth map
            depth_map = self._normalize_depth(depth_map)
            
            return depth_map
            
        except Exception as e:
            print(f"Error in depth estimation: {e}")
            return self._simple_depth_estimation(image_path)
    
    def _simple_depth_estimation(self, image_path):
        """Simple depth estimation fallback using image gradients"""
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        # Use Sobel gradients to estimate depth
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        
        # Combine gradients
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Invert gradient (higher gradient = closer to camera)
        depth_map = 255 - gradient_magnitude
        
        # Smooth the depth map
        depth_map = cv2.GaussianBlur(depth_map, (5, 5), 0)
        
        # Normalize
        depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
        
        return depth_map.astype(np.float32)
    
    def _enhance_depth_map(self, depth_map, image_path):
        """Enhance depth map using additional techniques"""
        # Load original image for edge-aware smoothing
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge-preserving smoothing
        depth_map_8bit = (depth_map * 255).astype(np.uint8)
        
        # Bilateral filter to preserve edges while smoothing
        smoothed = cv2.bilateralFilter(depth_map_8bit, 9, 75, 75)
        
        # Convert back to float
        enhanced_depth = smoothed.astype(np.float32) / 255.0
        
        # Fill holes using inpainting
        mask = (enhanced_depth == 0).astype(np.uint8)
        if np.sum(mask) > 0:
            enhanced_depth_8bit = (enhanced_depth * 255).astype(np.uint8)
            inpainted = cv2.inpaint(enhanced_depth_8bit, mask, 3, cv2.INPAINT_TELEA)
            enhanced_depth = inpainted.astype(np.float32) / 255.0
        
        return enhanced_depth
    
    def _normalize_depth(self, depth_map):
        """Normalize depth map to 0-1 range"""
        if depth_map.max() == depth_map.min():
            return np.zeros_like(depth_map)
        
        normalized = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
        return normalized.astype(np.float32)
    
    def create_point_cloud(self, image_path, depth_map, camera_params=None):
        """Create 3D point cloud from image and depth map"""
        # Load image
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        h, w = depth_map.shape
        
        # Default camera parameters if not provided
        if camera_params is None:
            fx = fy = w * 0.7  # Rough estimate
            cx, cy = w / 2, h / 2
        else:
            fx = camera_params.get('fx', w * 0.7)
            fy = camera_params.get('fy', w * 0.7)
            cx = camera_params.get('cx', w / 2)
            cy = camera_params.get('cy', h / 2)
        
        # Create coordinate grids
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        
        # Convert depth to actual Z coordinates (scale factor)
        z = depth_map * 10.0  # Scale depth to reasonable units
        
        # Calculate X and Y coordinates
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy
        
        # Stack coordinates
        points_3d = np.stack([x, y, z], axis=-1)
        
        # Reshape for point cloud
        points = points_3d.reshape(-1, 3)
        colors = image_rgb.reshape(-1, 3)
        
        # Filter out invalid points
        valid_mask = (z.reshape(-1) > 0) & (z.reshape(-1) < 100)
        points = points[valid_mask]
        colors = colors[valid_mask]
        
        return points, colors
    
    def estimate_surface_normals(self, depth_map):
        """Estimate surface normals from depth map"""
        # Calculate gradients
        grad_x = cv2.Sobel(depth_map, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(depth_map, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate normals (simplified)
        normal_x = -grad_x
        normal_y = -grad_y
        normal_z = np.ones_like(depth_map)
        
        # Normalize
        length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        length[length == 0] = 1  # Avoid division by zero
        
        normals = np.stack([
            normal_x / length,
            normal_y / length, 
            normal_z / length
        ], axis=-1)
        
        return normals
    
    def detect_depth_discontinuities(self, depth_map, threshold=0.1):
        """Detect depth discontinuities (object boundaries)"""
        # Calculate depth gradients
        grad_x = np.abs(cv2.Sobel(depth_map, cv2.CV_64F, 1, 0, ksize=3))
        grad_y = np.abs(cv2.Sobel(depth_map, cv2.CV_64F, 0, 1, ksize=3))
        
        # Combine gradients
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Threshold to find discontinuities
        discontinuities = gradient_magnitude > threshold
        
        return discontinuities.astype(np.uint8)