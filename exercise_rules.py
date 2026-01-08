"""
exercise_rules.py

Rule-based posture checks for different exercises.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from angle_calculation import calculate_angle, RollingStability

@dataclass
class PoseCheckResult:
    correct: bool
    score: float
    messages: list
    warnings: list
    stability: Dict[str, float]

class ExerciseRule:
    def __init__(self, thresholds: Dict, rolling: RollingStability):
        self.thresholds = thresholds
        self.rolling = rolling

    def evaluate(self, landmarks) -> PoseCheckResult:
        raise NotImplementedError()

class SquatRule(ExerciseRule):
    def evaluate(self, landmarks) -> PoseCheckResult:
        msgs = []
        warns = []
        if landmarks is None:
            return PoseCheckResult(False, 0.0, ["No person detected"], [], {})

        L = landmarks
        # Indices: 23/24(hips), 25/26(knees), 27/28(ankles), 11/12(shoulders)
        # Using simple average for left/right side
        hip = ((L[23][0]+L[24][0])/2, (L[23][1]+L[24][1])/2)
        knee = ((L[25][0]+L[26][0])/2, (L[25][1]+L[26][1])/2)
        ankle = ((L[27][0]+L[28][0])/2, (L[27][1]+L[28][1])/2)
        shoulder = ((L[11][0]+L[12][0])/2, (L[11][1]+L[12][1])/2)

        knee_angle = calculate_angle(hip, knee, ankle)
        back_angle = calculate_angle(shoulder, hip, knee)

        self.rolling.push('knee', knee_angle)
        
        score = 0.0
        checks = 0

        # --- Squat Logic ---
        if knee_angle is not None:
            checks += 1
            # If angle is between SAFE_MIN and DEEP_THRESHOLD, it's a good squat hold
            target = self.thresholds.get('knee_angle_deep', 80)
            
            # Feedback: If user is trying to squat but angle is still 150, say "Go Lower"
            # If user is at 60, they are deep enough (Good)
            if knee_angle > target + 30: 
                # Only warn "Go Lower" if they are clearly attempting it (e.g. < 160)
                if knee_angle < 160: 
                    msgs.append('Go Lower')
            
            if knee_angle <= target + 10: # Close to target or deeper
                score += 1.0

            if knee_angle < self.thresholds.get('knee_safe_min', 40):
                warns.append('Knee stress!')

        if back_angle is not None:
            checks += 1
            if back_angle >= self.thresholds.get('back_min', 140):
                score += 1.0
            else:
                msgs.append('Keep Back Straight')

        final_score = (score / max(1, checks)) * 100.0
        return PoseCheckResult(final_score > 60, final_score, msgs, warns, {})


class PushupRule(ExerciseRule):
    def evaluate(self, landmarks) -> PoseCheckResult:
        msgs = []
        warns = []
        if landmarks is None:
            return PoseCheckResult(False, 0.0, ["No person detected"], [], {})

        L = landmarks
        shoulder = ((L[11][0]+L[12][0])/2, (L[11][1]+L[12][1])/2)
        elbow = ((L[13][0]+L[14][0])/2, (L[13][1]+L[14][1])/2)
        wrist = ((L[15][0]+L[16][0])/2, (L[15][1]+L[16][1])/2)
        hip = ((L[23][0]+L[24][0])/2, (L[23][1]+L[24][1])/2)
        ankle = ((L[27][0]+L[28][0])/2, (L[27][1]+L[28][1])/2)

        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        body_angle = calculate_angle(shoulder, hip, ankle)

        score = 0.0
        checks = 0

        if elbow_angle is not None:
            checks += 1
            target = self.thresholds.get('elbow_target', 100)
            
            # If angle is large (> 150), arms are straight
            # If angle is small (< target), reps are good
            if elbow_angle <= target:
                score += 1.0
            elif elbow_angle < 150: # Mid-rep but not deep enough
                msgs.append('Go Lower')

        if body_angle is not None:
            checks += 1
            if body_angle >= self.thresholds.get('body_min', 160):
                score += 1.0
            else:
                msgs.append('Fix Hip Sag')

        final_score = (score / max(1, checks)) * 100.0
        return PoseCheckResult(final_score > 60, final_score, msgs, warns, {})

class BicepCurlRule(ExerciseRule):
    def evaluate(self, landmarks) -> PoseCheckResult:
        msgs = []
        warns = []

        if landmarks is None:
            return PoseCheckResult(False, 0.0, ["No person detected"], [], {})

        L = landmarks

        def arm_angle(s, e, w):
            ang = calculate_angle(L[s][:2], L[e][:2], L[w][:2])
            return ang

        # Left & Right elbow angles
        left = arm_angle(11, 13, 15)
        right = arm_angle(12, 14, 16)

        angles = [a for a in [left, right] if a is not None]
        if not angles:
            return PoseCheckResult(False, 0.0, ["Arms not visible"], [], {})

        active_angle = min(angles)

        checks = 0
        score = 0.0

        # 1️⃣ Curl depth check
        checks += 1
        flex_thresh = self.thresholds.get('curl_flexion_thresh', 60)

        if active_angle <= flex_thresh:
            score += 1.0
        else:
            msgs.append("Curl higher")

        # 2️⃣ Extension check (no half reps)
        checks += 1
        ext_thresh = self.thresholds.get('curl_extension_thresh', 150)

        if active_angle >= ext_thresh:
            score += 1.0
        else:
            msgs.append("Fully extend arm")

        # 3️⃣ Safety
        if active_angle < self.thresholds.get('elbow_safe_min', 20):
            warns.append("Elbow stress!")

        final_score = (score / checks) * 100.0
        correct = final_score >= self.thresholds.get('pass_score', 60)

        return PoseCheckResult(correct, final_score, msgs, warns, {})