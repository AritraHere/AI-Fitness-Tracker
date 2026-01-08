"""
pose_detection.py

Handles the MediaPipe Pose pipeline.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, Optional

class PoseDetector:
    def __init__(self, 
                 model_complexity: int = 1, 
                 min_detection_confidence: float = 0.5, 
                 min_tracking_confidence: float = 0.5):
        
        # STANDARD IMPORT
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize MediaPipe Pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.drawing_spec = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)

    def detect(self, frame: np.ndarray) -> Dict:
        """
        Processes frame and returns landmarks.
        Returns:
            dict with keys: 'image', 'landmarks'
            landmarks format: List of (x, y, z, visibility) tuples.
        """
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False 
        
        results = self.pose.process(image_rgb)
        
        image_rgb.flags.writeable = True
        annotated_image = frame.copy()
        landmarks_px = []
        
        if results.pose_landmarks:
            h, w, _ = frame.shape
            
            # Draw skeletons
            self.mp_drawing.draw_landmarks(
                annotated_image, 
                results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.drawing_spec,
                connection_drawing_spec=self.drawing_spec
            )
            
            # Convert to pixel coordinates
            for lm in results.pose_landmarks.landmark:
                landmarks_px.append((
                    int(lm.x * w), 
                    int(lm.y * h), 
                    lm.z, 
                    lm.visibility
                ))
        else:
            landmarks_px = None

        return {
            'image': annotated_image,
            'landmarks': landmarks_px
        }

    def close(self):
        self.pose.close()