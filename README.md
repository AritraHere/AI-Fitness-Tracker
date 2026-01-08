# 🏋️ AI Fitness Trainer

**AI Fitness Trainer Pro** is an intelligent, computer vision-based workout assistant built with Python. It uses **MediaPipe** for real-time pose estimation and **Streamlit** for a modern, interactive dashboard. The application tracks your movements via webcam, counts repetitions automatically, and provides real-time feedback on your form to ensure safe and effective exercise.

## ✨ Key Features

* **🧠 Smart Auto-Detection:**
* **Bicep Curls:** No need to select "Left" or "Right" arm manually. The AI automatically detects which arm is moving and tracks it.
* **Idle State:** The system recognizes when you are resting or standing still, suppressing false "Perfect Form" scores until you actually start the rep.


* **📊 Interactive Dashboard (Streamlit):**
* Real-time video feed with skeletal overlays.
* Live Rep Counter and Form Consistency Score (0-100%).
* Text-based feedback alerts (e.g., "Go Deeper", "Elbows Flaring").


* **🏋️ Multi-Exercise Support:**
* **Squats:** Tracks hip-to-knee depth and back stability.
* **Pushups:** Monitors elbow extension and body alignment.
* **Bicep Curls:** tracks arm flexion and isolation.


* **⚙️ Difficulty Modes:**
* **Beginner:** Lenient angle thresholds for those just starting.
* **Advanced:** Stricter form requirements for experienced athletes.



## 🛠️ Tech Stack

* **Python 3.8+**
* **OpenCV:** Video capture and image processing.
* **MediaPipe:** High-fidelity body landmark detection.
* **Streamlit:** Frontend UI and state management.
* **NumPy:** Angle calculations and data handling.

## 📂 Project Structure

| File | Description |
| --- | --- |
| `app.py` | **Main Application.** Runs the Streamlit dashboard, handles UI, video processing, and feedback logic. |
| `main.py` | *Legacy/Debug Mode.* A standalone OpenCV window version (useful for quick testing without the web UI). |
| `pose_detection.py` | Wrapper class for the MediaPipe Pose model. |
| `exercise_rules.py` | Contains the physics and logic (angles/thresholds) for Squats, Pushups, and Curls. |
| `utils.py` | Helper functions for drawing the skeleton overlay and the RepCounter class. |
| `angle_calculation.py` | Geometry functions to calculate angles between body joints. |
| `session_summary.py` | Manages workout statistics (total reps, average form score). |
| `config.py` | Configuration file containing angle thresholds and difficulty settings. |
| `requirements.txt` | List of Python dependencies. |

## 🚀 Installation

1. **Clone or Download** this repository to your local machine.
2. **Open your terminal** and navigate to the project directory.
3. **Install the dependencies** using pip:
```bash
pip install -r requirements.txt

```


*(If the command above fails, try installing manually: `pip install streamlit opencv-python mediapipe numpy pillow`)*

## 🎮 How to Run

### 1. The Dashboard (Recommended)

This launches the full UI with difficulty toggles and stats.

```bash
streamlit run app.py

```

* A new tab will open in your default web browser (usually `http://localhost:8501`).
* **Note:** You must allow the browser to access your webcam.

### 2. Desktop Mode (Testing)

For a simple popup window without the UI elements:

```bash
python main.py

```

* Press **'q'** to quit the application.

## 💡 Usage Guide

1. **Select Exercise:** Use the sidebar dropdown to choose Squat, Pushup, or Bicep Curl.
2. **Select Mode:** Choose "Beginner" or "Advanced".
3. **Toggle Camera:** Click the "Start Camera" switch.
4. **Position Yourself:**
* **Squats:** Ensure your whole body (legs to head) is visible.
* **Pushups:** Side profile works best.
* **Curls:** Upper body visible; you can curl with either arm.


5. **Status Indicators:**
* **"Ready to Start":** You are visible but haven't started moving.
* **"Form: XX%":** Appears during active movement.
* **"Resting":** Appears when you lock out or stand still between reps.



## 🛑 Troubleshooting

* **Camera Error:** Ensure no other application (Zoom, Teams, etc.) is using the webcam.
* **"Go Deeper" Warning:** The AI is strict! Ensure you hit the required angle (e.g., thighs parallel to ground for squats) to trigger the count.

* **Slow Performance:** MediaPipe runs on CPU. Ensure your lighting is good; poor lighting forces the AI to work harder to find landmarks.
