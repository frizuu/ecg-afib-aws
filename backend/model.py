import logging
import numpy as np
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam

from backend.config import (
    AWS_REGION,
    LOCAL_MODEL_PATH,
    MODEL_ALLOW_DUMMY,
    MODEL_S3_BUCKET,
    MODEL_S3_KEY,
)
from backend.signal_utils import prepare_window, calculate_bpm

SEG_LEN = 1250
MODEL_INFO = {
    "name": "ecg-afib-cnn1d-backend",
    "version": "0.1.0",
    "input_length": SEG_LEN,
    "sample_rate": 250,
    "labels": {"0": "NORMAL", "1": "AFIB"},
}

_model = None
logger = logging.getLogger(__name__)


class ModelLoadError(RuntimeError):
    pass


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

    if MODEL_S3_BUCKET:
        LOCAL_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            boto3.client("s3", region_name=AWS_REGION).download_file(
                MODEL_S3_BUCKET,
                MODEL_S3_KEY,
                str(LOCAL_MODEL_PATH),
            )
            logger.info("Downloaded model from S3", extra={"bucket": MODEL_S3_BUCKET, "key": MODEL_S3_KEY})
        except (BotoCoreError, ClientError) as exc:
            raise ModelLoadError(f"Gagal download model dari s3://{MODEL_S3_BUCKET}/{MODEL_S3_KEY}: {exc}") from exc

    if LOCAL_MODEL_PATH.exists():
        _model = load_model(LOCAL_MODEL_PATH)
        logger.info("Loaded ECG model", extra={"path": str(LOCAL_MODEL_PATH)})
    elif MODEL_ALLOW_DUMMY:
        _model = build_dummy_model()
        logger.warning("Using dummy untrained ECG model because MODEL_ALLOW_DUMMY=true")
    else:
        raise ModelLoadError(
            "Model H5 tidak ditemukan. Set MODEL_S3_BUCKET dan MODEL_S3_KEY, "
            "atau aktifkan MODEL_ALLOW_DUMMY=true hanya untuk demo."
        )
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
