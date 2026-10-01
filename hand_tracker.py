"""
Hand Tracker Module for Invisible Violin.
Wraps MediaPipe Hands with landmark smoothing, spatial calculations,
and individual finger extension detection (Index, Middle, Ring, Pinky) for authentic violin fingering.
"""

import sys
import os
import time
import math
import numpy as np

import cv2
import mediapipe as mp


class LandmarkFilter:
    """Exponential moving average filter for smoothing hand landmark positions."""

    def __init__(self, alpha=0.35):
        self.alpha = alpha
        self.value = None

    def update(self, new_val):
        if self.value is None:
            self.value = np.array(new_val, dtype=np.float32)
        else:
            self.value = self.alpha * np.array(new_val, dtype=np.float32) + (1.0 - self.alpha) * self.value
        return self.value

    def reset(self):
        self.value = None


class HandTracker:
    """Robust 2-Hand Tracker using MediaPipe with signal smoothing & finger gesture detection."""

    def __init__(self, min_detection_confidence=0.70, min_tracking_confidence=0.65):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        # Filters for key tracking points
        self.left_index_filter = LandmarkFilter(alpha=0.30)
        self.left_wrist_filter = LandmarkFilter(alpha=0.25)
        self.right_wrist_filter = LandmarkFilter(alpha=0.25)
        self.right_index_filter = LandmarkFilter(alpha=0.30)

    def process(self, frame_bgr):
        """
        Process BGR frame and return detected left and right hand dictionaries.
        Includes finger extension counts for authentic 1st, 2nd, 3rd, 4th violin fingering.
        """
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        left_hand_data = None
        right_hand_data = None

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks,
                results.multi_handedness,
            ):
                label = handedness.classification[0].label  # "Left" or "Right"
                score = handedness.classification[0].score

                landmarks = hand_landmarks.landmark

                wrist = np.array([landmarks[0].x * w, landmarks[0].y * h, landmarks[0].z * w])
                index_tip = np.array([landmarks[8].x * w, landmarks[8].y * h, landmarks[8].z * w])
                thumb_tip = np.array([landmarks[4].x * w, landmarks[4].y * h, landmarks[4].z * w])

                # Detect individual finger extensions (relative to wrist)
                # Finger tips: Index (8), Middle (12), Ring (16), Pinky (20)
                # Finger PIP joints: Index (6), Middle (10), Ring (14), Pinky (18)
                def dist_sq(lm1, lm2):
                    return (lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2

                wrist_lm = landmarks[0]
                index_ext = dist_sq(landmarks[8], wrist_lm) > dist_sq(landmarks[6], wrist_lm)
                middle_ext = dist_sq(landmarks[12], wrist_lm) > dist_sq(landmarks[10], wrist_lm)
                ring_ext = dist_sq(landmarks[16], wrist_lm) > dist_sq(landmarks[14], wrist_lm)
                pinky_ext = dist_sq(landmarks[20], wrist_lm) > dist_sq(landmarks[18], wrist_lm)

                # Count active extended fingers (1st finger = Index, 2nd = Middle, 3rd = Ring, 4th = Pinky)
                extended_count = 0
                if index_ext: extended_count += 1
                if middle_ext: extended_count += 1
                if ring_ext: extended_count += 1
                if pinky_ext: extended_count += 1

                hand_dict = {
                    "raw_landmarks": hand_landmarks,
                    "score": score,
                    "wrist": wrist,
                    "index_tip": index_tip,
                    "thumb_tip": thumb_tip,
                    "finger_count": extended_count,
                    "fingers": {
                        "index": index_ext,
                        "middle": middle_ext,
                        "ring": ring_ext,
                        "pinky": pinky_ext,
                    },
                }

                if label == "Left":
                    hand_dict["wrist_smooth"] = self.left_wrist_filter.update(wrist[:2])
                    hand_dict["index_smooth"] = self.left_index_filter.update(index_tip[:2])
                    
                    pinch_dist = math.hypot(
                        thumb_tip[0] - index_tip[0],
                        thumb_tip[1] - index_tip[1],
                    )
                    hand_dict["pinch_dist"] = pinch_dist
                    left_hand_data = hand_dict

                elif label == "Right":
                    hand_dict["wrist_smooth"] = self.right_wrist_filter.update(wrist[:2])
                    hand_dict["index_smooth"] = self.right_index_filter.update(index_tip[:2])
                    hand_dict["z_depth"] = landmarks[0].z
                    right_hand_data = hand_dict

        if left_hand_data is None:
            self.left_index_filter.reset()
            self.left_wrist_filter.reset()
        if right_hand_data is None:
            self.right_wrist_filter.reset()
            self.right_index_filter.reset()

        return left_hand_data, right_hand_data

    def draw_landmarks(self, frame, hand_landmarks):
        self.mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_styles.get_default_hand_landmarks_style(),
            self.mp_styles.get_default_hand_connections_style(),
        )

    def close(self):
        self.hands.close()
