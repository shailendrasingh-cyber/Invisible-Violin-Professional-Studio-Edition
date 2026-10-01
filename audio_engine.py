"""
Audio Engine for Invisible Violin — Real Violin Physics Edition.
Implements bowed string physical synthesis, Helmholtz slip-stick dynamics,
downbow attack accents, contact point timbre shifting (Sul Ponticello vs Sul Tasto),
sympathetic open-string resonance, body formant filtering, and Schroeder room reverb.
"""

import math
import sys
import os
import threading
import numpy as np

from scipy.signal import lfilter

from config import (
    SAMPLE_RATE,
    BLOCK_SIZE,
    VIOLIN_BODY_FORMANTS,
    TIMBRE_PRESETS,
)


class BiquadFilter:
    """IIR Biquad Filter for violin body formant synthesis."""

    def __init__(self, freq, q, gain, sample_rate=SAMPLE_RATE):
        w0 = 2.0 * np.pi * freq / sample_rate
        alpha = np.sin(w0) / (2.0 * q)
        
        # Bandpass filter coefficients
        b0 = alpha * gain
        b1 = 0.0
        b2 = -alpha * gain
        a0 = 1.0 + alpha
        a1 = -2.0 * np.cos(w0)
        a2 = 1.0 - alpha

        self.b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
        self.a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)

        # Filter state memory
        self.z1 = 0.0
        self.z2 = 0.0

    def process(self, x):
        """Process chunk using SciPy lfilter with state tracking."""
        zi = np.array([self.z1, self.z2], dtype=np.float64)
        y, zf = lfilter(self.b, self.a, x, zi=zi)
        self.z1, self.z2 = zf[0], zf[1]
        return y


class SchroederReverb:
    """Acoustic concert hall reverberation using Comb and Allpass filters."""

    def __init__(self, sample_rate=SAMPLE_RATE):
        self.comb_delays = [
            int(sample_rate * 0.0297),
            int(sample_rate * 0.0371),
            int(sample_rate * 0.0411),
            int(sample_rate * 0.0437),
        ]
        self.comb_gains = [0.80, 0.78, 0.75, 0.72]
        self.comb_buffers = [np.zeros(d, dtype=np.float64) for d in self.comb_delays]
        self.comb_indices = [0] * 4

        self.allpass_delays = [int(sample_rate * 0.005), int(sample_rate * 0.0017)]
        self.allpass_gain = 0.7
        self.allpass_buffers = [np.zeros(d, dtype=np.float64) for d in self.allpass_delays]
        self.allpass_indices = [0] * 2

    def process(self, input_signal, wet_level=0.25):
        if wet_level <= 0.001:
            return input_signal

        n = len(input_signal)
        comb_out = np.zeros(n, dtype=np.float64)

        for c in range(4):
            delay = self.comb_delays[c]
            gain = self.comb_gains[c]
            buf = self.comb_buffers[c]
            idx = self.comb_indices[c]

            for i in range(n):
                delayed_sample = buf[idx]
                buf[idx] = input_signal[i] + delayed_sample * gain
                comb_out[i] += delayed_sample
                idx = (idx + 1) % delay

            self.comb_indices[c] = idx

        ap_out = comb_out * 0.25
        for a in range(2):
            delay = self.allpass_delays[a]
            buf = self.allpass_buffers[a]
            idx = self.allpass_indices[a]

            for i in range(n):
                in_s = ap_out[i]
                d_s = buf[idx]
                buf[idx] = in_s + d_s * self.allpass_gain
                ap_out[i] = -in_s * self.allpass_gain + d_s * (1.0 - self.allpass_gain * self.allpass_gain)
                idx = (idx + 1) % delay

            self.allpass_indices[a] = idx

        return input_signal * (1.0 - wet_level) + ap_out * wet_level


