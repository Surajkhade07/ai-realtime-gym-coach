from core.base_exercise import BaseExercise

class SquatDetector(BaseExercise):
    DOWN_THRESHOLD = 100
    UP_THRESHOLD = 160
    MIN_VISIBILITY = 0.5

    LEFT_HIP = 23
    LEFT_KNEE = 25
    LEFT_ANKLE = 27
    RIGHT_HIP = 24
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
        left_knee_angle = self.calculate_angles(
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_KNEE),
            self.get_point(landmarks, self.LEFT_ANKLE)
        )

        right_knee_angle = self.calculate_angles(
            self.get_point(landmarks, self.RIGHT_HIP),
            self.get_point(landmarks, self.RIGHT_KNEE),
            self.get_point(landmarks, self.RIGHT_ANKLE)
        )

        left_vis = getattr(landmarks[self.LEFT_KNEE], 'visibility', 1.0) or 0.0
        right_vis = getattr(landmarks[self.RIGHT_KNEE], 'visibility', 1.0) or 0.0

        if left_vis >= right_vis:
            knee_angle = left_knee_angle
            hip_idx, knee_idx, ankle_idx, shoulder_idx = self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE, self.LEFT_SHOULDER
        else:
            knee_angle = right_knee_angle
            hip_idx, knee_idx, ankle_idx, shoulder_idx = self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE, self.RIGHT_SHOULDER

        back_angle = self.calculate_angles(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx)
        )

        hip_vis = getattr(landmarks[hip_idx], 'visibility', 1.0) or 0.0
        knee_vis = getattr(landmarks[knee_idx], 'visibility', 1.0) or 0.0
        ankle_vis = getattr(landmarks[ankle_idx], 'visibility', 1.0) or 0.0

        key_landmarks_visible = (
            hip_vis >= self.MIN_VISIBILITY
            and knee_vis >= self.MIN_VISIBILITY
            and ankle_vis >= self.MIN_VISIBILITY
        )

        depth_status = "N/A"
        if key_landmarks_visible:
            if knee_angle <= self.DOWN_THRESHOLD:
                self.stage = "down"
                depth_status = "GOOD DEPTH"
            elif knee_angle < 140:
                depth_status = "TOO HIGH" if self.stage == "down" or knee_angle < 125 else "DESCENDING"
            else:
                depth_status = "STANDING"

            if knee_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1
        else:
            depth_status = "STEP BACK"

        return {
            "reps": self.reps,
            "knee_angle": int(knee_angle),
            "back_angle": int(back_angle),
            "depth_status": depth_status,
        }