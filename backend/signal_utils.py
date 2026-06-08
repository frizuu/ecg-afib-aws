import threading
import time
from collections import deque
from datetime import datetime, timezone
from math import gcd
from typing import Optional

import numpy as np
from scipy.signal import butter, filtfilt, resample_poly, find_peaks

from backend.config import DEFAULT_SAMPLE_RATE, STREAM_BUFFER_SECONDS, STREAM_CHUNK_SECONDS

TARGET_FS = 250
SEG_LEN = 1250
BANDPASS = (0.5, 40.0)


def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, [lowcut / nyq, highcut / nyq], btype="band")
    return b, a


def apply_preprocess(signal, sample_rate):
    x = np.asarray(signal, dtype=np.float32).flatten()
    if sample_rate != TARGET_FS:
        g = gcd(int(sample_rate), TARGET_FS)
        up = TARGET_FS // g
        down = int(sample_rate) // g
        x = resample_poly(x, up, down)

    if len(x) < 10:
        raise ValueError("Signal terlalu pendek untuk preprocessing")

    b, a = butter_bandpass(BANDPASS[0], BANDPASS[1], TARGET_FS, order=4)
    x = filtfilt(b, a, x)
    return x


def zscore(x):
    x = np.asarray(x, dtype=np.float32)
    mu = x.mean()
    sigma = x.std() + 1e-8
    return (x - mu) / sigma


def prepare_window(signal, sample_rate):
    x = apply_preprocess(signal, sample_rate)
    if len(x) < SEG_LEN:
        padding = SEG_LEN - len(x)
        x = np.pad(x, (padding, 0), mode="reflect")
    window = x[-SEG_LEN:]
    return zscore(window).reshape(1, SEG_LEN, 1)


def calculate_bpm(signal, fs):
    x = np.asarray(signal, dtype=np.float32)
    if len(x) < fs * 3:
        return None
    x = x - np.mean(x)
    if np.max(np.abs(x)) < 1e-6:
        return None
    x = x / np.max(np.abs(x))
    peaks, _ = find_peaks(x, height=0.3, distance=fs * 0.4)
    duration = len(x) / fs
    if duration <= 0 or len(peaks) < 1:
        return None
    return float((len(peaks) / duration) * 60.0)


def generate_dummy_ecg(duration_sec=5, fs=TARGET_FS, afib=False):
    sample_count = int(duration_sec * fs)
    t = np.linspace(0.0, duration_sec, sample_count, endpoint=False)
    heart_rate = 70 + np.random.uniform(-2, 2)
    base = 0.8 * np.sin(2.0 * np.pi * (heart_rate / 60.0) * t)
    morphology = 0.1 * np.sin(2.0 * np.pi * 15.0 * t)
    noise = np.random.normal(0.0, 0.08, sample_count)

    if afib:
        jitter = np.sin(2.0 * np.pi * 1.5 * t) * 0.4
        signal = base + morphology + noise + jitter
        label = "AFIB"
    else:
        signal = base + morphology + noise
        label = "Normal"

    probability = 0.8 if afib else 0.2
    metadata = {
        "duration_sec": duration_sec,
        "sample_rate": fs,
        "label": label,
        "pseudo_probability": probability,
    }
    return signal.astype(np.float32), metadata


class EcgSignalStream:
    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._sample_rate = DEFAULT_SAMPLE_RATE
        self._buffer = deque(maxlen=DEFAULT_SAMPLE_RATE * STREAM_BUFFER_SECONDS)
        self._sample_index = 0
        self._afib = False
        self._started_at: Optional[str] = None

    def start(self, afib: bool = False, sample_rate: int = DEFAULT_SAMPLE_RATE) -> dict:
        with self._lock:
            if self._is_running_locked():
                return self._status_locked()

            self._sample_rate = sample_rate
            self._buffer = deque(maxlen=sample_rate * STREAM_BUFFER_SECONDS)
            self._sample_index = 0
            self._afib = afib
            self._started_at = datetime.now(timezone.utc).isoformat()
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            return self._status_locked()

    def stop(self) -> dict:
        with self._lock:
            thread = self._thread
            self._stop_event.set()

        if thread and thread.is_alive():
            thread.join(timeout=2.0)

        with self._lock:
            self._thread = None
            return self._status_locked()

    def status(self) -> dict:
        with self._lock:
            return self._status_locked()

    def latest(self, seconds: int = 5) -> dict:
        with self._lock:
            sample_count = max(1, int(seconds * self._sample_rate))
            signal = list(self._buffer)[-sample_count:]
            return {
                "running": self._is_running_locked(),
                "signal": signal,
                "metadata": {
                    "source": "stream",
                    "sample_rate": self._sample_rate,
                    "requested_seconds": seconds,
                    "available_samples": len(signal),
                    "buffer_seconds": STREAM_BUFFER_SECONDS,
                    "afib": self._afib,
                    "label": "AFIB" if self._afib else "Normal",
                    "started_at": self._started_at,
                },
            }

    def _run(self):
        chunk_size = max(1, int(self._sample_rate * STREAM_CHUNK_SECONDS))
        next_tick = time.monotonic()

        while not self._stop_event.is_set():
            chunk = self._make_chunk(chunk_size)
            with self._lock:
                self._buffer.extend(chunk.tolist())

            next_tick += STREAM_CHUNK_SECONDS
            time.sleep(max(0.0, next_tick - time.monotonic()))

    def _make_chunk(self, chunk_size: int) -> np.ndarray:
        idx = np.arange(self._sample_index, self._sample_index + chunk_size)
        t = idx / self._sample_rate
        self._sample_index += chunk_size

        heart_rate = 72.0
        if self._afib:
            heart_rate += 14.0 * np.sin(2.0 * np.pi * 0.17 * t)

        base = 0.75 * np.sin(2.0 * np.pi * (heart_rate / 60.0) * t)
        qrs = 0.18 * np.sin(2.0 * np.pi * 17.0 * t)
        baseline = 0.04 * np.sin(2.0 * np.pi * 0.33 * t)
        noise = np.random.normal(0.0, 0.035, chunk_size)

        if self._afib:
            fibrillation = 0.22 * np.sin(2.0 * np.pi * 6.0 * t + 0.7 * np.sin(2.0 * np.pi * 0.5 * t))
            signal = base + qrs + baseline + fibrillation + noise
        else:
            signal = base + qrs + baseline + noise

        return signal.astype(np.float32)

    def _is_running_locked(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def _status_locked(self) -> dict:
        return {
            "running": self._is_running_locked(),
            "sample_rate": self._sample_rate,
            "buffered_samples": len(self._buffer),
            "buffer_seconds": STREAM_BUFFER_SECONDS,
            "afib": self._afib,
            "started_at": self._started_at,
        }


ecg_stream = EcgSignalStream()
