import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image

# Import your modules
from pose_detection import PoseDetector
from exercise_rules import SquatRule, PushupRule, BicepCurlRule
from angle_calculation import RollingStability, calculate_angle
from session_summary import SessionSummary
import config

# Import utilities
from utils import RepCounter, draw_overlay

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Fitness Pro",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
        }
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }
        div.css-1r6slb0 {
            background-color: #1f2937;
            border: 1px solid #374151;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .title-text {
            font-size: 2.5rem;
            font-weight: 700;
            color: #58a6ff;
            text-align: center;
            margin-bottom: 20px;
            text-shadow: 0px 0px 10px rgba(88, 166, 255, 0.5);
        }
        .stImage > img {
            border-radius: 15px;
            border: 2px solid #58a6ff;
            box-shadow: 0 0 20px rgba(88, 166, 255, 0.3);
        }
        .stButton > button {
            background-color: #238636;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 24px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #2ea043;
            box-shadow: 0 0 10px rgba(46, 160, 67, 0.5);
        }
    </style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'counters' not in st.session_state:
    st.session_state.counters = {
        'squat': RepCounter(),
        'pushup': RepCounter(),
        'bicep_curl': RepCounter(),
    }

if 'summary' not in st.session_state:
    st.session_state.summary = {
        'squat': SessionSummary(),
        'pushup': SessionSummary(),
        'bicep_curl': SessionSummary()
    }

# --- Load Detector ---
@st.cache_resource
def load_detector():
    return PoseDetector()

detector = load_detector()

# --- Helper Functions ---
def get_rule(exercise, mode):
    base_thresholds = config.THRESHOLDS
    mode_mods = config.MODES.get(mode, {})
    
    def apply_mod(base, mods):
        t = base.copy()
        for k, v in mods.items():
            if k in t: t[k] += v 
        return t

    if exercise == 'squat':
        return SquatRule(apply_mod(base_thresholds['squat'], mode_mods.get('squat', {})), RollingStability())
    elif exercise == 'pushup':
        return PushupRule(apply_mod(base_thresholds['pushup'], mode_mods.get('pushup', {})), RollingStability())
    elif exercise == 'bicep_curl':
        return BicepCurlRule(apply_mod(base_thresholds['bicep_curl'], mode_mods.get('bicep_curl', {})), RollingStability())
    return None

def process_reps(exercise, landmarks, rule):
    """
    Calculates angles, updates RepCounter, and returns (did_rep_finish, current_angle).
    """
    angle = None
    thresh_enter = 0
    thresh_exit = 0

    if exercise == 'squat':
        angle = calculate_angle(landmarks[23][:2], landmarks[25][:2], landmarks[27][:2])
        thresh_enter = rule.thresholds.get('knee_angle_deep', 80)
        thresh_exit = rule.thresholds.get('knee_angle_high', 160)
        
    elif exercise == 'pushup':
        angle = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
        thresh_enter = rule.thresholds.get('elbow_target', 100)
        thresh_exit = rule.thresholds.get('elbow_reset', 160)
        
    elif exercise == 'bicep_curl': 
        # --- ROBUST AUTO-DETECT ---
        l_angle = calculate_angle(landmarks[11][:2], landmarks[13][:2], landmarks[15][:2])
        r_angle = calculate_angle(landmarks[12][:2], landmarks[14][:2], landmarks[16][:2])
        
        # Use the arm that is "working" (closest to the flexion target)
        if l_angle and r_angle:
            angle = min(l_angle, r_angle)
        elif l_angle:
            angle = l_angle
        elif r_angle:
            angle = r_angle
            
        # Hard-coded, relaxed thresholds for better usability
        thresh_enter = 95   
        thresh_exit = 150   

    rep_finished = False
    if angle is not None:
        counter = st.session_state.counters[exercise]
        rep_finished = counter.process(angle, thresh_enter, thresh_exit)
        
    return rep_finished, angle

# --- Sidebar UI ---
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    mode = st.radio("Difficulty Level", ["Beginner", "Advanced"], index=0).lower()
    st.divider()
    
    st.markdown("### Choose Workout")
    exercise_choice = st.selectbox("Exercise", ["squat", "pushup", "bicep_curl"])
    
    st.divider()
    run_app = st.toggle("🔴 Start Camera", value=False)
    
    st.divider()
    if st.button("🔄 Reset Stats"):
        st.session_state.counters[exercise_choice] = RepCounter()
        st.session_state.summary[exercise_choice] = SessionSummary()
        st.toast("Stats reset successfully!", icon="✅")

