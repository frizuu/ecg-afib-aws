import os
from pathlib import Path
import numpy as np
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam

from backend.signal import prepare_window, calculate_bpm

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "Models"
H5_MODEL_PATH = MODELS_DIR / "afib_cnn_1d_best.h5"
SEG_LEN = 1250
MODEL_INFO = {
    "name": "ecg-afib-cnn1d-backend",
    "version": "0.1.0",
    "input_length": SEG_LEN,
    "sample_rate": 250,
    "labels": {"0": "Normal", "1": "AFIB"},
}

_model = None


def build_dummy_model():
    model = Sequential([
        Conv1D(16, 7, activation="relu", input_shape=(SEG_LEN, 1)),
        BatchNormalization(),
        MaxPooling1D(2),
        Conv1D(32, 5, activation="relu"),
        BatchNormalization(),
        MaxPooling1D(2),
        Conv1D(64, 3, activation="relu"),
        BatchNormalization(),
        MaxPooling1D(2),
        Flatten(),
        Dense(64, activation="relu"),
        Dropout(0.3),
        Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer=Adam(1e-3), loss="binary_crossentropy", metrics=["accuracy"])
    return model


def get_model():
    global _model
    if _model is not None:
        return _model

    if H5_MODEL_PATH.exists():
        _model = load_model(H5_MODEL_PATH)
    else:
        _model = build_dummy_model()
    return _model


def predict_signal(signal, sample_rate, threshold=0.5):
    model = get_model()
    window = prepare_window(signal, sample_rate)
    raw_signal = np.asarray(signal, dtype=np.float32)
    prob = float(model.predict(window, verbose=0)[0, 0])
    label = "AFIB" if prob >= threshold else "Normal"

    bpm = calculate_bpm(raw_signal, sample_rate)
    return {
        "label": label,
        "probability": prob,
        "threshold": threshold,
        "bpm": bpm,
        "model_info": MODEL_INFO,
    }
