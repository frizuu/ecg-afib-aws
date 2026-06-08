import numpy as np
from math import gcd
from scipy.signal import butter, filtfilt, resample_poly, find_peaks

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
