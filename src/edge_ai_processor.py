"""
Edge AI Processor Module
Real-time object detection and hazard identification using YOLOv8.
Replaces previous simulation module.
"""
import logging
import cv2
import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os

# Import YOLO from ultralytics
try:
    from ultralytics import YOLO
except ImportError:
    # Fallback/Instruction if not installed, though we tried to install it.
    print("Ultralytics not installed. Please run: pip install ultralytics")
    YOLO = None

logger = logging.getLogger(__name__)

class EdgeAIProcessor:
    """
    Real-time Edge AI processing using YOLOv8.
    Detects objects in video frames and identifies potential hazards.
    """
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        self.is_initialized = False
        
        # Hazard definitions (mapping YOLO classes to hazard types)
        # COCO classes: 0:person, 1:bicycle, 2:car, 3:motorcycle, 5:bus, 7:truck, 9:traffic light, 11:stop sign
        self.hazard_classes = {
            0: "pedestrian_on_road",
            1: "cyclist_on_road",
            2: "stationary_vehicle", # Context dependent
            3: "motorcycle",
            5: "bus",
            7: "truck",
            # We can add more specific training for potholes later
        }
        
        self.risk_scores = {
            "pedestrian_on_road": 0.8,
            "cyclist_on_road": 0.6,
            "stationary_vehicle": 0.5,
            "truck": 0.4,
            "pothole": 0.9 # Future custom class
        }

    def _initialize_model(self):
        """Initialize the YOLOv8 model"""
        if YOLO:
            try:
                logger.info(f"Loading YOLOv8 model from {self.model_path}")
                self.model = YOLO(self.model_path)
                self.is_initialized = True
                logger.info("Edge AI Model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize YOLO model: {e}")
                self.is_initialized = False
        else:
            logger.error("Ultralytics library not available. Edge AI will not function.")

    def process_frame(self, frame_data: bytes, format: str = "jpg") -> Dict[str, Any]:
        """
        Process a single image frame for hazards.
        
        Args:
            frame_data: Raw bytes of the image
            format: Image format (jpg, png)
            
        Returns:
            Dict containing detected hazards and risk assessment
        """
        if not self.is_initialized:
            self._initialize_model()
            
        if not self.is_initialized or self.model is None:
            return {"error": "Model not initialized", "hazards": []}
            
        try:
            # Decode image bytes to OpenCV format
            nparr = np.frombuffer(frame_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {"error": "Failed to decode image", "hazards": []}

            # Run inference
            results = self.model(img, verbose=False)
            
            hazards = []
            max_risk = 0.0
            
            # Process detections
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Filter for known hazard classes with high confidence
                    if cls_id in self.hazard_classes and conf > 0.4:
                        hazard_type = self.hazard_classes[cls_id]
                        
                        # Simple logic: detected objects are potential hazards depending on context
                        # In a real app, we'd check if they are *in the lane* or *stationary*.
                        # For MVP, reporting presence is the "Real" step over mock random data.
                        
                        risk = self.risk_scores.get(hazard_type, 0.3)
                        
                        hazard = {
                            "type": hazard_type,
                            "confidence": conf,
                            "bbox": box.xyxy[0].tolist(), # [x1, y1, x2, y2]
                            "risk_score": risk
                        }
                        hazards.append(hazard)
                        max_risk = max(max_risk, risk)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "hazards_detected": len(hazards),
                "hazards": hazards,
                "overall_risk_score": max_risk,
                "processing_time_ms": results[0].speed['inference']
            }
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return {"error": str(e), "hazards": []}

    def analyze_driver_behavior(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze driver behavior based on telemetry (speed, g-force, etc.).
        This is distinct from visual processing but part of Edge AI.
        Running locally on the backend for this architecture phase.
        """
        # Real logic: Threshold checking
        # In production, this would use a TFLite model on the phone, 
        # but here we process the raw data sent by the app.
        
        speed = telemetry_data.get("speed_kmh", 0)
        acceleration = telemetry_data.get("acceleration_g", 0)
        braking = telemetry_data.get("braking_g", 0)
        swerving = telemetry_data.get("turn_rate_deg_s", 0)
        
        issues = []
        score = 100
        
        if speed > 120:
            issues.append("Excessive Speeding")
            score -= 20
        elif speed > 100:
            issues.append("Speeding")
            score -= 10
            
        if abs(acceleration) > 0.4:
            issues.append("Harsh Acceleration")
            score -= 15
            
        if abs(braking) > 0.6:
            issues.append("Harsh Braking")
            score -= 15
            
        if abs(swerving) > 30:
            issues.append("Aggressive Cornering")
            score -= 15
            
        return {
            "driver_score": max(0, score),
            "detected_issues": issues,
            "status": "unsafe" if score < 70 else "safe",
            "timestamp": datetime.now().isoformat()
        }

# Global instance
edge_ai = EdgeAIProcessor(model_path="yolov8n.pt")