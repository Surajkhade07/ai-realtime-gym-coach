import math
from core.base_exercise import BaseExercise


class BicepsCurlDetector(BaseExercise):
    UP_THRESHOLD = 50
    DOWN_THRESHOLD = 160
    MIN_VISIBILITY = 0.5
    ELBOW_DRIFT_TOLERANCE = 0.06
    SWING_THRESHOLD = 15

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24

    def __init__(self):
        super().__init__()
        self._shoulder_x_baseline = None

    def reset(self) -> None:
        self.reps = 0
        self.stage = None
        self._shoulder_x_baseline = None

    def process(self, landmarks) -> dict:
        left_vis = getattr(landmarks[self.LEFT_ELBOW], 'visibility', 1.0)
        right_vis = getattr(landmarks[self.RIGHT_ELBOW], 'visibility', 1.0)
        if left_vis is None: left_vis = 1.0
        if right_vis is None: right_vis = 1.0

        if left_vis >= right_vis:
            shoulder_idx = self.LEFT_SHOULDER
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx),
        )

        s_vis = getattr(landmarks[shoulder_idx], 'visibility', 1.0) or 1.0
        e_vis = getattr(landmarks[elbow_idx], 'visibility', 1.0) or 1.0
        w_vis = getattr(landmarks[wrist_idx], 'visibility', 1.0) or 1.0

        key_landmarks_visible = s_vis > self.MIN_VISIBILITY and e_vis > self.MIN_VISIBILITY and w_vis > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if elbow_angle < self.UP_THRESHOLD:
                self.stage = "up"

            if elbow_angle > self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

        shoulder_x = landmarks[shoulder_idx].x
        elbow_x = landmarks[elbow_idx].x

        elbow_drift = abs(elbow_x - shoulder_x)
        shoulder_status = "STABLE" if elbow_drift <= self.ELBOW_DRIFT_TOLERANCE else "ELBOW FLARED"

        if self._shoulder_x_baseline is None:
            self._shoulder_x_baseline = shoulder_x

        torso_sway = abs(shoulder_x - self._shoulder_x_baseline) * 100
        swing_status = "CONTROLLED" if torso_sway <= self.SWING_THRESHOLD else "SWINGING"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "shoulder_status": shoulder_status,
            "swing_status": swing_status,
        }
