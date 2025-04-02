import cv2
import numpy as np
from PIL import Image
import os
import logging
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing.image import img_to_array
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50
import torch.nn.functional as F

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EwasteAnalyzer:
    def __init__(self):
        # Device types and their base rewards
        self.device_rewards = {
            'smartphone': 100,
            'laptop': 200,
            'tablet': 150,
            'desktop': 250,
            'other': 50
        }

        # Condition multipliers
        self.condition_multipliers = {
            'good': 1.0,
            'okay': 0.7,
            'bad': 0.4,
            'worst': 0.2
        }

        # Initialize deep learning models
        self.setup_models()

        # Device-specific features
        self.device_features = {
            'smartphone': {
                'aspect_ratio_range': (0.4, 0.6),
                'size_range': (100, 500),
                'texture_features': ['smooth', 'metallic']
            },
            'laptop': {
                'aspect_ratio_range': (1.2, 1.5),
                'size_range': (500, 1000),
                'texture_features': ['keyboard', 'screen']
            },
            'tablet': {
                'aspect_ratio_range': (0.7, 0.9),
                'size_range': (300, 800),
                'texture_features': ['smooth', 'screen']
            },
            'desktop': {
                'aspect_ratio_range': (0.8, 1.2),
                'size_range': (800, 2000),
                'texture_features': ['box', 'ventilation']
            }
        }

    def setup_models(self):
        try:
            # Load MobileNetV2 for general object recognition
            self.mobilenet = MobileNetV2(weights='imagenet', include_top=True)
            
            # Load ResNet50 for detailed feature extraction
            self.resnet = resnet50(pretrained=True)
            self.resnet.eval()
            
            # Image preprocessing
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                  std=[0.229, 0.224, 0.225])
            ])
            
            logger.info("Deep learning models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise

    def analyze_device(self, image_path):
        """Analyze e-waste device from image using multiple AI models"""
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None

            # Load and preprocess image
            try:
                image = Image.open(image_path)
                img_array = np.array(image)
            except Exception as e:
                logger.error(f"Error opening image: {str(e)}")
                return None

            # Get device type using multiple methods
            device_type = self._classify_device(img_array)
            
            # Assess condition using multiple features
            condition = self._assess_condition(img_array)
            
            # Calculate reward
            base_reward = self.device_rewards.get(device_type, 50)
            reward = int(base_reward * self.condition_multipliers[condition])
            
            result = {
                'device_type': device_type,
                'condition': condition,
                'reward': reward,
                'confidence': self._calculate_confidence(device_type, condition)
            }
            
            logger.info(f"Successfully analyzed device: {device_type} in {condition} condition")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return None

    def _classify_device(self, image):
        """Classify device type using multiple AI models and computer vision"""
        try:
            # Convert to PIL Image for model input
            pil_image = Image.fromarray(image)
            
            # Get predictions from MobileNetV2
            mobile_pred = self._get_mobilenet_prediction(pil_image)
            
            # Get predictions from ResNet50
            resnet_pred = self._get_resnet_prediction(pil_image)
            
            # Get computer vision features
            cv_features = self._get_cv_features(image)
            
            # Combine predictions and features
            device_type = self._combine_predictions(mobile_pred, resnet_pred, cv_features)
            
            return device_type
            
        except Exception as e:
            logger.error(f"Error in device classification: {str(e)}")
            return 'other'

    def _get_mobilenet_prediction(self, image):
        """Get predictions from MobileNetV2 model"""
        try:
            # Preprocess image
            img_array = img_to_array(image)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            
            # Get predictions
            predictions = self.mobilenet.predict(img_array)
            decoded_predictions = decode_predictions(predictions, top=3)[0]
            
            return decoded_predictions
            
        except Exception as e:
            logger.error(f"Error in MobileNet prediction: {str(e)}")
            return []

    def _get_resnet_prediction(self, image):
        """Get predictions from ResNet50 model"""
        try:
            # Preprocess image
            img_tensor = self.transform(image)
            img_tensor = img_tensor.unsqueeze(0)
            
            # Get predictions
            with torch.no_grad():
                outputs = self.resnet(img_tensor)
                probabilities = F.softmax(outputs, dim=1)
                
            return probabilities[0].numpy()
            
        except Exception as e:
            logger.error(f"Error in ResNet prediction: {str(e)}")
            return np.zeros(1000)

    def _get_cv_features(self, image):
        """Extract computer vision features"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Get image dimensions
            height, width = image.shape[:2]
            aspect_ratio = width / height
            
            # Calculate texture features
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Calculate color features
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            color_std = np.std(hsv, axis=(0, 1))
            
            return {
                'aspect_ratio': aspect_ratio,
                'edge_density': edge_density,
                'color_std': color_std,
                'size': width * height
            }
            
        except Exception as e:
            logger.error(f"Error in CV feature extraction: {str(e)}")
            return {}

    def _combine_predictions(self, mobile_pred, resnet_pred, cv_features):
        """Combine predictions from multiple models and features"""
        try:
            # Initialize scores for each device type
            scores = {device: 0 for device in self.device_rewards.keys()}
            
            # Score based on MobileNet predictions
            for pred in mobile_pred:
                label = pred[1].lower()
                for device in scores:
                    if device in label:
                        scores[device] += pred[2]
            
            # Score based on ResNet predictions
            # (This would require mapping ImageNet classes to our device types)
            
            # Score based on computer vision features
            for device, features in self.device_features.items():
                aspect_ratio = cv_features.get('aspect_ratio', 0)
                size = cv_features.get('size', 0)
                
                # Check if features match device characteristics
                if (features['aspect_ratio_range'][0] <= aspect_ratio <= features['aspect_ratio_range'][1] and
                    features['size_range'][0] <= size <= features['size_range'][1]):
                    scores[device] += 0.3
            
            # Get device with highest score
            device_type = max(scores.items(), key=lambda x: x[1])[0]
            
            return device_type
            
        except Exception as e:
            logger.error(f"Error combining predictions: {str(e)}")
            return 'other'

    def _assess_condition(self, image):
        """Assess device condition using multiple features"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Calculate image quality metrics
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Apply Gaussian blur before edge detection
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Calculate texture features
            texture_score = self._calculate_texture_score(image)
            
            # Combine metrics for condition assessment
            if (brightness > 100 and contrast > 40 and 
                edge_density > 0.1 and texture_score > 0.8):
                return 'good'
            elif (brightness > 80 and contrast > 30 and 
                  edge_density > 0.05 and texture_score > 0.6):
                return 'okay'
            elif (brightness > 60 and contrast > 20 and 
                  edge_density > 0.02 and texture_score > 0.4):
                return 'bad'
            else:
                return 'worst'
                
        except Exception as e:
            logger.error(f"Error in condition assessment: {str(e)}")
            return 'worst'

    def _calculate_texture_score(self, image):
        """Calculate texture score using Gabor filters"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Apply Gabor filters
            ksize = 31
            sigma = 4.0
            theta = 0
            lambda_ = 10.0
            gamma = 0.5
            psi = 0
            
            kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lambda_, gamma, psi, ktype=cv2.CV_32F)
            filtered = cv2.filter2D(gray, cv2.CV_8UC3, kernel)
            
            # Calculate texture score
            texture_score = np.mean(filtered) / 255.0
            
            return texture_score
            
        except Exception as e:
            logger.error(f"Error calculating texture score: {str(e)}")
            return 0.0

    def _calculate_confidence(self, device_type, condition):
        """Calculate confidence score for the analysis"""
        try:
            # Base confidence on condition assessment
            condition_confidence = {
                'good': 0.9,
                'okay': 0.7,
                'bad': 0.5,
                'worst': 0.3
            }
            
            # Adjust confidence based on device type
            device_confidence = {
                'smartphone': 0.9,
                'laptop': 0.85,
                'tablet': 0.8,
                'desktop': 0.75,
                'other': 0.5
            }
            
            # Calculate final confidence
            confidence = (condition_confidence[condition] + device_confidence[device_type]) / 2
            
            return round(confidence * 100, 2)  # Convert to percentage
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 50.0 