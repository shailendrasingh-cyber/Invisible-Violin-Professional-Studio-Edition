"""
Gesture & Bow Physical Dynamics Engine.
Processes right-hand bowing speed, stroke direction (Upbow/Downbow),
bow pressure, contact point timbre dynamics (Sul Ponticello vs Sul Tasto), and pizzicato plucking triggers.
"""

import time
import math
import numpy as np

from config import BOW_START_SPEED, BOW_FULL_SPEED, BOW_RELEASE_SPEED


class GestureProcessor:
    """Calculates physical bowing dynamics and musical gestures."""

    def __init__(self):
        self.prev_bow_x = None
        self.prev_bow_y = None
        self.prev_time = None
        self.bow_direction = 1  # 1 = Downbow (->), -1 = Upbow (<-)

        # Smoothed bow metrics
        self.smoothed_speed = 0.0
        self.smoothed_pressure = 0.5
        self.volume_envelope = 0.0
        self.contact_point = 0.5  # 0.0 = Sul Ponticello, 1.0 = Sul Tasto

        # Pizzicato pinch tracker
        self.prev_pinch = False
        self.pinch_cooldown = 0.0

    def reset_bow(self):
        self.prev_bow_x = None
        self.prev_bow_y = None
        self.prev_time = None
        self.smoothed_speed = 0.0
        self.volume_envelope = 0.0

    def process_bow(self, right_hand_data, frame_w, frame_h):
        """
        Process right hand movement to calculate bow velocity, direction, pressure, and contact point.
        Returns dict with speed, volume, pressure, direction, bow_pos, contact_point, stroke_change.
        """
        if right_hand_data is None:
            self.reset_bow()
            return {
                "speed": 0.0,
                "volume": 0.0,
                "pressure": 0.5,
                "direction": 1,
                "bow_pos": None,
                "contact_point": 0.5,
                "stroke_change": False,
            }

        now = time.time()
        wrist = right_hand_data["wrist_smooth"]
        rx, ry = wrist[0], wrist[1]

        raw_speed = 0.0
        stroke_change = False

        if self.prev_bow_x is not None and self.prev_time is not None:
            dt = max(0.001, now - self.prev_time)
            
            # Horizontal stroke movement normalized to width
            dx = (rx - self.prev_bow_x) / frame_w
            dy = (ry - self.prev_bow_y) / frame_h
            dist = math.hypot(dx, dy)

            # Speed in screen units per second
            raw_speed = dist / dt

            # Detect stroke direction change (Upbow / Downbow)
            if abs(dx) > 0.015:
                new_dir = 1 if dx > 0 else -1
                if new_dir != self.bow_direction and raw_speed > BOW_START_SPEED:
                    self.bow_direction = new_dir
                    stroke_change = True

        self.prev_bow_x = rx
        self.prev_bow_y = ry
        self.prev_time = now

        # Smooth bow speed (low-pass filter)
        self.smoothed_speed += (raw_speed - self.smoothed_speed) * 0.35

        # Map speed to dynamic volume envelope [0.0, 1.0]
        if self.smoothed_speed > BOW_START_SPEED:
            target_vol = (self.smoothed_speed - BOW_START_SPEED) / (BOW_FULL_SPEED - BOW_START_SPEED)
            target_vol = min(1.0, max(0.12, target_vol))
        else:
            target_vol = 0.0

        # Envelope attack/release
        if target_vol > self.volume_envelope:
            self.volume_envelope += (target_vol - self.volume_envelope) * 0.30
        else:
            self.volume_envelope += (target_vol - self.volume_envelope) * 0.08

        # Estimate bow pressure using z-depth & vertical hand tilt
        z_depth = right_hand_data.get("z_depth", 0.0)
        pressure = min(1.0, max(0.2, 0.5 - z_depth * 2.5))
        self.smoothed_pressure += (pressure - self.smoothed_pressure) * 0.15

        # Bow contact point along string (Y position on screen: Top = Sul Tasto near fingerboard, Bottom = Sul Ponticello near bridge)
        norm_y = max(0.0, min(1.0, ry / frame_h))
        self.contact_point = norm_y

        return {
            "speed": self.smoothed_speed,
            "volume": self.volume_envelope,
            "pressure": self.smoothed_pressure,
            "direction": self.bow_direction,
            "bow_pos": (int(rx), int(ry)),
            "contact_point": self.contact_point,
            "stroke_change": stroke_change,
        }

    def check_pizzicato_trigger(self, left_hand_data):
        """
        Check if left hand performs a pinch/pluck gesture for pizzicato.
        Pinch distance < 28px triggers pizzicato.
        """
        if left_hand_data is None:
            self.prev_pinch = False
            return False

        now = time.time()
        pinch_dist = left_hand_data.get("pinch_dist", 999.0)
        is_pinched = pinch_dist < 28.0

        triggered = False
        if is_pinched and not self.prev_pinch and (now - self.pinch_cooldown) > 0.22:
            triggered = True
            self.pinch_cooldown = now

        self.prev_pinch = is_pinched
        return triggered
