import cv2
import numpy as np
from PIL import Image
import torch
from transformers import pipeline
from skimage import feature, measure
import json

class ImageProcessor:
    def __init__(self):
        """Initialize image processing models and tools"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize semantic segmentation model
        try:
            self.segmentation_model = pipeline(
                "image-segmentation",
                model="facebook/detr-resnet-50-panoptic",
                device=0 if torch.cuda.is_available() else -1
            )
        except:
            self.segmentation_model = None
            print("Warning: Segmentation model not available")
    
    def analyze_image(self, image_path):
        """Comprehensive image analysis for 3D reconstruction"""
        try:
            # Load image
            image = cv2.imread(image_path)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            analysis = {
                'resolution': image.shape[:2],
                'aspect_ratio': image.shape[1] / image.shape[0],
                'file_path': image_path
            }
            
            # Basic image quality metrics
            analysis.update(self._analyze_quality(image))
            
            # Detect objects and people
            analysis.update(self._detect_objects(pil_image))
            
            # Analyze lighting conditions
            analysis.update(self._analyze_lighting(image))
            
            # Detect edges and features
            analysis.update(self._analyze_features(image))
            
            # Estimate camera parameters
            analysis.update(self._estimate_camera_params(image))
            
            return analysis
            
        except Exception as e:
            print(f"Error in image analysis: {e}")
            return {'error': str(e), 'quality_score': 0.5}
    
    def _analyze_quality(self, image):
        """Analyze image quality metrics"""
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate sharpness using Laplacian variance
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calculate brightness
        brightness = np.mean(gray)
        
        # Calculate contrast
        contrast = gray.std()
        
        # Noise estimation
        noise_level = self._estimate_noise(gray)
        
        # Overall quality score (0-1)
        quality_score = min(1.0, (
            min(sharpness / 1000, 1.0) * 0.3 +
            min(contrast / 50, 1.0) * 0.3 +
            (1 - min(noise_level / 20, 1.0)) * 0.2 +
            (1 - abs(brightness - 128) / 128) * 0.2
        ))
        
        return {
            'sharpness': float(sharpness),
            'brightness': float(brightness),
            'contrast': float(contrast),
            'noise_level': float(noise_level),
            'quality_score': float(quality_score)
        }
    
    def _estimate_noise(self, gray_image):
        """Estimate noise level in image"""
        # Use Laplacian to estimate noise
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        noise = laplacian.var()
        return noise 
   
    def _detect_objects(self, pil_image):
        """Detect objects and people in the image"""
        objects_data = {
            'objects': [],
            'people_count': 0,
            'main_subjects': []
        }
        
        if self.segmentation_model is None:
            return objects_data
        
        try:
            # Run segmentation
            segments = self.segmentation_model(pil_image)
            
            for segment in segments:
                label = segment['label']
                score = segment.get('score', 0)
                
                if score > 0.5:  # Confidence threshold
                    objects_data['objects'].append({
                        'label': label,
                        'confidence': float(score)
                    })
                    
                    if 'person' in label.lower():
                        objects_data['people_count'] += 1
                        objects_data['main_subjects'].append(label)
            
        except Exception as e:
            print(f"Object detection error: {e}")
        
        return objects_data
    
    def _analyze_lighting(self, image):
        """Analyze lighting conditions in the image"""
        # Convert to LAB color space for better lighting analysis
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # Calculate lighting metrics
        mean_luminance = np.mean(l_channel)
        luminance_std = np.std(l_channel)
        
        # Detect shadows and highlights
        shadows = np.sum(l_channel < 50) / l_channel.size
        highlights = np.sum(l_channel > 200) / l_channel.size
        
        # Estimate light direction (simplified)
        gradient_x = cv2.Sobel(l_channel, cv2.CV_64F, 1, 0, ksize=3)
        gradient_y = cv2.Sobel(l_channel, cv2.CV_64F, 0, 1, ksize=3)
        
        light_direction = {
            'x': float(np.mean(gradient_x)),
            'y': float(np.mean(gradient_y))
        }
        
        return {
            'lighting': {
                'mean_luminance': float(mean_luminance),
                'luminance_variance': float(luminance_std),
                'shadow_ratio': float(shadows),
                'highlight_ratio': float(highlights),
                'estimated_light_direction': light_direction
            }
        }
    
    def _analyze_features(self, image):
        """Analyze image features for 3D reconstruction"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect corners using Harris corner detection
        corners = cv2.cornerHarris(gray, 2, 3, 0.04)
        corner_count = np.sum(corners > 0.01 * corners.max())
        
        # Detect edges using Canny
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        line_count = len(lines) if lines is not None else 0
        
        return {
            'features': {
                'corner_count': int(corner_count),
                'edge_density': float(edge_density),
                'line_count': int(line_count)
            }
        }
    
    def _estimate_camera_params(self, image):
        """Estimate camera parameters from image"""
        height, width = image.shape[:2]
        
        # Estimate focal length (rough approximation)
        # Assuming 35mm equivalent and typical viewing angles
        focal_length_35mm = 50  # Default assumption
        focal_length_pixels = (focal_length_35mm / 36) * width  # 36mm is full frame width
        
        # Estimate principal point (usually center of image)
        principal_point = (width / 2, height / 2)
        
        return {
            'camera': {
                'estimated_focal_length': float(focal_length_pixels),
                'principal_point': principal_point,
                'image_dimensions': (width, height)
            }
        }
    
    def preprocess_for_depth(self, image_path, target_size=(384, 384)):
        """Preprocess image for depth estimation"""
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize while maintaining aspect ratio
        h, w = image_rgb.shape[:2]
        if w > h:
            new_w, new_h = target_size[0], int(h * target_size[0] / w)
        else:
            new_w, new_h = int(w * target_size[1] / h), target_size[1]
        
        resized = cv2.resize(image_rgb, (new_w, new_h))
        
        # Pad to target size
        pad_h = (target_size[1] - new_h) // 2
        pad_w = (target_size[0] - new_w) // 2
        
        padded = np.pad(resized, 
                       ((pad_h, target_size[1] - new_h - pad_h),
                        (pad_w, target_size[0] - new_w - pad_w),
                        (0, 0)), 
                       mode='constant', constant_values=0)
        
        # Normalize
        normalized = padded.astype(np.float32) / 255.0
        
        return normalized, (pad_w, pad_h, new_w, new_h)