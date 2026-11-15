from core.base_exercise import BaseExercise


class ShoulderPressDetector(BaseExercise):
    UP_THRESHOLD = 160
    DOWN_THRESHOLD = 90
    MIN_VISIBILITY = 0.5

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        left_vis = getattr(landmarks[self.LEFT_ELBOW], 'visibility', 1.0)
        right_vis = getattr(landmarks[self.RIGHT_ELBOW], 'visibility', 1.0)
        if left_vis is None: left_vis = 1.0
        if right_vis is None: right_vis = 1.0

        if left_vis >= right_vis:
            shoulder_idx = self.LEFT_SHOULDER
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
            hip_idx = self.LEFT_HIP
            knee_idx = self.LEFT_KNEE
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST
            hip_idx = self.RIGHT_HIP
            knee_idx = self.RIGHT_KNEE

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
            if elbow_angle > self.UP_THRESHOLD:
                self.stage = "up"

            if elbow_angle < self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

        if elbow_angle >= self.UP_THRESHOLD:
            extension_status = "LOCKED OUT"
        elif elbow_angle >= 140:
            extension_status = "PARTIAL EXTENSION"
        else:
            extension_status = "BOTTOM"

        trunk_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
        )

        back_arch_status = "EXCESSIVE ARCH" if trunk_angle < 165 else "NEUTRAL"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "extension_status": extension_status,
            "back_arch_status": back_arch_status,
        }
