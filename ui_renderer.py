"""
UI Renderer Module for Invisible Violin — Real Violin Visual Edition.
Renders translucent violin body silhouette, f-holes, bridge, bow stick & horsehair,
musical notation stroke symbols (Downbow ⊓ vs Upbow ⋁), vibrating 4 strings, tuner dial,
and authentic Violin Fingering Badge (1st, 2nd, 3rd, 4th Finger + Position).
"""

import math
import cv2
import numpy as np

from config import VIOLIN_STRINGS, STRING_NAMES


class UIRenderer:
    """Renders stunning, studio-grade visual HUD on OpenCV frames."""

    def __init__(self):
        self.bow_particles = []
        self.phase = 0.0

    def draw_glass_panel(self, frame, x, y, w, h, bg_color=(15, 15, 25), alpha=0.65, border_color=(80, 80, 110)):
        """Renders semi-transparent glassmorphic panel overlay."""
        sub_img = frame[y:y+h, x:x+w]
        rect = np.full(sub_img.shape, bg_color, dtype=np.uint8)
        res = cv2.addWeighted(sub_img, 1.0 - alpha, rect, alpha, 0)
        frame[y:y+h, x:x+w] = res
        cv2.rectangle(frame, (x, y), (x + w, y + h), border_color, 1)

    def draw_violin_body(self, frame):
        """Draws aesthetic translucent wooden violin body contour and f-holes."""
        h, w = frame.shape[:2]
        cx = int(w * 0.505)
        cy = int(h * 0.55)

        cv2.ellipse(frame, (cx, cy + 60), (140, 180), 0, 0, 360, (25, 25, 40), -1)
        cv2.ellipse(frame, (cx, cy + 60), (140, 180), 0, 0, 360, (60, 60, 90), 1, cv2.LINE_AA)

        # F-holes (f)
        cv2.putText(frame, "f", (cx - 95, cy + 50), cv2.FONT_HERSHEY_SIMPLEX | cv2.FONT_ITALIC, 1.6, (120, 120, 160), 2, cv2.LINE_AA)
        cv2.putText(frame, "f", (cx + 80, cy + 50), cv2.FONT_HERSHEY_SIMPLEX | cv2.FONT_ITALIC, 1.6, (120, 120, 160), 2, cv2.LINE_AA)

        # Violin Bridge
        bridge_y = int(h * 0.72)
        cv2.rectangle(frame, (cx - 75, bridge_y), (cx + 75, bridge_y + 8), (140, 120, 90), -1)

    def draw_strings(self, frame, left_hand_info, audio_vol, tutorial_target=None):
        """
        Draws 4 violin strings (G, D, A, E) vibrating with sound output,
        plus target note guide ring when tutorial mode is active.
        """
        h, w = frame.shape[:2]
        self.phase += 0.4

        self.draw_violin_body(frame)

        active_string = left_hand_info["string"] if left_hand_info else "A"
        if tutorial_target:
            active_string = tutorial_target["string"]

        string_x_positions = {
            "G": int(w * 0.41),
            "D": int(w * 0.47),
            "A": int(w * 0.54),
            "E": int(w * 0.60),
        }

        # Fingerboard Backing
        fb_left = int(w * 0.37)
        fb_right = int(w * 0.64)
        self.draw_glass_panel(frame, fb_left, 110, fb_right - fb_left, h - 120, bg_color=(10, 10, 15), alpha=0.75, border_color=(50, 50, 70))

        # Position Markers (1st, 3rd, 5th position lines)
        pos_y_ratios = [0.80, 0.60, 0.42, 0.28, 0.18]
        pos_names = ["1st Pos", "3rd Pos", "5th Pos", "7th Pos", "Octave"]
        for y_rat, p_name in zip(pos_y_ratios, pos_names):
            py = int(110 + y_rat * (h - 220))
            cv2.line(frame, (fb_left + 10, py), (fb_right - 10, py), (40, 40, 60), 1, cv2.LINE_AA)
            cv2.putText(frame, p_name, (fb_left + 12, py - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (120, 120, 150), 1, cv2.LINE_AA)

        # Draw Tutorial Target Note Ring (if active)
        if tutorial_target:
            t_string = tutorial_target["string"]
            t_midi = tutorial_target["midi"]
            open_midi = VIOLIN_STRINGS[t_string]["midi"]
            norm_target_y = (t_midi - open_midi) / 28.0
            norm_target_y = max(0.0, min(1.0, norm_target_y))
            
            target_py = int(110 + (1.0 - norm_target_y) * (h - 220))
            target_px = string_x_positions.get(t_string, int(w * 0.54))

            cv2.circle(frame, (target_px, target_py), 20, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.circle(frame, (target_px, target_py), 6, (0, 255, 255), -1, cv2.LINE_AA)
            cv2.putText(frame, f"NOTE: {tutorial_target['name']}", (target_px + 24, target_py + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)

        # Draw Left Hand Finger Marker & Active Fingering Badge
        if left_hand_info and "index_smooth" in left_hand_info:
            fx, fy = int(left_hand_info["index_smooth"][0]), int(left_hand_info["index_smooth"][1])
            cv2.circle(frame, (fx, fy), 14, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.circle(frame, (fx, fy), 5, (0, 220, 255), -1, cv2.LINE_AA)

            # Fingering Badge (e.g. 1st Pos — 2nd Finger)
            pos_name = left_hand_info.get("pos_name", "1st Pos")
            f_num = left_hand_info.get("finger_number", 0)
            f_label = "Open String" if f_num == 0 else f"{f_num} Finger"
            cv2.putText(frame, f"{pos_name} | {f_label}", (fx + 18, fy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 200), 2, cv2.LINE_AA)

        # Draw 4 vibrating strings
        for s_name in STRING_NAMES:
            sx = string_x_positions[s_name]
            info = VIOLIN_STRINGS[s_name]
            base_color = info["color"]
            is_active = (s_name == active_string)

            thickness = 3 if s_name in ["G", "D"] else 2
            color = base_color if is_active else tuple(int(c * 0.45) for c in base_color)

            vib_amp = (audio_vol * 12.0) if (is_active and audio_vol > 0.01) else 0.0

            points = []
            steps = 40
            for i in range(steps + 1):
                y_pos = int(110 + (i / steps) * (h - 120))
                v_off = math.sin(self.phase + i * 0.4) * vib_amp if vib_amp > 0 else 0
                points.append((int(sx + v_off), y_pos))

            for i in range(len(points) - 1):
                cv2.line(frame, points[i], points[i+1], color, thickness if not is_active else thickness + 1, cv2.LINE_AA)

            label_bg = (30, 30, 45) if not is_active else base_color
            text_color = (255, 255, 255) if is_active else (160, 160, 160)
            cv2.circle(frame, (sx, 125), 14, label_bg, -1)
            cv2.putText(frame, s_name, (sx - 5, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2, cv2.LINE_AA)

    def draw_tuner_hud(self, frame, left_hand_info):
        """Renders pitch note badge and tuner needle dial."""
        if left_hand_info is None:
            return

        h, w = frame.shape[:2]
        note = left_hand_info["note_name"]
        cents = left_hand_info["cents"]
        freq = left_hand_info["freq"]
        vib_depth = left_hand_info.get("vibrato_depth", 0.0)

        tx, ty, tw, th = w // 2 - 130, 105, 260, 80
        self.draw_glass_panel(frame, tx, ty, tw, th, bg_color=(10, 15, 30), alpha=0.85, border_color=(0, 200, 255))

        cv2.putText(frame, note, (tx + 20, ty + 42), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, f"{freq:.1f} Hz", (tx + 20, ty + 66), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1, cv2.LINE_AA)

        meter_cx = tx + 180
        meter_cy = ty + 38
        cv2.circle(frame, (meter_cx, meter_cy), 26, (30, 35, 50), -1)
        cv2.circle(frame, (meter_cx, meter_cy), 26, (0, 200, 255), 1)

        angle_deg = (cents / 50.0) * 60.0
        rad = math.radians(angle_deg - 90)
        nx = int(meter_cx + 20 * math.cos(rad))
        ny = int(meter_cy + 20 * math.sin(rad))

        needle_color = (50, 255, 100) if abs(cents) < 10 else ((50, 180, 255) if abs(cents) < 25 else (50, 80, 255))
        cv2.line(frame, (meter_cx, meter_cy), (nx, ny), needle_color, 2, cv2.LINE_AA)
        cv2.circle(frame, (meter_cx, meter_cy), 3, (255, 255, 255), -1)

        cent_str = f"{cents:+.0f}c"
        cv2.putText(frame, cent_str, (meter_cx - 18, ty + 73), cv2.FONT_HERSHEY_SIMPLEX, 0.40, needle_color, 1, cv2.LINE_AA)

        if vib_depth > 1.5:
            cv2.putText(frame, "VIBRATO", (tx + 115, ty + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (255, 100, 220), 1, cv2.LINE_AA)

    def draw_bow_hud(self, frame, bow_info):
        """
        Renders right-hand bow stick & horsehair line, stroke symbols (Downbow ⊓ vs Upbow ⋁),
        speed meter, and contact point timbres.
        """
        if bow_info is None or bow_info["bow_pos"] is None:
            return

        h, w = frame.shape[:2]
        bx, by = bow_info["bow_pos"]
        speed = bow_info["speed"]
        vol = bow_info["volume"]
        direction = bow_info["direction"]
        contact = bow_info.get("contact_point", 0.5)

        bow_stick_start = (max(20, bx - 220), by - 12)
        bow_stick_end = (min(w - 20, bx + 220), by + 12)
        cv2.line(frame, bow_stick_start, bow_stick_end, (140, 90, 40), 4, cv2.LINE_AA)
        cv2.line(frame, (bow_stick_start[0], bow_stick_start[1] + 6), (bow_stick_end[0], bow_stick_end[1] + 6), (240, 240, 220), 2, cv2.LINE_AA)

        self.bow_particles.append({"pos": (bx, by), "life": 1.0, "dir": direction})
        if len(self.bow_particles) > 18:
            self.bow_particles.pop(0)

        for p in self.bow_particles:
            p["life"] -= 0.05
            if p["life"] > 0:
                alpha = p["life"]
                radius = int(8 * alpha)
                color = (0, 255, 255) if p["dir"] == 1 else (255, 150, 50)
                cv2.circle(frame, p["pos"], radius, color, -1, cv2.LINE_AA)

        glow_radius = 12 + int(vol * 14)
        cv2.circle(frame, (bx, by), glow_radius, (0, 220, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, (bx, by), 5, (255, 255, 255), -1)

        stroke_symbol = "DOWNBOW [ ]" if direction == 1 else "UPBOW V"
        stroke_color = (0, 255, 200) if direction == 1 else (255, 180, 50)
        cv2.putText(frame, stroke_symbol, (bx - 45, by - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, stroke_color, 2, cv2.LINE_AA)

        bx_panel, by_panel, bw_panel, bh_panel = w - 180, 110, 165, 130
        self.draw_glass_panel(frame, bx_panel, by_panel, bw_panel, bh_panel, bg_color=(15, 15, 25), alpha=0.75)

        cv2.putText(frame, "BOW DYNAMICS", (bx_panel + 15, by_panel + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1, cv2.LINE_AA)

        cv2.putText(frame, "Speed", (bx_panel + 15, by_panel + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 150), 1)
        cv2.rectangle(frame, (bx_panel + 65, by_panel + 45), (bx_panel + 150, by_panel + 55), (40, 40, 60), -1)
        fill_w = int(min(1.0, speed / 0.25) * 85)
        cv2.rectangle(frame, (bx_panel + 65, by_panel + 45), (bx_panel + 65 + fill_w, by_panel + 55), (0, 220, 255), -1)

        cv2.putText(frame, "Volume", (bx_panel + 15, by_panel + 85), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 150), 1)
        cv2.rectangle(frame, (bx_panel + 65, by_panel + 75), (bx_panel + 150, by_panel + 85), (40, 40, 60), -1)
        vol_w = int(vol * 85)
        cv2.rectangle(frame, (bx_panel + 65, by_panel + 75), (bx_panel + 65 + vol_w, by_panel + 85), (50, 255, 120), -1)

        contact_str = "Sul Tasto" if contact < 0.35 else ("Sul Ponticello" if contact > 0.68 else "Normal Position")
        cv2.putText(frame, contact_str, (bx_panel + 15, by_panel + 112), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 220), 1)

    def draw_tutorial_panel(self, frame, tutorial):
        """Renders Interactive Song Tutorial Banner & Guide Prompt."""
        if tutorial.mode != "TUTORIAL_GUIDE":
            return

        h, w = frame.shape[:2]
        song = tutorial.current_song()
        target = tutorial.current_target()

        px, py, pw, ph = 20, 110, 320, 120
        self.draw_glass_panel(frame, px, py, pw, ph, bg_color=(15, 25, 45), alpha=0.85, border_color=(0, 255, 255))

        cv2.putText(frame, "🎵 SONG TUTORIAL & GUIDE MODE", (px + 12, py + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"{song['title']} ({song['composer']})", (px + 12, py + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 2, cv2.LINE_AA)

        target_str = f"AUTO PLAYING: {target['name']} ({target['string']} String)"
        cv2.putText(frame, target_str, (px + 12, py + 72), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (50, 255, 150), 2, cv2.LINE_AA)

        cv2.putText(frame, "Watch glowing ring on string fingerboard!", (px + 12, py + 98), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 220, 100), 1, cv2.LINE_AA)

    def draw_oscilloscope(self, frame, scope_buffer):
        """Draws real-time audio waveform oscilloscope."""
        h, w = frame.shape[:2]
        ox, oy, ow, oh = 20, h - 110, 220, 90
        self.draw_glass_panel(frame, ox, oy, ow, oh, bg_color=(10, 10, 20), alpha=0.80, border_color=(0, 180, 255))

        cv2.putText(frame, "AUDIO WAVEFORM", (ox + 10, oy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 200, 255), 1, cv2.LINE_AA)

        pts = []
        n = len(scope_buffer)
        step = max(1, n // ow)
        mid_y = oy + oh // 2 + 10

        for i in range(0, n, step):
            x_pos = ox + int((i / n) * ow)
            y_pos = int(mid_y - scope_buffer[i] * (oh * 0.35))
            y_pos = max(oy + 25, min(oy + oh - 5, y_pos))
            pts.append((x_pos, y_pos))

        for i in range(len(pts) - 1):
            cv2.line(frame, pts[i], pts[i+1], (0, 255, 200), 1, cv2.LINE_AA)

    def draw_header_and_controls(self, frame, audio_enabled, play_mode, timbre_mode, tutorial_mode, fps):
        """Draws top title header, status indicators, and hotkey legend."""
        h, w = frame.shape[:2]

        self.draw_glass_panel(frame, 0, 0, w, 95, bg_color=(10, 12, 22), alpha=0.90, border_color=(40, 45, 65))

        cv2.putText(frame, "INVISIBLE VIOLIN", (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "STUDIO EDITION", (265, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1, cv2.LINE_AA)

        # Badges
        audio_str = "AUDIO ON" if audio_enabled else "MUTED"
        audio_bg = (0, 180, 80) if audio_enabled else (0, 50, 200)
        cv2.rectangle(frame, (20, 55), (105, 82), audio_bg, -1)
        cv2.putText(frame, audio_str, (26, 73), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

        # Play Mode Badge
        cv2.rectangle(frame, (115, 55), (265, 82), (40, 50, 75), -1)
        cv2.putText(frame, f"MODE: {play_mode}", (122, 73), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (220, 220, 255), 1, cv2.LINE_AA)

        # Timbre Badge
        cv2.rectangle(frame, (275, 55), (445, 82), (50, 40, 75), -1)
        cv2.putText(frame, f"SOUND: {timbre_mode}", (282, 73), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (240, 180, 255), 1, cv2.LINE_AA)

        # Practice / Free Play Mode Badge
        if tutorial_mode == "TUTORIAL_GUIDE":
            tut_bg = (0, 180, 220)
            tut_text = "TUTORIAL GUIDE (AUTO)"
        else:
            tut_bg = (40, 140, 50)
            tut_text = "NORMAL FREE PLAY"

        cv2.rectangle(frame, (455, 55), (660, 82), tut_bg, -1)
        cv2.putText(frame, tut_text, (463, 73), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)

        # FPS
        cv2.putText(frame, f"FPS: {fps}", (w - 100, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (180, 180, 180), 1, cv2.LINE_AA)

        # Controls Legend on Bottom Right
        lx, ly, lw, lh = w - 350, h - 120, 330, 105
        self.draw_glass_panel(frame, lx, ly, lw, lh, bg_color=(10, 12, 20), alpha=0.80)
        cv2.putText(frame, "CONTROLS & SHORTCUTS", (lx + 12, ly + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1)
        cv2.putText(frame, "G: Switch Mode (Normal Free Play <-> Tutorial)", (lx + 12, ly + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)
        cv2.putText(frame, "H: Change Practice Song | T: Violin Sound Model", (lx + 12, ly + 56), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 200, 100), 1)
        cv2.putText(frame, "M: Scale Mode | SPACE: Toggle Mute | R: Reset", (lx + 12, ly + 74), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (210, 210, 210), 1)
        cv2.putText(frame, "Q / ESC: Exit Studio Application", (lx + 12, ly + 92), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1)
