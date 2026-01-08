"""
angle_calculation.py

Utilities to compute joint angles and rolling stability metrics.
"""

import math
from typing import Tuple, Optional, Dict, List

def calculate_angle(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> Optional[float]:
    """
    Calculate the interior angle at point B formed by A-B-C.
    Returns angle in degrees (0-180).
    """
    try:
        ax, ay = a
        bx, by = b
        cx, cy = c
    except (TypeError, ValueError):
        return None

    # Vector BA (from B to A) and BC (from B to C)
    ba = (ax - bx, ay - by)
    bc = (cx - bx, cy - by)

    # Dot product
    dot_prod = ba[0] * bc[0] + ba[1] * bc[1]
    
    # Magnitudes
    mag_ba = math.hypot(ba[0], ba[1])
    mag_bc = math.hypot(bc[0], bc[1])

    if mag_ba == 0 or mag_bc == 0:
        return None

    # Cosine rule
    cosine_angle = dot_prod / (mag_ba * mag_bc)
    
    # Clamp value to handle floating point errors (must be -1 to 1)
    cosine_angle = max(-1.0, min(1.0, cosine_angle))
    
    angle_rad = math.acos(cosine_angle)
    return math.degrees(angle_rad)

class RollingStability:
    """
    Tracks recent angle history to detect shaking/instability.
    returns a score from 0 (stable) to 100 (unstable).
    """
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.history: Dict[str, List[float]] = {}

    def push(self, joint_name: str, angle: Optional[float]):
        if angle is None:
            return
        if joint_name not in self.history:
            self.history[joint_name] = []
        
        self.history[joint_name].append(angle)
        if len(self.history[joint_name]) > self.window_size:
            self.history[joint_name].pop(0)

    def stability_score(self, joint_name: str) -> float:
        data = self.history.get(joint_name, [])
        if len(data) < 3:
            return 0.0
        
        # Calculate standard deviation
        avg = sum(data) / len(data)
        variance = sum((x - avg) ** 2 for x in data) / len(data)
        stdev = math.sqrt(variance)
        
        # Normalize: Standard deviation of ~5 deg is "shaky" (score 100)
        # Standard deviation of < 1 deg is "stable" (score 0)
        return min(100.0, (stdev / 5.0) * 100.0)