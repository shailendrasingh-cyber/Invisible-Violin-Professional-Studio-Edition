"""
===================================================================
INVISIBLE VIOLIN - PROFESSIONAL STUDIO EDITION
===================================================================
Webcam + MediaPipe Hands + Physical Bowed String Acoustic DSP Engine.
Author: Shailendra Singh

Features:
  - Real Violin Fingering Mechanics (Open string + 1st, 2nd, 3rd, 4th finger placement)
  - Sticky String Selection Hysteresis & Position Shifting (1st, 3rd, 5th position)
  - Realistic Violin Physics (Helmholtz slip-stick, downbow attack accents, contact point timbre shifting, sympathetic open-string resonance)
  - Translucent Violin Body Silhouette, F-holes, Bridge, Bow Stick & Horsehair Overlay
  - Standard Violin Musical Notation Symbols (Downbow ⊓ vs Upbow ⋁)
  - 2 Play Modes: NORMAL FREE PLAY (100% hand controlled) & TUTORIAL GUIDE (Auto-plays song & shows target markers)
  - 5 Distinct Violin Sound Models (Solo Acoustic, Electric Overdrive, Baroque Warmth, Orchestral Section, Pizzicato)
  - Practice Songs: Twinkle Twinkle Little Star, Ode to Joy, Canon in D, Vivaldi Spring
  - 4 Open Strings (G3, D4, A4, E5) with scale snapping (Continuous, Chromatic, Major, Pentatonic)
  - Expressive Left-Hand Vibrato & Pizzicato Pinch Plucking

Controls:
  G          -> Switch between NORMAL FREE PLAY & TUTORIAL SONG GUIDE
  H          -> Next Tutorial Practice Song
  T          -> Cycle Sound Model (Acoustic, Electric, Baroque, Orchestra, Pizzicato)
  M          -> Cycle Scale Snapping (Continuous, Chromatic, Major Scale, Pentatonic)
  SPACE      -> Mute / Unmute Audio
  R          -> Reset Bow Tracking
  Q / ESC    -> Quit Application
"""

import sys
import os
import time
import argparse

import cv2
import sounddevice as sd
import numpy
import scipy
import mediapipe

from config import (
    WINDOW_TITLE,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    PLAY_MODES,
    TIMBRE_PRESETS,
)
from audio_engine import AudioEngine
from hand_tracker import HandTracker
from violin import ViolinModel
from gesture import GestureProcessor
from ui_renderer import UIRenderer
from tutorial import SongTutorialEngine


