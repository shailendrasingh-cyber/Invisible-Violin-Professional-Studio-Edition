"""
Tutorial & Song Practice Guide Module for Invisible Violin.
Contains classic violin practice melodies, automatic song tune playback,
interactive pitch guide, and seamless switching between Normal Free Play & Practice Tutorial.
"""

import time
from config import VIOLIN_STRINGS

TUTORIAL_SONGS = [
    {
        "title": "Twinkle Twinkle Little Star",
        "composer": "Mozart / Traditional",
        "bpm": 105,
        "notes": [
            {"name": "G3", "midi": 55, "string": "G", "dur": 0.5},
            {"name": "G3", "midi": 55, "string": "G", "dur": 0.5},
            {"name": "D4", "midi": 62, "string": "D", "dur": 0.5},
            {"name": "D4", "midi": 62, "string": "D", "dur": 0.5},
            {"name": "E4", "midi": 64, "string": "D", "dur": 0.5},
            {"name": "E4", "midi": 64, "string": "D", "dur": 0.5},
            {"name": "D4", "midi": 62, "string": "D", "dur": 0.9},
            {"name": "C4", "midi": 60, "string": "G", "dur": 0.5},
            {"name": "C4", "midi": 60, "string": "G", "dur": 0.5},
            {"name": "B3", "midi": 59, "string": "G", "dur": 0.5},
            {"name": "B3", "midi": 59, "string": "G", "dur": 0.5},
            {"name": "A3", "midi": 57, "string": "G", "dur": 0.5},
            {"name": "A3", "midi": 57, "string": "G", "dur": 0.5},
            {"name": "G3", "midi": 55, "string": "G", "dur": 0.9},
        ],
    },
    {
        "title": "Ode to Joy",
        "composer": "L. v. Beethoven",
        "bpm": 115,
        "notes": [
            {"name": "B4", "midi": 71, "string": "A", "dur": 0.5},
            {"name": "B4", "midi": 71, "string": "A", "dur": 0.5},
            {"name": "C5", "midi": 72, "string": "A", "dur": 0.5},
            {"name": "D5", "midi": 74, "string": "A", "dur": 0.5},
            {"name": "D5", "midi": 74, "string": "A", "dur": 0.5},
            {"name": "C5", "midi": 72, "string": "A", "dur": 0.5},
            {"name": "B4", "midi": 71, "string": "A", "dur": 0.5},
            {"name": "A4", "midi": 69, "string": "A", "dur": 0.5},
            {"name": "G4", "midi": 67, "string": "D", "dur": 0.5},
            {"name": "G4", "midi": 67, "string": "D", "dur": 0.5},
            {"name": "A4", "midi": 69, "string": "A", "dur": 0.5},
            {"name": "B4", "midi": 71, "string": "A", "dur": 0.5},
            {"name": "B4", "midi": 71, "string": "A", "dur": 0.75},
            {"name": "A4", "midi": 69, "string": "A", "dur": 0.25},
            {"name": "A4", "midi": 69, "string": "A", "dur": 0.9},
        ],
    },
    {
        "title": "Canon in D",
        "composer": "J. Pachelbel",
        "bpm": 95,
        "notes": [
            {"name": "D5", "midi": 74, "string": "A", "dur": 0.6},
            {"name": "C#5", "midi": 73, "string": "A", "dur": 0.6},
            {"name": "B4", "midi": 71, "string": "A", "dur": 0.6},
            {"name": "A4", "midi": 69, "string": "A", "dur": 0.6},
            {"name": "G4", "midi": 67, "string": "D", "dur": 0.6},
            {"name": "F#4", "midi": 66, "string": "D", "dur": 0.6},
            {"name": "G4", "midi": 67, "string": "D", "dur": 0.6},
            {"name": "A4", "midi": 69, "string": "A", "dur": 0.6},
        ],
    },
    {
        "title": "Spring (Four Seasons)",
        "composer": "A. Vivaldi",
        "bpm": 125,
        "notes": [
            {"name": "E5", "midi": 76, "string": "E", "dur": 0.5},
            {"name": "G#5", "midi": 80, "string": "E", "dur": 0.5},
            {"name": "G#5", "midi": 80, "string": "E", "dur": 0.5},
            {"name": "G#5", "midi": 80, "string": "E", "dur": 0.5},
            {"name": "F#5", "midi": 78, "string": "E", "dur": 0.4},
            {"name": "E5", "midi": 76, "string": "E", "dur": 0.4},
            {"name": "B4", "midi": 71, "string": "A", "dur": 0.8},
            {"name": "E5", "midi": 76, "string": "E", "dur": 0.9},
        ],
    },
]


class SongTutorialEngine:
    """Manages Automatic Song Playback & Practice Guide."""

    def __init__(self):
        self.active_song_idx = 0
        self.note_idx = 0
        # Modes: "NORMAL_FREE_PLAY" vs "TUTORIAL_GUIDE"
        self.mode = "NORMAL_FREE_PLAY"
        
        self.auto_play = True  # Plays sound automatically in tutorial mode
        self.note_timer = time.time()
        self.score = 0
        self.feedback_text = "PRESS 'G' TO TOGGLE TUTORIAL MODE"

    def current_song(self):
        return TUTORIAL_SONGS[self.active_song_idx]

    def current_target(self):
        song = self.current_song()
        notes = song["notes"]
        return notes[self.note_idx % len(notes)]

    def toggle_mode(self):
        """Switch between Normal Free Play and Tutorial Practice Guide."""
        if self.mode == "NORMAL_FREE_PLAY":
            self.mode = "TUTORIAL_GUIDE"
            self.note_idx = 0
            self.note_timer = time.time()
            self.feedback_text = f"TUTORIAL: {self.current_song()['title']} (Auto-Playing Guide Tune)"
        else:
            self.mode = "NORMAL_FREE_PLAY"
            self.feedback_text = "NORMAL MODE: Play Freely with your Hands!"
        return self.mode

    def next_song(self):
        self.active_song_idx = (self.active_song_idx + 1) % len(TUTORIAL_SONGS)
        self.note_idx = 0
        self.note_timer = time.time()
        self.feedback_text = f"TUTORIAL SONG: {self.current_song()['title']}"

    def update_auto_tune(self):
        """
        Calculates automatic audio pitch and bowing parameters for the current song note.
        Steps to the next note based on note duration.
        """
        if self.mode != "TUTORIAL_GUIDE" or not self.auto_play:
            return None

        now = time.time()
        target = self.current_target()
        dur = target.get("dur", 0.5)

        # Advance note when timer expires
        if now - self.note_timer >= dur:
            self.note_timer = now
            self.note_idx = (self.note_idx + 1) % len(self.current_song()["notes"])
            target = self.current_target()

        elapsed = now - self.note_timer
        note_progress = elapsed / dur

        # Bow volume envelope for natural violin note articulation (attack & release)
        if note_progress < 0.20:
            vol = note_progress / 0.20 * 0.70  # Attack
        elif note_progress > 0.80:
            vol = (1.0 - note_progress) / 0.20 * 0.70  # Release
        else:
            vol = 0.70  # Sustain

        freq = 440.0 * (2.0 ** ((target["midi"] - 69) / 12.0))

        return {
            "freq": freq,
            "midi": target["midi"],
            "string": target["string"],
            "volume": max(0.08, vol),
            "target": target,
        }
