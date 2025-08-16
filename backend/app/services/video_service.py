import cv2
import mediapipe as mp
import tempfile
import shutil
from fastapi import UploadFile
import math

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def calculate_angle(a, b, c):
    """Calculate angle at point b given 3 points"""
    ba = [a.x - b.x, a.y - b.y]
    bc = [c.x - b.x, c.y - b.y]
    dot_product = ba[0]*bc[0] + ba[1]*bc[1]
    mag_ba = math.hypot(*ba)
    mag_bc = math.hypot(*bc)
    if mag_ba * mag_bc == 0:
        return 0
    angle = math.acos(dot_product / (mag_ba * mag_bc))
    return math.degrees(angle)

async def process_video(file: UploadFile):
    # Save uploaded video temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    with open(temp_file.name, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cap = cv2.VideoCapture(temp_file.name)
    pose = mp_pose.Pose()
    feedback = []

    rep_count = 0
    going_down = False
    frame_num = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_num += 1

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Example for squat: angle at hip
            shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]

            hip_angle = calculate_angle(shoulder, hip, knee)

            # Detect reps
            down_threshold = 90  # angle considered "bottom" of squat
            up_threshold = 160   # angle considered "standing"

            if hip_angle < down_threshold and not going_down:
                going_down = True
            if hip_angle > up_threshold and going_down:
                rep_count += 1
                going_down = False
                # Add feedback for this rep
                if hip_angle < 80:
                    feedback.append(f"Rep {rep_count}: Go higher, keep your back straight!")
                else:
                    feedback.append(f"Rep {rep_count}: Good form!")

    cap.release()

    return {
        "frames_analyzed": frame_num,
        "reps_detected": rep_count,
        "feedback": feedback if feedback else ["No reps detected, check your form!"]
    }