def main():
    parser = argparse.ArgumentParser(description="Invisible Violin Studio Edition")
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index (default: 0)")
    args = parser.parse_args()

    print("=" * 65)
    print("      INVISIBLE VIOLIN - PROFESSIONAL STUDIO EDITION      ")
    print("                    by Shailendra Singh                   ")
    print("=" * 65)
    print("Initializing webcam and audio engine...")

    # 1. Initialize Camera with fallback
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened() and args.camera == 0:
        print("Camera index 0 failed. Trying camera index 1...")
        cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("ERROR: Could not access webcam. Please check your camera connection.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    # 2. Initialize Subsystems
    audio = AudioEngine()
    if not audio.start():
        print("ERROR: Failed to start audio output stream.")
        cap.release()
        return

    tracker = HandTracker()
    violin = ViolinModel()
    gesture = GestureProcessor()
    ui = UIRenderer()
    tutorial = SongTutorialEngine()

    # FPS tracking
    fps_time = time.time()
    fps_counter = 0
    fps = 60

    play_mode_idx = 0
    timbre_mode_idx = 0

    print("Studio Engine Ready!")
    print("Press 'G' to switch between Normal Free Play and Song Tutorial Guide.")
    print("Press Q or ESC in the window to exit.")
    print("=" * 65)

    try:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                print("Failed to grab camera frame.")
                break

            # Mirror webcam frame for natural selfie interaction
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            # 3. Hand Tracking
            left_hand, right_hand = tracker.process(frame)

            # Draw Hand Skeletons
            if left_hand and "raw_landmarks" in left_hand:
                tracker.draw_landmarks(frame, left_hand["raw_landmarks"])
            if right_hand and "raw_landmarks" in right_hand:
                tracker.draw_landmarks(frame, right_hand["raw_landmarks"])

            # 4. Left Hand Violin Fretboard & Real Fingering Mechanics
            left_info = None
            if left_hand is not None:
                ix_norm = left_hand["index_smooth"][0] / float(w)
                iy_norm = left_hand["index_smooth"][1] / float(h)
                finger_count = left_hand.get("finger_count", 0)

                left_info = violin.process_left_hand(ix_norm, iy_norm, finger_count=finger_count)

                # Check for Pizzicato (pluck) trigger gesture
                if gesture.check_pizzicato_trigger(left_hand):
                    audio.trigger_pizzicato(left_info["freq"], velocity=0.85)

            # 5. Right Hand Bowing Physical Dynamics
            bow_info = gesture.process_bow(right_hand, w, h)

            # Trigger Downbow Accent Friction Bite on Stroke Change
            if bow_info.get("stroke_change", False):
                audio.trigger_stroke_accent()

            # 6. Mode Audio Dispatch
            if tutorial.mode == "TUTORIAL_GUIDE":
                # Tutorial Mode: Auto-play song tune & display target note marker
                auto_data = tutorial.update_auto_tune()
                if auto_data:
                    audio.update_params(
                        freq=auto_data["freq"],
                        volume=auto_data["volume"],
                        bow_speed=0.15,
                        pressure=0.5,
                        contact_point=0.5,
                    )
            else:
                # Normal Mode: 100% Hand Controlled
                if left_info is not None:
                    audio.update_params(
                        freq=left_info["freq"],
                        volume=bow_info["volume"],
                        bow_speed=bow_info["speed"],
                        pressure=bow_info["pressure"],
                        vibrato_depth=left_info["vibrato_depth"],
                        vibrato_freq=left_info["vibrato_freq"],
                        contact_point=bow_info.get("contact_point", 0.5),
                    )
                else:
                    audio.update_params(
                        freq=audio.current_freq,
                        volume=0.0,
                        bow_speed=0.0,
                        pressure=0.5,
                        contact_point=0.5,
                    )

            # 7. Render UI Overlays
            target_guide = tutorial.current_target() if tutorial.mode == "TUTORIAL_GUIDE" else None
            ui.draw_strings(frame, left_info, audio.current_volume, tutorial_target=target_guide)
            ui.draw_tuner_hud(frame, left_info)
            ui.draw_bow_hud(frame, bow_info)
            ui.draw_tutorial_panel(frame, tutorial)
            ui.draw_oscilloscope(frame, audio.scope_buffer)

            # FPS calculation
            fps_counter += 1
            if time.time() - fps_time >= 1.0:
                fps = fps_counter
                fps_counter = 0
                fps_time = time.time()

            ui.draw_header_and_controls(
                frame,
                audio_enabled=audio.audio_enabled,
                play_mode=violin.play_mode,
                timbre_mode=audio.timbre_mode,
                tutorial_mode=tutorial.mode,
                fps=fps,
            )

            # Display Window
            cv2.imshow(WINDOW_TITLE, frame)

            # Keyboard Input Handling
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # Q or ESC
                break
            elif key == ord(" "):  # Space to mute/unmute
                audio.toggle_audio()
            elif key == ord("g") or key == ord("G"):  # G to toggle Normal Free Play vs Tutorial Guide
                tutorial.toggle_mode()
                audio.play_chime(880.0)
            elif key == ord("h") or key == ord("H"):  # H for next practice song
                tutorial.next_song()
                audio.play_chime(987.77)
            elif key == ord("m") or key == ord("M"):  # M to change scale mode
                play_mode_idx = (play_mode_idx + 1) % len(PLAY_MODES)
                violin.play_mode = PLAY_MODES[play_mode_idx]
                audio.play_chime(783.99)
            elif key == ord("t") or key == ord("T"):  # T to change timbre sound model
                timbre_mode_idx = (timbre_mode_idx + 1) % len(TIMBRE_PRESETS)
                audio.set_timbre(TIMBRE_PRESETS[timbre_mode_idx])
            elif key == ord("r") or key == ord("R"):  # R to reset bow
                gesture.reset_bow()

    except Exception as e:
        print(f"Runtime Exception: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("Shutting down Invisible Violin...")
        audio.stop()
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()
        print("Shutdown complete. Thank you for playing!")


if __name__ == "__main__":
    main()
