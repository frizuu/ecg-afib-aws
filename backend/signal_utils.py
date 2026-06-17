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


def _generate_single_beat(beat_time, beat_duration, fs, heart_rate_variation=1.0):
    # Normalize time within beat (0 to 1)
    t_norm = beat_time / beat_duration
    
    # P wave: low amplitude, early in the cycle (around 0.2 to 0.3)
    p_wave_time = np.maximum(0, np.minimum(1, (t_norm - 0.15) / 0.08))
    p_wave = 0.15 * np.sin(np.pi * p_wave_time) * np.exp(-((t_norm - 0.2) ** 2) / 0.004)
    
    # QRS complex: high amplitude, sharp peaks (around 0.4 to 0.6)
    qrs_time = np.maximum(0, np.minimum(1, (t_norm - 0.35) / 0.12))
    qrs = 0.8 * heart_rate_variation * np.sin(np.pi * qrs_time) * np.exp(-((t_norm - 0.45) ** 2) / 0.003)
    # Add Q wave (negative)
    q_wave = -0.15 * np.sin(2 * np.pi * (t_norm - 0.4)) * np.exp(-((t_norm - 0.40) ** 2) / 0.0015)
    # Add S wave (negative)
    s_wave = -0.12 * np.sin(2 * np.pi * (t_norm - 0.5)) * np.exp(-((t_norm - 0.52) ** 2) / 0.0015)
    
    # T wave: medium amplitude, late in cycle (around 0.7 to 0.8)
    t_wave_time = np.maximum(0, np.minimum(1, (t_norm - 0.65) / 0.1))
    t_wave = 0.25 * np.sin(np.pi * t_wave_time) * np.exp(-((t_norm - 0.75) ** 2) / 0.008)
    
    # Baseline variation
    baseline = 0.02 * np.sin(2.0 * np.pi * 0.5 * t_norm)
    
    signal = p_wave + qrs + q_wave + s_wave + t_wave + baseline
    return signal.astype(np.float32)


