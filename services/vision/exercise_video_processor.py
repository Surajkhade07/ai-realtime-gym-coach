from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp
import threading
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.squat import SquatDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curl import BicepsCurlDetector
from detectors.shoulders_press import ShoulderPressDetector
from detectors.lunges import LungesDetector
from services.config.workout_config import POSE_CONNECTIONS


class VideoProcessorClass:
    """
    MediaPipe pose processor.
    Accepts BGR frames from cv2 / decoded JPEG and returns annotated BGR frames.
    No WebRTC dependency — works on Streamlit Cloud.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics: dict = {"pose_detected": False, "reps": 0}
        self._exercise_type: str = "Squats"

        _project_root = Path(__file__).resolve().parents[2]
        model_path = str(_project_root / "ml_model" / "pose_landmarker_full.task")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        self._detectors = {
            "Squats":                   SquatDetector(),
            "Push-ups":                 PushUpDetector(),
            "Biceps Curls (Dumbbell)":  BicepsCurlDetector(),
            "Shoulder Press":           ShoulderPressDetector(),
            "Lunges":                   LungesDetector(),
        }

        self._frame_ts_ms: int = 0

    # ------------------------------------------------------------------ #
    # Thread-safe accessors                                                #
    # ------------------------------------------------------------------ #

    def set_latest_metrics(self, metrics: dict):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self) -> dict | None:
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise(self, exercise_type: str):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self) -> str:
        with self._lock:
            return self._exercise_type

    # ------------------------------------------------------------------ #
    # Drawing helpers                                                      #
    # ------------------------------------------------------------------ #

    def _draw_skeleton(self, img: np.ndarray, landmarks):
        h, w = img.shape[:2]
        for s, e in POSE_CONNECTIONS:
            if s < len(landmarks) and e < len(landmarks):
                p1, p2 = landmarks[s], landmarks[e]
                v1 = getattr(p1, "visibility", 1.0)
                v2 = getattr(p2, "visibility", 1.0)
                if (v1 is None or v1 >= 0.5) and (v2 is None or v2 >= 0.5):
                    cv2.line(
                        img,
                        (int(p1.x * w), int(p1.y * h)),
                        (int(p2.x * w), int(p2.y * h)),
                        (0, 255, 0), 3,
                    )
        for lm in landmarks:
            v = getattr(lm, "visibility", 1.0)
            if v is None or v >= 0.5:
                cv2.circle(img, (int(lm.x * w), int(lm.y * h)), 5, (255, 0, 0), -1)

    def _draw_no_pose(self, img: np.ndarray):
        cv2.putText(img, "NO POSE DETECTED",     (30, 45),  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(img, "STEP BACK & FACE CAM", (30, 85),  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

    def _draw_overlays(self, img: np.ndarray, metrics: dict, ex: str):
        h, w = img.shape[:2]
        y = h - 20
        f = cv2.FONT_HERSHEY_SIMPLEX

        if ex == "Squats":
            cv2.putText(img, f"DEPTH: {metrics.get('depth_status','')}",   (20, y), f, 0.8, (0,255,0), 2)
        elif ex == "Push-ups":
            cv2.putText(img, f"BODY: {metrics.get('body_alignment','')} | HIP: {metrics.get('hip_status','')}", (20, y), f, 0.7, (0,255,0), 2)
        elif ex == "Biceps Curls (Dumbbell)":
            cv2.putText(img, f"SWING: {metrics.get('swing_status','')}", (20, y), f, 0.8, (0,255,0), 2)
        elif ex == "Shoulder Press":
            cv2.putText(img, f"EXT: {metrics.get('extension_status','')} | BACK: {metrics.get('back_arch_status','')}", (20, y), f, 0.7, (0,255,0), 2)
        elif ex == "Lunges":
            cv2.putText(img, f"BALANCE: {metrics.get('balance_status','')}", (20, y), f, 0.8, (0,255,0), 2)

        # Rep counter — top-right
        cv2.putText(img, f"REPS: {metrics.get('reps',0)}", (w - 160, 45), f, 1.0, (0, 200, 255), 2, cv2.LINE_AA)

    # ------------------------------------------------------------------ #
    # Main entry point                                                     #
    # ------------------------------------------------------------------ #

    def process_frame(self, bgr_frame: np.ndarray) -> np.ndarray:
        """
        Process one BGR frame:
          1. Flip horizontally (mirror view).
          2. Run MediaPipe pose landmarker.
          3. Draw skeleton + overlays.
          4. Update internal metrics.
          5. Return annotated BGR frame.
        """
        image = cv2.flip(bgr_frame, 1)

        # MediaPipe Tasks API requires RGB
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self._frame_ts_ms += 33          # strictly increasing timestamp
        result = self._landmarker.detect_for_video(mp_image, self._frame_ts_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            self._draw_skeleton(image, landmarks)

            ex_type  = self.get_exercise()
            detector = self._detectors.get(ex_type)

            if detector:
                try:
                    metrics = detector.process(landmarks)
                except Exception:
                    metrics = None

                if metrics is not None:
                    metrics["pose_detected"] = True
                    self._draw_overlays(image, metrics, ex_type)
                    self.set_latest_metrics(metrics)
        else:
            self._draw_no_pose(image)
            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                else:
                    self._latest_metrics = {"pose_detected": False, "reps": 0}

        return image
