import time
import cv2
import numpy as np

from pose_detection import PoseDetector
from angle_calculation import calculate_angle, RollingStability
from exercise_rules import SquatRule, PushupRule, BicepCurlRule
from session_summary import SessionSummary
import config

# =========================
# UI & STATE
# =========================
BUTTON_DEFS = [
    {'label': 'Squat', 'action': 'squat'},
    {'label': 'Push-up', 'action': 'pushup'},
    {'label': 'Bicep Curl', 'action': 'bicep_curl'},
    {'label': 'Mode: Beg', 'action': 'toggle_mode'},
    {'label': 'Quit', 'action': 'quit'},
]

class AppState:
    def __init__(self):
        self.exercise = 'squat'
        self.mode = 'beginner'
        self.running = True
        self.rules = {}
        self.counters = {}
        self.summaries = {}
        self.detector = PoseDetector()
        
        # Initialize
        self.refresh_rules()

    def refresh_rules(self):
        # Factory to create rules based on current mode
        base_thresholds = config.THRESHOLDS
        mode_mods = config.MODES.get(self.mode, {})
        
        def apply_mod(base, mods):
            t = base.copy()
            for k, v in mods.items():
                if k in t: t[k] += v 
            return t

        self.rules = {
            'squat': SquatRule(apply_mod(base_thresholds['squat'], mode_mods.get('squat', {})), RollingStability()),
            'pushup': PushupRule(apply_mod(base_thresholds['pushup'], mode_mods.get('pushup', {})), RollingStability()),
            'bicep_curl': BicepCurlRule(apply_mod(base_thresholds['bicep_curl'], mode_mods.get('bicep_curl', {})), RollingStability()),
        }
        
        # Reset counters/summaries if needed, or keep them persistent
        if not self.counters:
            self.counters = {k: RepCounter() for k in self.rules}
            self.summaries = {k: SessionSummary() for k in self.rules}

class RepCounter:
    """
    Generic State Machine for Rep counting.
    State 0: Rest (Extended/Standing)
    State 1: Peak (Flexed/Deep)
    """
    def __init__(self):
        self.in_peak = False
    
    def process(self, val_now, thresh_enter_peak, thresh_exit_peak):
        """
        Returns True if a full rep (Rest -> Peak -> Rest) just completed.
        """
        completed_rep = False
        
        # Transition to Peak (Down/Flexed)
        if not self.in_peak and val_now < thresh_enter_peak:
            self.in_peak = True
            
        # Transition to Rest (Up/Extended)
        elif self.in_peak and val_now > thresh_exit_peak:
            self.in_peak = False
            completed_rep = True
            
        return completed_rep

def draw_ui(frame, app_state: AppState, result):
    # Overlay Box
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 80), (30, 30, 30), -1)
    
    # Stats
    ex = app_state.exercise
    reps = app_state.summaries[ex].total_reps
    score = int(result.score) if result else 0
    
    cv2.putText(frame, f"{ex.upper()} ({app_state.mode})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Reps: {reps}", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.putText(frame, f"Form: {score}%", (200, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Feedback Messages
    if result:
        y = 30
        for msg in result.messages:
            cv2.putText(frame, msg, (400, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            y += 30
        for warn in result.warnings:
            cv2.putText(frame, warn, (400, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Buttons
    h, w, _ = frame.shape
    btn_w, btn_h = 110, 40
    start_x = 10
    start_y = h - 50
    
    for i, btn in enumerate(BUTTON_DEFS):
        x1 = start_x + (i * (btn_w + 5))
        y1 = start_y
        x2 = x1 + btn_w
        y2 = y1 + btn_h
        
        # Store coords for click handling
        btn['coords'] = (x1, y1, x2, y2)
        
        color = (0, 120, 255) if btn['action'] == app_state.exercise else (100, 100, 100)
        if btn['action'] == 'toggle_mode': color = (100, 0, 100)
        if btn['action'] == 'quit': color = (0, 0, 200)
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        
        # Dynamic label for Mode button
        label = btn['label']
        if btn['action'] == 'toggle_mode':
            label = f"Mode: {app_state.mode[:3].upper()}"
            
        cv2.putText(frame, label, (x1+5, y1+25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        app_state = param
        for btn in BUTTON_DEFS:
            x1, y1, x2, y2 = btn.get('coords', (0,0,0,0))
            if x1 <= x <= x2 and y1 <= y <= y2:
                act = btn['action']
                if act == 'quit':
                    app_state.running = False
                elif act == 'toggle_mode':
                    app_state.mode = 'advanced' if app_state.mode == 'beginner' else 'beginner'
                    app_state.refresh_rules()
                else:
                    app_state.exercise = act

def main():
    app = AppState()
    cap = cv2.VideoCapture(0)
    
    cv2.namedWindow("Fitness Tracker")
    cv2.setMouseCallback("Fitness Tracker", on_mouse, app)
    
    while app.running:
        ret, frame = cap.read()
        if not ret: break
        
        # Detection
        data = app.detector.detect(frame)
        frame = data['image']
        landmarks = data['landmarks']
        
        ex = app.exercise
        rule = app.rules[ex]
        
        # Evaluate Logic
        result = rule.evaluate(landmarks)
        
        # Rep Counting Logic
        if landmarks:
            # Calculate the primary angle for the current exercise
            angle = None
            if ex == 'squat': # Hip-Knee-Ankle
                angle = calculate_angle(landmarks[23][:2], landmarks[25][:2], landmarks[27][:2])
                thresh_enter = rule.thresholds['knee_angle_deep']
                thresh_exit = rule.thresholds['knee_angle_high']
                
            elif ex == 'pushup': # Shoulder-Elbow-Wrist
                angle = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
                thresh_enter = rule.thresholds['elbow_target']
                thresh_exit = rule.thresholds['elbow_reset']
                
            elif ex == 'bicep_curl': # Shoulder-Elbow-Wrist (taking min of left/right)
                la = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
                ra = calculate_angle(landmarks[12][:2], landmarks[14][:2], landmarks[16][:2])
                # Use the arm that is more flexed (active)
                if la and ra: angle = min(la, ra)
                elif la: angle = la
                elif ra: angle = ra
                
                thresh_enter = rule.thresholds['curl_flexion_thresh']
                thresh_exit = rule.thresholds['curl_extension_thresh']

            # Update Counter
            if angle is not None:
                if app.counters[ex].process(angle, thresh_enter, thresh_exit):
                    app.summaries[ex].push_rep(result.correct, result.score)

        draw_ui(frame, app, result)
        cv2.imshow("Fitness Tracker", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    app.detector.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()