from core.base_exercise import BaseExercise


class PushUpDetector(BaseExercise):
    DOWN_THRESHOLD = 90
    UP_THRESHOLD = 160
    MIN_VISIBILITY = 0.5
    HIP_SAG_TOLERANCE = 0.08

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

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
            ankle_idx = self.LEFT_ANKLE
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST
            hip_idx = self.RIGHT_HIP
            ankle_idx = self.RIGHT_ANKLE

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx),
        )

        body_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, ankle_idx),
        )

        shoulder_y = landmarks[shoulder_idx].y
        ankle_y = landmarks[ankle_idx].y
        hip_y = landmarks[hip_idx].y

        expected_hip_y = (shoulder_y + ankle_y) / 2
        hip_deviation = hip_y - expected_hip_y

        s_vis = getattr(landmarks[shoulder_idx], 'visibility', 1.0) or 1.0
        e_vis = getattr(landmarks[elbow_idx], 'visibility', 1.0) or 1.0
        w_vis = getattr(landmarks[wrist_idx], 'visibility', 1.0) or 1.0
        h_vis = getattr(landmarks[hip_idx], 'visibility', 1.0) or 1.0

        key_landmarks_visible = (
            s_vis > self.MIN_VISIBILITY
            and e_vis > self.MIN_VISIBILITY
            and w_vis > self.MIN_VISIBILITY
            and h_vis > self.MIN_VISIBILITY
        )
        
        if key_landmarks_visible:
            if elbow_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if elbow_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        body_alignment = "GOOD" if body_angle >= 160 else "BENT"

        if hip_deviation > self.HIP_SAG_TOLERANCE:
            hip_status = "HIPS TOO LOW"
        elif hip_deviation < -self.HIP_SAG_TOLERANCE:
            hip_status = "HIPS TOO HIGH"
        else:
            hip_status = "ALIGNED"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "body_alignment": body_alignment,
            "hip_status": hip_status,
        }
