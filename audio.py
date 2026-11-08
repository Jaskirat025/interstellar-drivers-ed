"""Procedural sound for the simulator.

Every sound is synthesised to a temporary WAV the first time it is needed.
Pygame mixes the effects and the loops; if no audio device or no pygame is
available the engine degrades to silence instead of breaking the game.
"""

import math
import os
import random
import struct
import tempfile
import wave

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

try:  # pygame is optional at import time so headless tests stay silent.
    import pygame
except Exception:  # pragma: no cover - exercised on machines without pygame
    pygame = None

RATE = 22050


def _clamp(value):
    return -1.0 if value < -1.0 else 1.0 if value > 1.0 else value


def _sine(frequency, t):
    return math.sin(2.0 * math.pi * frequency * t)


def _square(frequency, t):
    return 1.0 if _sine(frequency, t) >= 0 else -1.0


def _envelope(t, duration, attack=0.01, release=0.08):
    attack = max(0.001, attack)
    release = max(0.001, release)
    if t < attack:
        return t / attack
    if t > duration - release:
        return max(0.0, (duration - t) / release)
    return 1.0


def _samples(duration, fn):
    count = int(RATE * duration)
    return [fn(index / float(RATE), duration) for index in range(count)]


def _write_wav(path, samples):
    frames = bytearray()
    for sample in samples:
        frames.extend(struct.pack("<h", int(_clamp(sample) * 32767.0)))
    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(bytes(frames))


def _click(t, duration):
    return 0.26 * _sine(1500, t) * _envelope(t, duration, 0.002, 0.03)


def _confirm(t, duration):
    frequency = 660 if t < duration * 0.45 else 990
    return 0.28 * _sine(frequency, t) * _envelope(t, duration, 0.01, 0.06)


def _deny(t, duration):
    frequency = 190 if int(t * 9) % 2 else 130
    return 0.20 * _square(frequency, t) * _envelope(t, duration, 0.01, 0.05)


def _servo(t, duration):
    sweep = 320 + 220 * (t / duration)
    noise = random.Random(int(t * RATE)).uniform(-0.06, 0.06)
    return (0.16 * _sine(sweep, t) + noise) * _envelope(t, duration, 0.01, 0.08)


def _impact(t, duration):
    noise = random.Random(17).uniform(-0.7, 0.7)
    low = _sine(74, t) + 0.45 * _sine(48, t)
    return (0.42 * noise * (1.0 - t / duration) + 0.55 * low
            * (1.0 - t / duration) ** 2) * _envelope(t, duration, 0.002, 0.12)


def _success(t, duration):
    notes = (523.25, 659.25, 783.99, 1046.5)
    index = min(len(notes) - 1, int(t / (duration / len(notes))))
    local = t - index * (duration / len(notes))
    return (0.28 * _sine(notes[index], t) + 0.10 * _sine(notes[index] * 2, t)
            ) * _envelope(local, duration / len(notes), 0.01, 0.18)


def _fail(t, duration):
    frequency = 392 * (130.0 / 392.0) ** (t / duration)
    return (0.26 * _sine(frequency, t) + 0.10 * _square(frequency / 2, t)
            ) * _envelope(t, duration, 0.01, 0.20)


def _warning(t, duration):
    frequency = 720 if int(t * 4) % 2 else 520
    return 0.20 * _square(frequency, t) * _envelope(t, duration, 0.01, 0.05)


def _shield(t, duration):
    sweep = 980 - 620 * (t / duration)
    return (0.16 * _sine(sweep, t) + 0.06 * _sine(sweep * 1.7, t)
            ) * _envelope(t, duration, 0.01, 0.22)


def _engine(t, duration):
    # Seamless low rumble: all components complete whole cycles in the loop.
    cycles = 2.0
    base = _sine(55 * cycles, t)
    second = _sine(82.5 * cycles, t)
    third = _sine(27.5 * cycles, t)
    return 0.20 * base + 0.10 * second + 0.12 * third


def _ambient(t, duration):
    cycles = 4.0
    drift = 0.5 + 0.5 * _sine(0.25 * cycles, t)
    return (0.10 * _sine(55 * cycles, t)
            + 0.06 * _sine(82.5 * cycles, t) * drift
            + 0.03 * _sine(110 * cycles, t) * (1.0 - drift))


SOUND_BUILDERS = {
    "click": (_click, 0.055),
    "confirm": (_confirm, 0.20),
    "deny": (_deny, 0.24),
    "servo": (_servo, 0.32),
    "impact": (_impact, 0.40),
    "success": (_success, 0.80),
    "fail": (_fail, 0.75),
    "warning": (_warning, 0.42),
    "shield": (_shield, 0.30),
    "engine": (_engine, 2.0),
    "ambient": (_ambient, 4.0),
}

LOOPS = ("engine", "ambient")


def build_sound(name, directory=None):
    """Write one sound and return its path (also useful in tests)."""
    directory = directory or os.path.join(tempfile.gettempdir(),
                                         "interstellar_drivers_ed_audio")
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name + ".wav")
    if not os.path.exists(path):
        builder, duration = SOUND_BUILDERS[name]
        _write_wav(path, _samples(duration, builder))
    return path


class Audio:
    """Small mixer wrapper used by the screens."""

    def __init__(self, enabled=True):
        self.enabled = bool(enabled)
        self.available = False
        self._sounds = {}
        self._loop_channel = None
        self._loop_name = None
        self._directory = None
        if self.enabled:
            self._initialise()

    def _initialise(self):
        if pygame is None:
            return
        try:
            pygame.mixer.pre_init(RATE, -16, 1, 512)
            pygame.mixer.init()
            self.available = True
        except Exception:
            self.available = False

    def _sound(self, name):
        if not self.available:
            return None
        if name not in self._sounds:
            try:
                if self._directory is None:
                    self._directory = os.path.join(
                        tempfile.gettempdir(),
                        "interstellar_drivers_ed_audio")
                path = build_sound(name, self._directory)
                self._sounds[name] = pygame.mixer.Sound(path)
            except Exception:
                return None
        return self._sounds[name]

    def play(self, name, volume=0.4):
        if not self.enabled or not self.available:
            return
        sound = self._sound(name)
        if sound is None:
            return
        try:
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play()
        except Exception:
            pass

    def loop(self, name, volume=0.18):
        if not self.enabled or not self.available:
            return
        if self._loop_name == name and self._loop_channel is not None:
            return
        self.stop_loop()
        sound = self._sound(name)
        if sound is None:
            return
        try:
            channel = pygame.mixer.Channel(0)
            sound.set_volume(max(0.0, min(1.0, volume)))
            channel.play(sound, loops=-1)
            self._loop_channel = channel
            self._loop_name = name
        except Exception:
            self._loop_channel = None
            self._loop_name = None

    def stop_loop(self):
        if self._loop_channel is not None:
            try:
                self._loop_channel.stop()
            except Exception:
                pass
        self._loop_channel = None
        self._loop_name = None

    def stop_all(self):
        self.stop_loop()
        if self.available:
            try:
                pygame.mixer.stop()
            except Exception:
                pass

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        if not self.enabled:
            self.stop_all()
        elif not self.available:
            self._initialise()
