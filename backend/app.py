import logging
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.aws_services import AwsIntegrationError, publish_afib_alert, upload_prediction_artifacts
from backend.config import DEFAULT_SAMPLE_RATE, DEFAULT_SIGNAL_DURATION_SEC
from backend.database import get_latest_prediction, get_prediction_history, save_prediction
from backend.model import MODEL_INFO, ModelLoadError, get_model, predict_signal
from backend.signal_utils import ecg_stream, generate_dummy_ecg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ECG AFIB Detection Backend",
    description="Backend AWS untuk deteksi aritmia ECG dengan FastAPI, EC2, S3, DynamoDB, SNS, dan CloudWatch.",
    version=MODEL_INFO["version"],
)

last_prediction: Optional[dict] = None


class PredictRequest(BaseModel):
    signal: List[float]
    sample_rate: Optional[int] = DEFAULT_SAMPLE_RATE
    threshold: Optional[float] = 0.5
    metadata: Optional[dict] = None


def persist_prediction(
    result: dict,
    signal: list[float],
    source: str,
    sample_rate: int,
    metadata: Optional[dict] = None,
) -> dict:
    prediction_id = str(uuid4())
    artifact_uris = upload_prediction_artifacts(
        prediction_id,
        signal,
        result,
        metadata=metadata,
    )
    saved_item = save_prediction(
        result,
        source=source,
        sample_rate=sample_rate,
        signal_length=len(signal),
        metadata=metadata,
        artifact_uris=artifact_uris,
        prediction_id=prediction_id,
    )
    sns_message_id = publish_afib_alert(saved_item)
    if sns_message_id:
        saved_item = save_prediction(
            result,
            source=source,
            sample_rate=sample_rate,
            signal_length=len(signal),
            metadata=metadata,
            artifact_uris=artifact_uris,
            sns_message_id=sns_message_id,
            prediction_id=saved_item["prediction_id"],
            created_at=saved_item["created_at"],
        )
    return saved_item


@app.on_event("startup")
async def startup_event():
    get_model()
    logger.info("ECG AFIB backend started")


@app.get("/generate")
async def generate(afib: bool = False):
    sample, metadata = generate_dummy_ecg(
        duration_sec=DEFAULT_SIGNAL_DURATION_SEC,
        fs=DEFAULT_SAMPLE_RATE,
        afib=afib,
    )
    return {
        "signal": sample.tolist(),
        "metadata": metadata,
        "model_info": MODEL_INFO,
    }


@app.post("/stream/start")
async def stream_start(afib: bool = False):
    return ecg_stream.start(afib=afib, sample_rate=DEFAULT_SAMPLE_RATE)


@app.post("/stream/stop")
async def stream_stop():
    return ecg_stream.stop()


@app.get("/stream/status")
async def stream_status():
    return ecg_stream.status()


@app.get("/stream/latest")
async def stream_latest(seconds: int = DEFAULT_SIGNAL_DURATION_SEC):
    if seconds < 1 or seconds > 60:
        raise HTTPException(status_code=400, detail="Seconds harus antara 1 sampai 60")
    return ecg_stream.latest(seconds=seconds)


@app.post("/predict")
async def predict(request: PredictRequest):
    if len(request.signal) < 100:
        raise HTTPException(status_code=400, detail="Signal harus memiliki setidaknya 100 sampel")

    try:
        result = predict_signal(request.signal, request.sample_rate, threshold=request.threshold)
        saved_item = persist_prediction(
            result,
            source="request",
            sample_rate=request.sample_rate,
            signal=request.signal,
            metadata=request.metadata,
        )
    except ModelLoadError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AwsIntegrationError as exc:
        logger.exception("AWS integration failed during prediction")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    global last_prediction
    last_prediction = saved_item
    logger.info("Prediction completed", extra={"prediction_id": saved_item["prediction_id"], "label": saved_item["label"]})
    return saved_item


@app.post("/predict-dummy")
async def predict_dummy(afib: bool = False):
    try:
        sample, metadata = generate_dummy_ecg(
            duration_sec=DEFAULT_SIGNAL_DURATION_SEC,
            fs=DEFAULT_SAMPLE_RATE,
            afib=afib,
        )
        result = predict_signal(sample, metadata["sample_rate"])
        signal = sample.tolist()
        saved_item = persist_prediction(
            result,
            source="dummy",
            sample_rate=metadata["sample_rate"],
            signal=signal,
            metadata=metadata,
        )
    except ModelLoadError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AwsIntegrationError as exc:
        logger.exception("AWS integration failed during dummy prediction")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    global last_prediction
    last_prediction = saved_item
    logger.info("Dummy prediction completed", extra={"prediction_id": saved_item["prediction_id"], "label": saved_item["label"]})
    return saved_item


@app.post("/predict-stream")
async def predict_stream(seconds: int = DEFAULT_SIGNAL_DURATION_SEC, threshold: float = 0.5):
    if seconds < 1 or seconds > 60:
        raise HTTPException(status_code=400, detail="Seconds harus antara 1 sampai 60")

    stream_data = ecg_stream.latest(seconds=seconds)
    signal = stream_data["signal"]
    metadata = stream_data["metadata"]

    if len(signal) < 100:
        raise HTTPException(status_code=400, detail="Stream belum memiliki minimal 100 sampel")

    try:
        result = predict_signal(signal, metadata["sample_rate"], threshold=threshold)
        saved_item = persist_prediction(
            result,
            source="stream",
            sample_rate=metadata["sample_rate"],
            signal=signal,
            metadata=metadata,
        )
    except ModelLoadError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AwsIntegrationError as exc:
        logger.exception("AWS integration failed during stream prediction")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    global last_prediction
    last_prediction = saved_item
    logger.info("Stream prediction completed", extra={"prediction_id": saved_item["prediction_id"], "label": saved_item["label"]})
    return saved_item


@app.get("/latest")
async def latest():
    return {
        "model_info": MODEL_INFO,
        "last_prediction": get_latest_prediction() or last_prediction,
    }


@app.get("/history")
async def history(limit: int = 20):
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit harus antara 1 sampai 100")

    return {
        "model_info": MODEL_INFO,
        "items": get_prediction_history(limit=limit),
    }