class AudioEngine:
    """
    Real Bowed String Synthesizer Engine.
    Models Helmholtz friction, downbow attack accents, contact point timbres,
    sympathetic string resonance, body formants, and room reverb.
    """

    def __init__(self, sample_rate=SAMPLE_RATE, block_size=BLOCK_SIZE):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.lock = threading.Lock()

        # Dynamic Audio State
        self.target_freq = 440.0
        self.current_freq = 440.0
        self.target_volume = 0.0
        self.current_volume = 0.0
        self.target_pressure = 0.5
        self.current_pressure = 0.5
        self.bow_speed = 0.0
        self.vibrato_depth = 0.0
        self.vibrato_freq = 5.5
        self.contact_point = 0.5  # 0.0 = Sul Ponticello (bridge), 1.0 = Sul Tasto (fingerboard)

        # Stroke attack accent (Downbow bite)
        self.stroke_accent = 0.0

        # Pizzicato State
        self.pizz_active = False
        self.pizz_freq = 440.0
        self.pizz_phase = 0.0
        self.pizz_envelope = 0.0

        # Chime Feedback
        self.chime_phase = 0.0
        self.chime_freq = 880.0
        self.chime_envelope = 0.0

        # Oscillators
        self.main_phase = 0.0
        self.vibrato_phase = 0.0
        self.ens_phase1 = 0.0
        self.ens_phase2 = 0.0
        self.sympathetic_phase = 0.0

        # Timbre settings
        self.timbre_mode = "SOLO_ACOUSTIC"
        self.audio_enabled = True

        # Formant Filter Bank
        self.formants = [
            BiquadFilter(f["freq"], f["q"], f["gain"], sample_rate)
            for f in VIOLIN_BODY_FORMANTS
        ]

        # Reverb
        self.reverb = SchroederReverb(sample_rate)

        # Oscilloscope visualizer buffer
        self.scope_buffer = np.zeros(512, dtype=np.float32)

        # Audio stream
        self.stream = None

    def start(self):
        import sounddevice as sd
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
            )
            self.stream.start()
            return True
        except Exception as e:
            print(f"[AudioEngine Error] Failed to open audio stream: {e}")
            return False

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def play_chime(self, freq=880.0):
        with self.lock:
            self.chime_freq = freq
            self.chime_phase = 0.0
            self.chime_envelope = 0.70

    def trigger_stroke_accent(self):
        """Trigger downbow dynamic attack accent (friction bite)."""
        with self.lock:
            self.stroke_accent = 0.85

    def trigger_pizzicato(self, freq, velocity=1.0):
        with self.lock:
            self.pizz_active = True
            self.pizz_freq = freq
            self.pizz_phase = 0.0
            self.pizz_envelope = min(1.0, max(0.25, velocity))

    def update_params(self, freq, volume, bow_speed, pressure=0.5, vibrato_depth=0.0, vibrato_freq=5.5, contact_point=0.5):
        with self.lock:
            self.target_freq = freq
            self.target_volume = volume if self.audio_enabled else 0.0
            self.bow_speed = bow_speed
            self.target_pressure = pressure
            self.vibrato_depth = vibrato_depth
            self.vibrato_freq = vibrato_freq
            self.contact_point = contact_point

    def set_timbre(self, timbre_name):
        with self.lock:
            self.timbre_mode = timbre_name
        self.play_chime(1046.5)

    def toggle_audio(self):
        with self.lock:
            self.audio_enabled = not self.audio_enabled
            if self.audio_enabled:
                self.play_chime(659.25)
            return self.audio_enabled

    def _generate_helmholtz_wave(self, freq, pressure, contact, frames):
        """
        Synthesizes Helmholtz bowed string wave with contact point timbre shifting:
        Sul Ponticello (near bridge) = high harmonic bite.
        Sul Tasto (near fingerboard) = soft warm fundamental.
        """
        t = np.arange(frames, dtype=np.float64)
        
        # Vibrato LFO
        vib_lfo = np.sin(self.vibrato_phase + 2.0 * np.pi * self.vibrato_freq / self.sample_rate * t)
        inst_freq = freq + self.vibrato_depth * vib_lfo
        inst_freq = np.maximum(20.0, inst_freq)

        # Phase accumulation
        phase_inc = 2.0 * np.pi * inst_freq / self.sample_rate
        phases = self.main_phase + np.cumsum(phase_inc)
        wrapped_phases = phases % (2.0 * np.pi)

        # Helmholtz Sawtooth with dynamic bow pressure corner rounding
        saw = (wrapped_phases / np.pi) - 1.0
        sharpness = 0.5 + 2.8 * pressure
        wave = np.tanh(saw * sharpness)

        # Contact Point Timbre Shift (Sul Ponticello vs Sul Tasto)
        # Low contact (Sul Ponticello) boosts upper harmonics; High contact (Sul Tasto) softens fundamental
        pont_factor = (1.0 - contact) * 0.45
        tasto_factor = contact * 0.35

        h2 = (0.35 + pont_factor) * np.sin(2.0 * wrapped_phases)
        h3 = (0.22 + pont_factor * 1.2) * np.sin(3.0 * wrapped_phases)
        h4 = (0.12 + pont_factor * 1.5) * np.sin(4.0 * wrapped_phases)
        h6 = 0.05 * np.sin(6.0 * wrapped_phases)

        wave = wave * (0.65 - tasto_factor) + h2 + h3 + h4 + h6

        self.main_phase = (self.main_phase + np.sum(phase_inc)) % (2.0 * np.pi)
        self.vibrato_phase = (self.vibrato_phase + 2.0 * np.pi * self.vibrato_freq / self.sample_rate * frames) % (2.0 * np.pi)

        return wave

    def _audio_callback(self, outdata, frames, callback_time, status):
        with self.lock:
            target_f = self.target_freq
            target_v = self.target_volume
            target_p = self.target_pressure
            speed = self.bow_speed
            contact = self.contact_point
            timbre = self.timbre_mode

        # Exponential parameter smoothing
        self.current_freq += (target_f - self.current_freq) * 0.14
        if target_v > self.current_volume:
            self.current_volume += (target_v - self.current_volume) * 0.24
        else:
            self.current_volume += (target_v - self.current_volume) * 0.05

        self.current_pressure += (target_p - self.current_pressure) * 0.10

        sound = np.zeros(frames, dtype=np.float64)

        # Handle Chime Tone
        if self.chime_envelope > 0.005:
            t_chime = np.arange(frames, dtype=np.float64)
            chime_inc = 2.0 * np.pi * self.chime_freq / self.sample_rate
            chime_wave = np.sin(self.chime_phase + chime_inc * t_chime) * self.chime_envelope * 0.15
            sound += chime_wave
            self.chime_phase = (self.chime_phase + chime_inc * frames) % (2.0 * np.pi)
            self.chime_envelope *= math.exp(-frames / (self.sample_rate * 0.08))

        if self.current_volume > 0.0005 or self.pizz_active or timbre == "PIZZICATO_ONLY":
            raw_wave = self._generate_helmholtz_wave(self.current_freq, self.current_pressure, contact, frames)

            # Rosin Friction Noise (horsehair friction on string)
            if speed > 0.01 and self.current_volume > 0.001:
                rosin_noise = (np.random.rand(frames) * 2.0 - 1.0) * (0.042 * np.sqrt(speed))
                raw_wave += rosin_noise

            # Downbow Stroke Accent transient (friction bite at stroke start)
            if self.stroke_accent > 0.01:
                t_acc = np.arange(frames, dtype=np.float64)
                accent_env = np.exp(-t_acc / (self.sample_rate * 0.04)) * self.stroke_accent
                raw_wave += (np.random.rand(frames) * 2.0 - 1.0) * accent_env * 0.18
                self.stroke_accent *= math.exp(-frames / (self.sample_rate * 0.05))

            # Sympathetic String Resonance (subtle wooden body open string vibration)
            symp_inc = 2.0 * np.pi * 196.0 / self.sample_rate  # G3 sympathetic base
            symp_wave = 0.06 * np.sin(self.sympathetic_phase + symp_inc * np.arange(frames))
            self.sympathetic_phase = (self.sympathetic_phase + symp_inc * frames) % (2.0 * np.pi)
            raw_wave += symp_wave

            # Timbre Models
            if timbre == "ELECTRIC_VIOLIN":
                octave_sub = 0.35 * np.sin(self.main_phase * 0.5)
                dist_wave = np.tanh((raw_wave + octave_sub) * 4.5)
                sound += dist_wave * self.current_volume * 0.40

            elif timbre == "BAROQUE_WARM":
                body_wave = self.formants[0].process(raw_wave) * 1.5 + self.formants[1].process(raw_wave) * 1.3
                sound += body_wave * self.current_volume * 0.38

            elif timbre == "ORCHESTRAL_SECTION":
                t_ens = np.arange(frames, dtype=np.float64)
                f1 = self.current_freq * 0.995
                f2 = self.current_freq * 1.005

                inc1 = 2.0 * np.pi * f1 / self.sample_rate
                inc2 = 2.0 * np.pi * f2 / self.sample_rate

                v1 = np.sin(self.ens_phase1 + inc1 * t_ens)
                v2 = np.sin(self.ens_phase2 + inc2 * t_ens)

                self.ens_phase1 = (self.ens_phase1 + inc1 * frames) % (2.0 * np.pi)
                self.ens_phase2 = (self.ens_phase2 + inc2 * frames) % (2.0 * np.pi)

                ens_wave = (raw_wave * 0.5 + v1 * 0.28 + v2 * 0.28)
                sound += ens_wave * self.current_volume * 0.42

            elif timbre == "PIZZICATO_ONLY":
                if speed > 0.05 and not self.pizz_active:
                    self.trigger_pizzicato(self.current_freq, velocity=min(1.0, speed * 4.0))

            else:
                # SOLO_ACOUSTIC: Wooden acoustic violin body resonance
                body_wave = np.zeros(frames, dtype=np.float64)
                for filter_band in self.formants:
                    body_wave += filter_band.process(raw_wave)

                sound += (body_wave * 0.40 + raw_wave * 0.20) * self.current_volume * 0.48

        # Pizzicato Pluck
        if self.pizz_active:
            t_pizz = np.arange(frames, dtype=np.float64)
            pizz_inc = 2.0 * np.pi * self.pizz_freq / self.sample_rate
            pizz_phases = self.pizz_phase + pizz_inc * t_pizz
            
            decay = np.exp(-t_pizz / (self.sample_rate * 0.25))
            pizz_wave = (np.sin(pizz_phases) + 0.3 * np.sin(pizz_phases * 2.0)) * self.pizz_envelope * decay
            sound += pizz_wave * 0.75
            
            self.pizz_phase = (self.pizz_phase + pizz_inc * frames) % (2.0 * np.pi)
            self.pizz_envelope *= math.exp(-frames / (self.sample_rate * 0.30))
            if self.pizz_envelope < 0.001:
                self.pizz_active = False

        # Concert Hall Reverb
        reverb_level = 0.28 if timbre in ["SOLO_ACOUSTIC", "ORCHESTRAL_SECTION"] else 0.15
        sound = self.reverb.process(sound, wet_level=reverb_level)

        # Soft Clip
        output = np.tanh(sound)

        outdata[:, 0] = output.astype(np.float32)

        # Update Oscilloscope
        shift = min(frames, len(self.scope_buffer))
        self.scope_buffer = np.roll(self.scope_buffer, -shift)
        self.scope_buffer[-shift:] = output[-shift:].astype(np.float32)
