# 🎻 Invisible Violin — Professional Studio Edition

<div align="center">

**An AI-powered computer vision & acoustic DSP studio that turns your webcam and bare hands into a real violin.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

**Author: Shailendra Singh**

</div>

---

## 📖 What Is This?

**Invisible Violin** is a real-time computer vision and digital signal processing (DSP) application that lets you play a virtual violin in mid-air — no instrument required. Your **left hand** fingers the notes on the virtual fingerboard, and your **right hand** bows the strings. The physics engine models genuine Helmholtz slip-stick bowing dynamics, wooden body acoustic formant resonances, rosin friction noise, expressive vibrato, downbow/upbow stroke transients, and pizzicato plucking gestures.

---

## ✨ Features

### 🎧 5 Distinct Violin Sound Models
Cycle through with the `T` key:

| Model | Description |
|:------|:------------|
| **SOLO ACOUSTIC** | Warm wooden acoustic violin — 5-band body formants, rosin friction noise, Helmholtz synthesis, concert hall reverb |
| **ELECTRIC VIOLIN** | High-gain tube overdrive (`tanh` saturation) with octave crunch — rock violin solos |
| **BAROQUE WARM** | Dark gut-string tone with deep air-cavity resonance and low-pass filtering |
| **ORCHESTRAL SECTION** | Multi-voice ensemble effect — 3 detuned strings (−8¢, 0¢, +8¢) simulating a full symphony violin section |
| **PIZZICATO ONLY** | Percussive plucked string synth on every bow stroke or left-hand finger pinch |

---

### 🎵 4 Scale / Play Modes
Cycle with the `M` key:

| Mode | Description |
|:-----|:------------|
| **CONTINUOUS** | Fretless microtonal slides & expressive glissando — like a real violin fingerboard |
| **CHROMATIC** | Snaps to the nearest semitone — pitch tuner needle shows cents deviation |
| **MAJOR SCALE** | Snaps to the C Major diatonic scale — great for beginners |
| **PENTATONIC** | 5-note pentatonic scale — always sounds musical |

---

### 🎓 Interactive Tutorial & Song Practice Guide
Press `G` to activate, `H` to cycle songs:

| Song | Composer | BPM |
|:-----|:---------|:----|
| Twinkle Twinkle Little Star | Mozart / Traditional | 105 |
| Ode to Joy | L. v. Beethoven | 115 |
| Canon in D | J. Pachelbel | 95 |
| Spring (Four Seasons) | A. Vivaldi | 125 |

- **Auto-Play Mode**: The song plays automatically so you can hear how it should sound
- **Visual Target Guide Ring**: A glowing ring shows exactly where your finger should be on the string
- **Pitch Arrows**: On-screen arrows (↑ / ↓) guide you to the correct position in real time
- **Instant Switch**: Press `G` to jump back to free play at any time

---

### 🎻 Realistic Violin Mechanics

| Mechanic | How It Works |
|:---------|:-------------|
| **4 Open Strings** | G3 (196 Hz), D4 (293.66 Hz), A4 (440 Hz), E5 (659.25 Hz) — mapped to horizontal hand position |
| **Fingerboard Positions** | 1st Position, 3rd Position (+5 semitones), 5th Position (+9 semitones) — mapped to hand height |
| **Finger Placement** | Open string + 1st, 2nd, 3rd, 4th finger offsets — based on left-hand extended finger count |
| **Vibrato** | Rapid left-hand Y oscillation is detected and converted to pitch modulation (3–9 Hz) |
| **Bow Dynamics** | Right-hand horizontal speed → volume; vertical position → Sul Ponticello / Sul Tasto timbre shift |
| **Downbow / Upbow** | Stroke direction changes trigger a friction bite accent transient |
| **Pizzicato** | Left-hand thumb-index pinch (distance < 28px) triggers a pluck sound |
| **Double-Stop Chords** | Chord mode adds a Perfect 5th harmonic above the played note |

---

## 🖥️ System Requirements