def generate_dummy_ecg(duration_sec=5, fs=TARGET_FS, afib=False):
    sample_count = int(duration_sec * fs)
    
    if afib:
        # AFIB: irregular heart rate (60-120 bpm with random variations)
        # Generate beat times with variable intervals
        beat_times = []
        current_time = 0
        while current_time < duration_sec:
            # Random RR interval between 0.4 to 1.0 seconds (60-150 bpm range)
            rr_interval = np.random.uniform(0.4, 1.0)
            beat_times.append(current_time)
            current_time += rr_interval
        
        signal = np.zeros(sample_count, dtype=np.float32)
        
        # Generate each beat
        for i, beat_start in enumerate(beat_times):
            if i + 1 < len(beat_times):
                beat_duration = beat_times[i + 1] - beat_start
            else:
                beat_duration = 0.8  # Default for last beat
            
            # Find samples for this beat
            beat_start_sample = int(beat_start * fs)
            beat_end_sample = int((beat_start + beat_duration) * fs)
            beat_end_sample = min(beat_end_sample, sample_count)
            
            if beat_start_sample < sample_count:
                beat_samples = beat_end_sample - beat_start_sample
                beat_t = np.linspace(0, beat_duration, beat_samples, endpoint=False)
                
                # Vary morphology for AFIB
                morphology_var = np.random.uniform(0.8, 1.2)
                beat_signal = _generate_single_beat(beat_t, beat_duration, fs, morphology_var)
                signal[beat_start_sample:beat_end_sample] = beat_signal
        
        # Add AFIB-specific noise and fibrillation
        t = np.linspace(0, duration_sec, sample_count, endpoint=False)
        fibrillation = 0.15 * np.sin(2.0 * np.pi * 5.5 * t + np.random.uniform(0, 2*np.pi)) * (0.5 + 0.5 * np.sin(2.0 * np.pi * 0.3 * t))
        noise = np.random.normal(0.0, 0.04, sample_count)
        
        signal = signal + fibrillation + noise
        label = "AFIB"
        probability = 0.85
        
    else:
        # Normal: regular heart rate
        heart_rate = 70 + np.random.uniform(-5, 5)  # 65-75 bpm
        beat_duration = 60.0 / heart_rate
        
        signal = np.zeros(sample_count, dtype=np.float32)
        
        # Generate beats at regular intervals
        beat_count = int(duration_sec / beat_duration) + 1
        for i in range(beat_count):
            beat_start = i * beat_duration
            if beat_start >= duration_sec:
                break
            
            beat_start_sample = int(beat_start * fs)
            beat_end_sample = int((beat_start + beat_duration) * fs)
            beat_end_sample = min(beat_end_sample, sample_count)
            
            if beat_start_sample < sample_count:
                beat_samples = beat_end_sample - beat_start_sample
                beat_t = np.linspace(0, beat_duration, beat_samples, endpoint=False)
                beat_signal = _generate_single_beat(beat_t, beat_duration, fs, 1.0)
                signal[beat_start_sample:beat_end_sample] = beat_signal
        
        # Add normal ECG noise
        t = np.linspace(0, duration_sec, sample_count, endpoint=False)
        noise = np.random.normal(0.0, 0.025, sample_count)
        
        signal = signal + noise
        label = "Normal"
        probability = 0.15
    
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
        self._beat_index = 0  # Track which beat we're on
        self._next_beat_time = 0.8  # Time of next beat (updated dynamically)

    def start(self, afib: bool = False, sample_rate: int = DEFAULT_SAMPLE_RATE) -> dict:
        with self._lock:
            if self._is_running_locked():
                return self._status_locked()

            self._sample_rate = sample_rate
            self._buffer = deque(maxlen=sample_rate * STREAM_BUFFER_SECONDS)
            self._sample_index = 0
            self._afib = afib
            self._beat_index = 0
            # Initialize first beat duration (0.8s for ~75 bpm normal, variable for AFIB)
            if afib:
                self._next_beat_time = np.random.uniform(0.4, 1.0)
            else:
                self._next_beat_time = 0.8
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
        """
        Generate realistic ECG chunk with structured P-QRS-T beats.
        """
        signal = np.zeros(chunk_size, dtype=np.float32)
        current_sample = 0
        
        while current_sample < chunk_size:
            # Current time in seconds
            current_time = self._sample_index / self._sample_rate
            beat_start_time = current_time - (current_time % self._next_beat_time) if self._beat_index == 0 else current_time
            
            # Time within current beat (0 to beat_duration)
            time_in_beat = current_time - (self._beat_index * self._next_beat_time + sum([0] if self._beat_index == 0 else [0]))
            
            # For simplicity: calculate beat start for current chunk
            samples_in_beat = max(1, int(self._next_beat_time * self._sample_rate))
            beat_sample_index = int((current_time % self._next_beat_time) * self._sample_rate)
            
            # Generate samples for this beat until end of beat or chunk
            samples_to_generate = min(samples_in_beat - beat_sample_index, chunk_size - current_sample)
            
            if samples_to_generate > 0:
                # Time array for these samples
                idx = np.arange(self._sample_index, self._sample_index + samples_to_generate)
                time_array = idx / self._sample_rate
                
                # Get time within the beat cycle (0 to 1)
                beat_time = (time_array % self._next_beat_time)
                
                # Morphology variation for AFIB
                morphology_var = 1.0
                if self._afib:
                    morphology_var = np.random.uniform(0.7, 1.3)
                
                # Generate P wave
                p_wave_phase = (beat_time - 0.15) / 0.08
                p_wave = 0.15 * np.sin(np.pi * np.clip(p_wave_phase, 0, 1)) * np.exp(-((beat_time - 0.2) ** 2) / 0.004)
                
                # Generate QRS complex
                qrs_phase = (beat_time - 0.35) / 0.12
                qrs = 0.8 * morphology_var * np.sin(np.pi * np.clip(qrs_phase, 0, 1)) * np.exp(-((beat_time - 0.45) ** 2) / 0.003)
                
                # Q wave
                q_wave = -0.15 * np.sin(2 * np.pi * (beat_time - 0.4)) * np.exp(-((beat_time - 0.40) ** 2) / 0.0015)
                
                # S wave
                s_wave = -0.12 * np.sin(2 * np.pi * (beat_time - 0.5)) * np.exp(-((beat_time - 0.52) ** 2) / 0.0015)
                
                # Generate T wave
                t_wave_phase = (beat_time - 0.65) / 0.1
                t_wave = 0.25 * np.sin(np.pi * np.clip(t_wave_phase, 0, 1)) * np.exp(-((beat_time - 0.75) ** 2) / 0.008)
                
                # Baseline variation
                baseline = 0.02 * np.sin(2.0 * np.pi * 0.5 * beat_time)
                
                # Add AFIB fibrillation if needed
                if self._afib:
                    fibrillation = 0.15 * np.sin(2.0 * np.pi * 5.5 * time_array + np.random.uniform(0, 2*np.pi)) * (0.5 + 0.5 * np.sin(2.0 * np.pi * 0.3 * time_array))
                    noise = np.random.normal(0.0, 0.04, samples_to_generate)
                else:
                    fibrillation = 0
                    noise = np.random.normal(0.0, 0.025, samples_to_generate)
                
                # Combine all components
                beat_signal = p_wave + qrs + q_wave + s_wave + t_wave + baseline + fibrillation + noise
                signal[current_sample:current_sample + samples_to_generate] = beat_signal.astype(np.float32)
                
                self._sample_index += samples_to_generate
                current_sample += samples_to_generate
                
                # Check if beat is complete, prepare next beat
                if beat_sample_index + samples_to_generate >= samples_in_beat:
                    self._beat_index += 1
                    if self._afib:
                        # Random RR interval for AFIB
                        self._next_beat_time = np.random.uniform(0.4, 1.0)
                    else:
                        # Regular interval for normal sinus
                        self._next_beat_time = 0.8
            else:
                break
        
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
