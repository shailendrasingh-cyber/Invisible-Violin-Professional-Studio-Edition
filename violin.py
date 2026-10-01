"""
Violin Fretboard, Double-Stop Chords, & Responsive String Selection Model.
Implements easy E-string access (widened 0.15 to 0.85 horizontal range),
Double-Stop Chord Harmonization (Major 3rds & Perfect 5ths),
authentic violin fingering (Open + 1st, 2nd, 3rd, 4th finger), and position shifting.
"""

import math
import time
import numpy as np

from config import VIOLIN_STRINGS, STRING_NAMES


def midi_to_freq(midi_note):
    """Convert MIDI note number to frequency in Hz."""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def freq_to_midi(freq):
    """Convert frequency in Hz to fractional MIDI note number."""
    if freq <= 0:
        return 69.0
    return 69.0 + 12.0 * math.log2(freq / 440.0)


def midi_to_note_name(midi_note):
    """Convert MIDI note number to musical note string e.g. A4, C#5."""
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    rounded = int(round(midi_note))
    note = names[rounded % 12]
    octave = (rounded // 12) - 1
    return f"{note}{octave}"


SCALES = {
    "MAJOR_SCALE": [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24],
    "PENTATONIC": [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24],
}


class VibratoDetector:
    """Detects rapid left-hand finger position oscillations for physical vibrato."""

    def __init__(self, history_len=15):
        self.history = []
        self.timestamps = []
        self.history_len = history_len

    def update(self, pos_y):
        now = time.time()
        self.history.append(pos_y)
        self.timestamps.append(now)

        if len(self.history) > self.history_len:
            self.history.pop(0)
            self.timestamps.pop(0)

        if len(self.history) < 8:
            return 0.0, 5.5

        arr = np.array(self.history)
        amp = (np.max(arr) - np.min(arr))

        mean = np.mean(arr)
        zero_crossings = np.where(np.diff(np.sign(arr - mean)))[0]

        dt = self.timestamps[-1] - self.timestamps[0]
        freq_hz = 5.5
        if dt > 0.05 and len(zero_crossings) >= 2:
            freq_hz = (len(zero_crossings) / 2.0) / dt
            freq_hz = max(3.0, min(9.0, freq_hz))

        vibrato_depth = max(0.0, min(14.0, (amp - 0.003) * 600.0))
        return vibrato_depth, freq_hz


class ViolinModel:
    """Violin Fretboard & Chord Controller."""

    def __init__(self):
        self.active_string_idx = 2  # Default to 'A' string
        self.play_mode = "CONTINUOUS"
        self.double_stop_chord = False  # Toggle Double-Stop Chord Mode
        self.smoothed_pitch = 69.0  # MIDI A4
        self.vibrato_detector = VibratoDetector()

        # Fingering offset map (in semitones)
        self.finger_semitones = [0, 2, 4, 5, 7]

    def select_string_responsive(self, hand_x_norm):
        """
        Responsive string selection with widened boundaries across [0.15, 0.85].
        E-string is now extremely easy to reach on the right side of the screen.
        """
        curr = self.active_string_idx
        # Boundaries: G (x < 0.32), D (0.32-0.49), A (0.49-0.66), E (x >= 0.66)
        margin = 0.035

        if curr == 0 and hand_x_norm > (0.32 + margin):
            curr = 1
        elif curr == 1:
            if hand_x_norm < (0.32 - margin):
                curr = 0
            elif hand_x_norm > (0.49 + margin):
                curr = 2
        elif curr == 2:
            if hand_x_norm < (0.49 - margin):
                curr = 1
            elif hand_x_norm > (0.66 + margin):
                curr = 3
        elif curr == 3 and hand_x_norm < (0.66 - margin):
            curr = 2

        # Direct override if far right or far left
        if hand_x_norm >= 0.68:
            curr = 3  # E String
        elif hand_x_norm <= 0.28:
            curr = 0  # G String

        self.active_string_idx = curr
        return STRING_NAMES[curr]

    def toggle_chord_mode(self):
        """Toggle Double-Stop Violin Chord mode."""
        self.double_stop_chord = not self.double_stop_chord
        return self.double_stop_chord

    def process_left_hand(self, hand_x_norm, hand_y_norm, finger_count=0):
        """
        Process left hand with responsive E-string access, position shifting, and double-stop chord harmonization.
        """
        string_name = self.select_string_responsive(hand_x_norm)
        open_string_info = VIOLIN_STRINGS[string_name]
        base_midi = open_string_info["midi"]

        # 1. Position Shift (1st, 3rd, 5th position based on Y height)
        if hand_y_norm > 0.62:
            pos_shift = 0   # 1st Position
            pos_name = "1st Pos"
        elif hand_y_norm > 0.32:
            pos_shift = 5   # 3rd Position (+5 semitones)
            pos_name = "3rd Pos"
        else:
            pos_shift = 9   # 5th Position (+9 semitones)
            pos_name = "5th Pos"

        # 2. Finger Placement (Open, 1st, 2nd, 3rd, 4th finger)
        finger_idx = min(4, max(0, finger_count))
        finger_offset = self.finger_semitones[finger_idx]

        # 3. Calculate target pitch
        if self.play_mode == "CONTINUOUS":
            norm_pos = max(0.0, min(1.0, 1.0 - ((hand_y_norm - 0.08) / 0.85)))
            raw_midi = base_midi + pos_shift + finger_offset + (norm_pos * 2.5 - 1.0)
            target_midi = raw_midi
        elif self.play_mode == "CHROMATIC":
            target_midi = base_midi + pos_shift + finger_offset
        elif self.play_mode in SCALES:
            raw = base_midi + pos_shift + finger_offset
            scale_intervals = SCALES[self.play_mode]
            offset = raw - base_midi
            closest_interval = min(scale_intervals, key=lambda x: abs(x - offset))
            target_midi = base_midi + closest_interval

        # 4. Inertial pitch smoothing
        smoothing = 0.28 if self.play_mode == "CONTINUOUS" else 0.45
        self.smoothed_pitch += (target_midi - self.smoothed_pitch) * smoothing

        freq = midi_to_freq(self.smoothed_pitch)

        # 5. Double-Stop Chord Harmonization (Perfect 5th or Major 3rd interval)
        chord_freq = None
        if self.double_stop_chord:
            chord_midi = self.smoothed_pitch + 7.0  # Perfect 5th double stop
            chord_freq = midi_to_freq(chord_midi)

        exact_midi = freq_to_midi(freq)
        nearest_midi = round(exact_midi)
        cents = (exact_midi - nearest_midi) * 100.0
        note_name = midi_to_note_name(nearest_midi)

        vib_depth, vib_freq = self.vibrato_detector.update(hand_y_norm)

        return {
            "freq": freq,
            "chord_freq": chord_freq,
            "midi": self.smoothed_pitch,
            "target_midi": target_midi,
            "note_name": note_name,
            "cents": cents,
            "string": string_name,
            "string_info": open_string_info,
            "pos_name": pos_name,
            "finger_number": finger_idx,
            "vibrato_depth": vib_depth,
            "vibrato_freq": vib_freq,
            "chord_active": self.double_stop_chord,
        }
