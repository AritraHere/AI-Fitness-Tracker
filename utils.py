import cv2

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

def draw_overlay(frame, result, reps, mode, exercise_name):
    # Overlay Box (Top Banner)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 80), (30, 30, 30), -1)
    
    # Stats
    score = int(result.score) if result else 0
    
    cv2.putText(frame, f"{exercise_name.upper()} ({mode})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
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