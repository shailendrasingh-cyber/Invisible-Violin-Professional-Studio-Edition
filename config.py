"""
Config file for Invisible Violin Production Application.
Contains tuning constants, audio specifications, gesture parameters, and UI settings.
"""

# Audio Configuration
SAMPLE_RATE = 44100
BLOCK_SIZE = 256
AUDIO_CHANNELS = 1

# Standard Violin 4 Open Strings (in Hz)
VIOLIN_STRINGS = {
    "G": {"name": "G3", "midi": 55, "freq": 196.00, "color": (50, 180, 255)},   # Electric Cyan
    "D": {"name": "D4", "midi": 62, "freq": 293.66, "color": (50, 255, 150)},   # Emerald Green
    "A": {"name": "A4", "midi": 69, "freq": 440.00, "color": (255, 200, 50)},   # Warm Gold
    "E": {"name": "E5", "midi": 76, "freq": 659.25, "color": (255, 80, 150)},   # Hot Pink/Magenta
}

STRING_NAMES = ["G", "D", "A", "E"]

# Pitch Settings
PITCH_SMOOTHING = 0.15
VIBRATO_SENSITIVITY = 1.0  # Multiplier for hand oscillation detection

# Bowing Parameters
BOW_START_SPEED = 0.015
BOW_FULL_SPEED = 0.22
BOW_RELEASE_SPEED = 0.03
VOLUME_ATTACK = 0.15
VOLUME_RELEASE = 0.04

# Formant Filter Frequencies (Violin Body Resonances in Hz)
VIOLIN_BODY_FORMANTS = [
    {"freq": 280.0, "q": 3.5, "gain": 1.2},    # Air cavity (f-hole)
    {"freq": 520.0, "q": 4.0, "gain": 1.5},    # Main wood body
    {"freq": 1500.0, "q": 3.0, "gain": 1.1},   # Wood top plate
    {"freq": 3200.0, "q": 2.5, "gain": 1.4},   # Bridge resonance
    {"freq": 5500.0, "q": 2.0, "gain": 0.5},   # Rosin brilliance
]

# UI & Display
WINDOW_TITLE = "Invisible Violin - Professional Studio Edition"
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
TARGET_FPS = 60

# Modes & Timbre Presets
PLAY_MODES = ["CONTINUOUS", "CHROMATIC", "MAJOR_SCALE", "PENTATONIC"]
TIMBRE_PRESETS = [
    "SOLO_ACOUSTIC",
    "ELECTRIC_VIOLIN",
    "BAROQUE_WARM",
    "ORCHESTRAL_SECTION",
    "PIZZICATO_ONLY",
]