| Component | Minimum |
|:----------|:--------|
| Python | 3.9 or higher |
| Webcam | Any USB or built-in camera (720p+ recommended) |
| OS | Windows 10/11, macOS, Linux |
| RAM | 4 GB |
| CPU | Intel i5 / AMD Ryzen 5 or better (for real-time MediaPipe hand tracking) |

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/shailendra-singh/invisible-violin.git
cd invisible-violin
```

### 2. Install dependencies
```bash
pip install opencv-python mediapipe sounddevice numpy scipy
```

### 3. Run the application
```bash
python main.py
```

### Optional: Specify a different camera index
```bash
python main.py --camera 1
```

---

## 🎮 Controls Reference

### ⌨️ Keyboard Shortcuts

| Key | Action |
|:----|:-------|
| `G` | Toggle **Tutorial Guide** ON / OFF |
| `H` | Next practice song |
| `T` | Cycle sound model (Acoustic → Electric → Baroque → Orchestra → Pizzicato) |
| `M` | Cycle play mode (Continuous → Chromatic → Major → Pentatonic) |
| `SPACE` | Mute / Unmute audio |
| `R` | Reset bow tracking |
| `Q` or `ESC` | Quit |

### 🤚 Hand Gestures

| Gesture | Action |
|:--------|:-------|
| **Left hand — move horizontally** | Switch violin string (left = G3, right = E5) |
| **Left hand — move vertically** | Change pitch on the fingerboard (up = higher register) |
| **Left hand — extend fingers** | Finger placement (0 fingers = open string, 1–4 fingers = 1st–4th finger) |
| **Left hand — oscillate up/down** | Vibrato (detected automatically from wrist oscillation) |
| **Left hand — pinch thumb + index** | Pizzicato pluck |
| **Right hand — move left/right** | Bow the string (speed = volume) |
| **Right hand — move up/down** | Contact point (top = Sul Tasto warm, bottom = Sul Ponticello bright) |

---

## 🏗️ Project Architecture

```
invisible_violin/
│
├── main.py            # Entry point — webcam loop, keyboard input, subsystem orchestration
├── config.py          # Audio tuning, string MIDI definitions, UI constants, formant values
│
├── audio_engine.py    # Helmholtz bowed string synthesis, 5 sound models, formant filter bank,
│                      #   rosin noise, Schroeder concert hall reverb, oscilloscope buffer
│
├── hand_tracker.py    # MediaPipe Hands wrapper — dual-hand detection, One-Euro smoothing,
│                      #   landmark extraction (wrist, index, pinch distance, finger count)
│
├── violin.py          # 4-string fingerboard model — string selection with hysteresis,
│                      #   position shifting, finger semitone offsets, scale snapping,
│                      #   vibrato detector, double-stop chord harmonization
│
├── gesture.py         # Right-hand bow velocity, stroke direction change, pressure estimation,
│                      #   Sul Ponticello/Tasto contact point, pizzicato pinch detector
│
├── tutorial.py        # Song practice engine — 4 classic melodies, auto-play with ADSR envelope,
│                      #   note timing, pitch target guide, mode switching
│
├── ui_renderer.py     # Glassmorphic HUD — violin silhouette, f-holes, bridge, bow stick,
│                      #   vibrating string animation, tuner dial, oscilloscope, target guide ring
│
└── README.md          # This file
```

---

## 🔊 Audio Engine Deep Dive

The audio engine (`audio_engine.py`) implements:

1. **Helmholtz Bowed String Synthesis** — a sawtooth wave shaped by `tanh` saturation models the nonlinear Helmholtz slip-stick friction between the bow and string. Bow pressure controls the wave's sharpness (corner rounding).

2. **Contact Point Timbre Shifting**
   - **Sul Ponticello** (bow near the bridge) → upper harmonics (H2–H4) are boosted → bright, glassy tone
   - **Sul Tasto** (bow near the fingerboard) → fundamental is softened → warm, hollow tone

3. **Body Formant Filter Bank** — 5 biquad bandpass filters tuned to real violin body resonance modes (280 Hz, 520 Hz, 1500 Hz, 3200 Hz, 5500 Hz) colour the raw string output to simulate a wooden instrument body.

4. **Rosin Friction Noise** — low-level band-limited noise scaled by bow speed adds the characteristic gritty "hair on string" texture.

5. **Sympathetic Resonance** — a subtle G3 drone represents the open-string sympathetic vibration.

6. **Schroeder Concert Hall Reverb** — 4 feedback comb filters + 2 Schroeder allpass filters simulate a small concert hall acoustic space.

---

## 📁 Configuration (`config.py`)

```python
SAMPLE_RATE = 44100          # Audio sample rate (Hz)
BLOCK_SIZE  = 256            # Audio callback block size (samples)

VIOLIN_STRINGS = {
    "G": { "midi": 55, "freq": 196.00 },   # G3
    "D": { "midi": 62, "freq": 293.66 },   # D4
    "A": { "midi": 69, "freq": 440.00 },   # A4
    "E": { "midi": 76, "freq": 659.25 },   # E5
}

PLAY_MODES     = ["CONTINUOUS", "CHROMATIC", "MAJOR_SCALE", "PENTATONIC"]
TIMBRE_PRESETS = ["SOLO_ACOUSTIC", "ELECTRIC_VIOLIN", "BAROQUE_WARM",
                  "ORCHESTRAL_SECTION", "PIZZICATO_ONLY"]
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|:--------|:---------|
| **No audio output** | Press `SPACE` to unmute. Check your system default audio output device. |
| **Camera not opening** | Try `python main.py --camera 1` to switch to a secondary camera |
| **Hand tracking laggy** | Ensure good lighting. Reduce background clutter. |
| **`ModuleNotFoundError`** | Run `pip install opencv-python mediapipe sounddevice numpy scipy` |
| **Only one hand detected** | MediaPipe detects up to 2 hands. Ensure both hands are visible in frame. |
| **E string hard to reach** | Move your left hand to the far right side of the camera frame |

---

## 📜 License

This project is released under the **MIT License** — free to use, modify, and distribute with attribution.

---

## 👤 Author

<div align="center">

**Shailendra Singh**

*Creator & Lead Developer — Invisible Violin Professional Studio Edition*

</div>