# --- Main Dashboard ---
st.markdown('<p class="title-text">🏋️ AI Fitness Trainer Pro</p>', unsafe_allow_html=True)

col_left, col_video, col_right = st.columns([1, 3, 1])

# Placeholders
with col_left:
    st.markdown("### 📊 Live Stats")
    metric_reps = st.empty()
    st.markdown("---")
    st.markdown("**Target Muscle:**")
    st.info(f"{exercise_choice.replace('_', ' ').title()}")

with col_video:
    st_frame = st.empty()

with col_right:
    st.markdown("### 🎯 Form Score")
    score_bar = st.progress(0)
    score_text = st.empty()
    st.markdown("---")
    feedback_box = st.empty()

# --- Main Logic Loop ---
if run_app:
    cap = cv2.VideoCapture(0)
    rule = get_rule(exercise_choice, mode)

    while cap.isOpened() and run_app:
        ret, frame = cap.read()
        if not ret:
            st.error("Camera not accessible")
            break

        # 1. Detection
        detection_result = detector.detect(frame)
        image = detection_result['image']
        landmarks = detection_result['landmarks']

        # 2. Evaluate Form (Backend Check)
        pose_result = rule.evaluate(landmarks)

        # 3. Process Reps & Get Angle
        current_angle = 180 
        if landmarks:
            just_finished_rep, current_angle = process_reps(exercise_choice, landmarks, rule)
            
            if just_finished_rep:
                st.session_state.summary[exercise_choice].push_rep(pose_result.correct, pose_result.score)

        # --- SANITY CHECK PROTOCOL (CRITICAL FIXES) ---

        # A. Filter "Phantom Squeeze" Errors
        # If angle > 50, it is IMPOSSIBLE to squeeze too hard. Delete the message.
        if exercise_choice == 'bicep_curl' and current_angle > 50:
            if pose_result.messages:
                pose_result.messages = [m for m in pose_result.messages if "squeeze" not in m.lower()]

        # B. Conflict Resolution (Score 100% vs Error Message)
        # If there is an error message, Score CANNOT be 100%. Force it down.
        if pose_result.messages and pose_result.score > 90:
            pose_result.score = 75  # Downgrade score to reflect the error

        # C. Idle Detection
        is_idle = False
        if exercise_choice == 'bicep_curl' and current_angle > 155: is_idle = True
        elif exercise_choice == 'squat' and current_angle > 165: is_idle = True
        elif exercise_choice == 'pushup' and current_angle > 165: is_idle = True

        # 4. Update UI Elements
        current_reps = st.session_state.summary[exercise_choice].total_reps
        
        # -- Stats Column --
        metric_reps.metric(label="Total Reps", value=current_reps, delta="Count")
        
        # -- Feedback Column (Strict Logic) --
        
        # Scenario 1: User hasn't started yet (0 reps)
        if current_reps == 0:
            score_bar.progress(0)
            score_text.markdown("**Status: Ready to Start**")
            if is_idle:
                feedback_box.info("ℹ️ Perform your first rep to start tracking")
            else:
                feedback_box.info("ℹ️ Go deeper to trigger count")

        # Scenario 2: User is resting (Idle)
        elif is_idle:
            score_bar.progress(0) # Hide score while resting
            score_text.markdown("**Status: Resting**")
            feedback_box.info("⬇️ Resetting for next rep...")

        # Scenario 3: Active Rep
        else:
            score_val = int(pose_result.score)
            score_bar.progress(score_val)
            score_text.markdown(f"**Form Consistency: {score_val}%**")
            
            if pose_result.messages:
                # If we have messages (that survived the filter), show them!
                feedback_box.warning(f"⚠️ {pose_result.messages[0]}")
            elif score_val < 80:
                feedback_box.info("ℹ️ Keep form steady")
            else:
                feedback_box.success("✅ Perfect Form!")

        # -- Video Overlay --
        draw_overlay(image, pose_result, current_reps, mode, exercise_choice)
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        st_frame.image(image, channels="RGB", use_container_width=True)

    cap.release()
else:
    with col_video:
        st.markdown(
            """
            <div style="text-align: center; padding: 50px; border: 2px dashed #444; border-radius: 15px;">
                <h3>👋 Ready to workout?</h3>
                <p>Select your exercise from the sidebar and toggle 'Start Camera'</p>
            </div>
            """, 
            unsafe_allow_html=True
        )