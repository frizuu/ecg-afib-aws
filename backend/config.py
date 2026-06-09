import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "Models"
LOCAL_MODEL_PATH = MODELS_DIR / "afib_cnn_1d_best.h5"

APP_NAME = os.getenv("APP_NAME", "ecg-afib-backend")
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "ecg_predictions")
DYNAMODB_CREATED_AT_INDEX = os.getenv("DYNAMODB_CREATED_AT_INDEX", "prediction_created_at_index")
DYNAMODB_LATEST_SCAN_LIMIT = int(os.getenv("DYNAMODB_LATEST_SCAN_LIMIT", "100"))

MODEL_S3_BUCKET = os.getenv("MODEL_S3_BUCKET")
MODEL_S3_KEY = os.getenv("MODEL_S3_KEY", "models/afib_cnn_1d_best.h5")
MODEL_ALLOW_DUMMY = os.getenv("MODEL_ALLOW_DUMMY", "false").lower() in {"1", "true", "yes"}

PREDICTION_S3_BUCKET = os.getenv("PREDICTION_S3_BUCKET")
PREDICTION_S3_PREFIX = os.getenv("PREDICTION_S3_PREFIX", "ecg-predictions")

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")
SNS_ALERT_ON_LABEL = os.getenv("SNS_ALERT_ON_LABEL", "AFIB")

DEFAULT_SAMPLE_RATE = int(os.getenv("DEFAULT_SAMPLE_RATE", "250"))
DEFAULT_SIGNAL_DURATION_SEC = int(os.getenv("DEFAULT_SIGNAL_DURATION_SEC", "5"))
STREAM_BUFFER_SECONDS = int(os.getenv("STREAM_BUFFER_SECONDS", "60"))
STREAM_CHUNK_SECONDS = float(os.getenv("STREAM_CHUNK_SECONDS", "0.2"))
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
