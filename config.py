"""
config.py

Configuration dictionaries for thresholds and modes.
"""

THRESHOLDS = {
    'squat': {
        # Angle 180 = Standing. Angle 70 = Deep Squat.
        'knee_angle_deep': 80,     # Must go below this to count as 'down'
        'knee_angle_high': 160,    # Must go above this to count as 'up' (reset)
        'knee_safe_min': 40,       # Safety floor
        'hip_min': 80,             # Hip flexion
        'back_min': 140,           # Keep back straight
        'pass_score': 70,
    },
    'pushup': {
        # Angle 180 = High Plank. Angle 90 = Low Plank.
        'elbow_target': 100,       # Must go below this (bend arms)
        'elbow_reset': 160,        # Must straighten arms to reset
        'elbow_safe_min': 40,
        'body_min': 160,           # Body should be straight line
        'pass_score': 75,
    },
    'bicep_curl': {
        # Angle 180 = Extended. Angle 40 = Curled.
        'curl_flexion_thresh': 60,    # Angle must be < this to count rep
        'curl_extension_thresh': 150, # Angle must be > this to reset rep
        'elbow_safe_min': 20,
        'pass_score': 60,
    }
}

MODES = {
    'beginner': {
        'squat': {'knee_angle_deep': 10},  # Add 10 deg (easier, don't need to go as deep: 80+10=90)
        'pushup': {'elbow_target': 10},    # Easier (100+10=110)
        'bicep_curl': {}
    },
    'advanced': {
        'squat': {'knee_angle_deep': 0},   # Standard
        'pushup': {'elbow_target': 0},
        'bicep_curl': {}
    }
}