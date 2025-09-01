import cv2
import mediapipe as mp
import tempfile
import shutil
from fastapi import UploadFile
import math
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
import os
import logging

# Suppress MediaPipe and Protobuf warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings
warnings.filterwarnings('ignore', category=UserWarning, module='google.protobuf')
warnings.filterwarnings('ignore', category=UserWarning, module='absl')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='google.protobuf')

# Configure logging to suppress MediaPipe warnings
logging.getLogger('absl').setLevel(logging.ERROR)
logging.getLogger('mediapipe').setLevel(logging.ERROR)
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Suppress stdout/stderr for MediaPipe initialization
import sys
from contextlib import contextmanager

@contextmanager
def suppress_output():
    """Context manager to suppress stdout and stderr"""
    with open(os.devnull, 'w') as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

class ExerciseAnalyzer:
    def __init__(self):
        # Suppress MediaPipe initialization warnings and output
        with suppress_output():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.pose = mp_pose.Pose(
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
        
        # Exercise detection thresholds
        self.exercise_patterns = {
            'squat': {
                'key_landmarks': ['LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_KNEE'],
                'movement_pattern': 'vertical_up_down',
                'thresholds': {'down': 90, 'up': 160}
            },
            'deadlift': {
                'key_landmarks': ['LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_KNEE'],
                'movement_pattern': 'hip_hinge',
                'thresholds': {'down': 45, 'up': 160}
            },
            'pushup': {
                'key_landmarks': ['LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST'],
                'movement_pattern': 'horizontal_push',
                'thresholds': {'down': 90, 'up': 160}
            },
            'lunge': {
                'key_landmarks': ['LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE'],
                'movement_pattern': 'forward_back',
                'thresholds': {'down': 80, 'up': 160}
            },
            'plank': {
                'key_landmarks': ['LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_ANKLE'],
                'movement_pattern': 'static_hold',
                'thresholds': {'tolerance': 10}
            }
        }

    def calculate_angle(self, a, b, c) -> float:
        """Calculate angle at point b given 3 points"""
        # Check if any landmark is None
        if a is None or b is None or c is None:
            return 0
            
        ba = [a.x - b.x, a.y - b.y]
        bc = [c.x - b.x, c.y - b.y]
        dot_product = ba[0]*bc[0] + ba[1]*bc[1]
        mag_ba = math.hypot(*ba)
        mag_bc = math.hypot(*bc)
        if mag_ba * mag_bc == 0:
            return 0
        angle = math.acos(dot_product / (mag_ba * mag_bc))
        return math.degrees(angle)

    def detect_exercise_type(self, landmarks_history: List) -> str:
        """Auto-detect exercise type based on movement patterns"""
        if len(landmarks_history) < 30:  # Need enough frames
            return 'unknown'
        
        # Calculate movement patterns
        hip_movements = []
        shoulder_movements = []
        
        for frame_landmarks in landmarks_history:
            if frame_landmarks:
                hip = frame_landmarks[mp_pose.PoseLandmark.LEFT_HIP]
                shoulder = frame_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
                hip_movements.append((hip.x, hip.y))
                shoulder_movements.append((shoulder.x, shoulder.y))
        
        # Analyze movement patterns
        hip_variance = np.var([y for x, y in hip_movements])
        shoulder_variance = np.var([y for x, y in shoulder_movements])
        
        # Exercise classification logic
        if hip_variance > 0.01 and shoulder_variance > 0.01:
            # Check if it's vertical movement (squat/deadlift)
            hip_y_range = max([y for x, y in hip_movements]) - min([y for x, y in hip_movements])
            if hip_y_range > 0.1:
                # Determine squat vs deadlift based on hip angle patterns
                return 'squat' if hip_y_range > 0.15 else 'deadlift'
            else:
                return 'pushup'
        elif hip_variance < 0.005 and shoulder_variance < 0.005:
            return 'plank'
        else:
            return 'lunge'
        
        return 'unknown'

    def analyze_squat(self, landmarks, rep_count: int) -> Dict:
        """Analyze squat form and provide feedback"""
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        
        # Check if required landmarks are available
        if not all([shoulder, hip, knee, ankle]):
            return {
                "rep": rep_count,
                "feedback": ["Unable to analyze form - landmarks not detected. Please ensure your full body is visible in the video."],
                "score": 0,
                "metrics": {}
            }
        
        hip_angle = self.calculate_angle(shoulder, hip, knee)
        knee_angle = self.calculate_angle(hip, knee, ankle)
        
        feedback = []
        score = 100
        
        # Depth analysis
        if hip_angle < 80:
            feedback.append("Excellent depth! You're going low enough.")
        elif hip_angle < 90:
            feedback.append("Good depth, but try to go a bit lower for full range of motion.")
        else:
            feedback.append("Go deeper! Aim for thighs parallel to ground.")
            score -= 20
        
        # Knee tracking
        if knee.x > ankle.x:
            feedback.append("Keep knees behind toes to protect joints.")
            score -= 15
        
        # Back angle
        back_angle = self.calculate_angle(shoulder, hip, ankle)
        if back_angle < 45:
            feedback.append("Keep your chest up and back straight!")
            score -= 25
        
        return {
            "rep": rep_count,
            "feedback": feedback,
            "score": max(0, score),
            "metrics": {
                "hip_angle": round(hip_angle, 1),
                "knee_angle": round(knee_angle, 1),
                "back_angle": round(back_angle, 1)
            }
        }

    def analyze_deadlift(self, landmarks, rep_count: int) -> Dict:
        """Analyze deadlift form and provide feedback"""
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        
        # Check if required landmarks are available
        if not all([shoulder, hip, knee, ankle]):
            return {
                "rep": rep_count,
                "feedback": ["Unable to analyze form - landmarks not detected. Please ensure your full body is visible in the video."],
                "score": 0,
                "metrics": {}
            }
        
        hip_angle = self.calculate_angle(shoulder, hip, knee)
        back_angle = self.calculate_angle(shoulder, hip, ankle)
        
        feedback = []
        score = 100
        
        # Hip hinge analysis
        if hip_angle < 60:
            feedback.append("Great hip hinge! You're using your glutes properly.")
        else:
            feedback.append("Focus on hip hinge, not squatting down.")
            score -= 20
        
        # Back position
        if back_angle < 30:
            feedback.append("Keep your back straight and chest up!")
            score -= 25
        
        return {
            "rep": rep_count,
            "feedback": feedback,
            "score": max(0, score),
            "metrics": {
                "hip_angle": round(hip_angle, 1),
                "back_angle": round(back_angle, 1)
            }
        }

    def analyze_pushup(self, landmarks, rep_count: int) -> Dict:
        """Analyze push-up form and provide feedback"""
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        
        # Check if required landmarks are available
        if not all([shoulder, elbow, wrist, hip, ankle]):
            return {
                "rep": rep_count,
                "feedback": ["Unable to analyze form - landmarks not detected. Please ensure your full body is visible in the video."],
                "score": 0,
                "metrics": {}
            }
        
        arm_angle = self.calculate_angle(shoulder, elbow, wrist)
        body_angle = self.calculate_angle(shoulder, hip, ankle)
        
        feedback = []
        score = 100
        
        # Arm angle analysis
        if arm_angle < 80:
            feedback.append("Go lower! Touch your chest to the ground.")
            score -= 20
        elif arm_angle > 100:
            feedback.append("Good depth! You're getting full range of motion.")
        
        # Body alignment
        if abs(body_angle - 180) > 15:
            feedback.append("Keep your body in a straight line!")
            score -= 25
        
        return {
            "rep": rep_count,
            "feedback": feedback,
            "score": max(0, score),
            "metrics": {
                "arm_angle": round(arm_angle, 1),
                "body_angle": round(body_angle, 1)
            }
        }

    def analyze_plank(self, landmarks, rep_count: int) -> Dict:
        """Analyze plank form and provide feedback"""
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        
        # Check if required landmarks are available
        if not all([shoulder, hip, ankle]):
            return {
                "rep": rep_count,
                "feedback": ["Unable to analyze form - landmarks not detected. Please ensure your full body is visible in the video."],
                "score": 0,
                "metrics": {}
            }
        
        body_angle = self.calculate_angle(shoulder, hip, ankle)
        
        feedback = []
        score = 100
        
        # Body alignment
        if abs(body_angle - 180) > 10:
            feedback.append("Keep your body in a straight line!")
            score -= 30
        else:
            feedback.append("Perfect plank form! Body is straight.")
        
        # Hip position
        if hip.y > shoulder.y:
            feedback.append("Don't let your hips sag! Keep them level with shoulders.")
            score -= 20
        
        return {
            "rep": rep_count,
            "feedback": feedback,
            "score": max(0, score),
            "metrics": {
                "body_angle": round(body_angle, 1)
            }
        }

    def analyze_lunge(self, landmarks, rep_count: int) -> Dict:
        """Analyze lunge form and provide feedback"""
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        
        # Check if required landmarks are available
        if not all([hip, knee, ankle]):
            return {
                "rep": rep_count,
                "feedback": ["Unable to analyze form - landmarks not detected. Please ensure your full body is visible in the video."],
                "score": 0,
                "metrics": {}
            }
        
        knee_angle = self.calculate_angle(hip, knee, ankle)
        
        feedback = []
        score = 100
        
        # Knee tracking
        if knee.x > ankle.x:
            feedback.append("Keep your front knee behind your toes!")
            score -= 20
        else:
            feedback.append("Good knee position! Knee is properly aligned.")
        
        # Depth
        if knee_angle < 80:
            feedback.append("Excellent depth! You're getting a good stretch.")
        elif knee_angle < 90:
            feedback.append("Good depth, but try to go a bit lower.")
        else:
            feedback.append("Go deeper! Aim for 90-degree angles.")
            score -= 15
        
        return {
            "rep": rep_count,
            "feedback": feedback,
            "score": max(0, score),
            "metrics": {
                "knee_angle": round(knee_angle, 1)
            }
        }

async def process_video(file: UploadFile, exercise_type: str = "squat") -> Dict:
    """Process uploaded video and return exercise analysis"""
    print(f"Processing video for exercise type: {exercise_type}")
    analyzer = ExerciseAnalyzer()
    
    # Save uploaded video temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    try:
        with open(temp_file.name, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        cap = cv2.VideoCapture(temp_file.name)
        landmarks_history = []
        feedback_per_rep = []
        rep_count = 0
        going_down = False
        frame_num = 0
        
        # First pass: collect landmarks
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_num += 1
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Suppress MediaPipe processing warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                results = analyzer.pose.process(rgb_frame)
            
            if results.pose_landmarks:
                landmarks_history.append(results.pose_landmarks.landmark)
            else:
                landmarks_history.append(None)
        
        cap.release()
        
        # Use user-selected exercise type instead of auto-detection
        # exercise_type = analyzer.detect_exercise_type(landmarks_history)
        
        # Second pass: analyze form and count reps
        cap = cv2.VideoCapture(temp_file.name)
        going_down = False
        last_hip_angle = None
        
        # Suppress MediaPipe warnings during processing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
        
        print(f"Starting rep detection for {exercise_type}...")
        print(f"Total frames to analyze: {len(landmarks_history)}")
        print(f"Exercise thresholds - Down: {analyzer.exercise_patterns[exercise_type]['thresholds']['down']}°, Up: {analyzer.exercise_patterns[exercise_type]['thresholds']['up']}°")
        
        for frame_idx, landmarks in enumerate(landmarks_history):
            if not landmarks:
                continue
                
            # Exercise-specific analysis
            if exercise_type == 'squat':
                hip_angle = analyzer.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
                )
                
                if hip_angle:
                    # Detect reps with improved logic
                    if hip_angle < analyzer.exercise_patterns['squat']['thresholds']['down'] and not going_down:
                        going_down = True
                        print(f"Frame {frame_idx}: Going down detected (hip_angle: {hip_angle:.1f}°)")
                    
                    elif hip_angle > analyzer.exercise_patterns['squat']['thresholds']['up'] and going_down:
                        rep_count += 1
                        going_down = False
                        print(f"Frame {frame_idx}: Rep {rep_count} completed (hip_angle: {hip_angle:.1f}°)")
                        feedback_per_rep.append(analyzer.analyze_squat(landmarks, rep_count))
                    
                    # Reset state if stuck for too long
                    elif going_down and last_hip_angle and abs(hip_angle - last_hip_angle) < 5:
                        # If angle hasn't changed much for several frames, reset state
                        if frame_idx % 10 == 0:  # Check every 10 frames
                            going_down = False
                            print(f"Frame {frame_idx}: State reset due to lack of movement")
                    
                    last_hip_angle = hip_angle
            
            elif exercise_type == 'deadlift':
                hip_angle = analyzer.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
                )
                
                if hip_angle:
                    # Detect reps with improved logic
                    if hip_angle < analyzer.exercise_patterns['deadlift']['thresholds']['down'] and not going_down:
                        going_down = True
                        print(f"Frame {frame_idx}: Deadlift going down detected (hip_angle: {hip_angle:.1f}°)")
                    
                    elif hip_angle > analyzer.exercise_patterns['deadlift']['thresholds']['up'] and going_down:
                        rep_count += 1
                        going_down = False
                        print(f"Frame {frame_idx}: Deadlift rep {rep_count} completed (hip_angle: {hip_angle:.1f}°)")
                        feedback_per_rep.append(analyzer.analyze_deadlift(landmarks, rep_count))
                    
                    # Reset state if stuck for too long
                    elif going_down and last_hip_angle and abs(hip_angle - last_hip_angle) < 5:
                        if frame_idx % 10 == 0:
                            going_down = False
                            print(f"Frame {frame_idx}: Deadlift state reset due to lack of movement")
                    
                    last_hip_angle = hip_angle
            
            elif exercise_type == 'pushup':
                arm_angle = analyzer.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                    landmarks[mp_pose.PoseLandmark.LEFT_ELBOW],
                    landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
                )
                
                if arm_angle and arm_angle < analyzer.exercise_patterns['pushup']['thresholds']['down'] and not going_down:
                    going_down = True
                if arm_angle and arm_angle > analyzer.exercise_patterns['pushup']['thresholds']['up'] and going_down:
                    rep_count += 1
                    going_down = False
                    feedback_per_rep.append(analyzer.analyze_pushup(landmarks, rep_count))
            
            elif exercise_type == 'plank':
                # For plank, analyze every 30 frames (1 second at 30fps)
                if frame_idx % 30 == 0:
                    rep_count += 1
                    feedback_per_rep.append(analyzer.analyze_plank(landmarks, rep_count))
            
            elif exercise_type == 'lunge':
                knee_angle = analyzer.calculate_angle(
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP],
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE],
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
                )
                
                if knee_angle and knee_angle < analyzer.exercise_patterns['lunge']['thresholds']['down'] and not going_down:
                    going_down = True
                if knee_angle and knee_angle > analyzer.exercise_patterns['lunge']['thresholds']['up'] and going_down:
                    rep_count += 1
                    going_down = False
                    feedback_per_rep.append(analyzer.analyze_lunge(landmarks, rep_count))
        
        cap.release()
        
        # Check if we ended in the middle of a rep (going down)
        if going_down:
            print(f"Video ended while going down. Final rep may be incomplete.")
            # Optionally analyze the last frame as a partial rep
            if landmarks_history and landmarks_history[-1]:
                last_landmarks = landmarks_history[-1]
                if exercise_type == 'squat':
                    feedback_per_rep.append(analyzer.analyze_squat(last_landmarks, rep_count + 1))
                elif exercise_type == 'deadlift':
                    feedback_per_rep.append(analyzer.analyze_deadlift(last_landmarks, rep_count + 1))
                elif exercise_type == 'pushup':
                    feedback_per_rep.append(analyzer.analyze_pushup(last_landmarks, rep_count + 1))
                elif exercise_type == 'lunge':
                    feedback_per_rep.append(analyzer.analyze_lunge(last_landmarks, rep_count + 1))
                rep_count += 1
        
        print(f"Rep detection complete. Total reps detected: {rep_count}")
        
        # Calculate overall score
        overall_score = 0
        if feedback_per_rep:
            overall_score = sum(rep['score'] for rep in feedback_per_rep) / len(feedback_per_rep)
        
        return {
            "exercise_detected": exercise_type,
            "frames_analyzed": frame_num,
            "reps_detected": rep_count,
            "overall_score": round(overall_score, 1),
            "feedback_per_rep": feedback_per_rep if feedback_per_rep else [
                {
                    "rep": 1,
                    "feedback": ["No reps detected. Check your form and try again!"],
                    "score": 0,
                    "metrics": {}
                }
            ],
            "summary": {
                "total_reps": rep_count,
                "average_score": round(overall_score, 1),
                "exercise_type": exercise_type,
                "recommendations": get_recommendations(exercise_type, overall_score)
            }
        }
        
    finally:
        # Clean up temporary file
        import os
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def get_recommendations(exercise_type: str, score: float) -> List[str]:
    """Get personalized recommendations based on exercise type and score"""
    recommendations = []
    
    if score >= 90:
        recommendations.append("Excellent form! Keep up the great work.")
    elif score >= 70:
        recommendations.append("Good form overall. Focus on the areas mentioned in feedback.")
    elif score >= 50:
        recommendations.append("Form needs improvement. Practice the movement slowly and focus on technique.")
    else:
        recommendations.append("Consider working with a trainer to perfect your form.")
    
    # Exercise-specific recommendations
    if exercise_type == 'squat':
        recommendations.append("Focus on keeping knees behind toes and maintaining a straight back.")
    elif exercise_type == 'deadlift':
        recommendations.append("Practice hip hinge movement and keep your back straight throughout.")
    elif exercise_type == 'pushup':
        recommendations.append("Maintain a straight body line and go through full range of motion.")
    elif exercise_type == 'plank':
        recommendations.append("Keep your body in a straight line and don't let hips sag.")
    elif exercise_type == 'lunge':
        recommendations.append("Keep your front knee behind your toes and maintain balance.")
    
    return recommendations
