from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.model import MODEL_INFO, get_model, predict_signal
from backend.signal import generate_dummy_ecg

app = FastAPI(
    title="ECG AFIB Detection Backend",
    description="Backend service untuk demo deteksi aritmia dengan data dummy dan model CNN 1D.",
    version=MODEL_INFO["version"],
)

last_prediction: Optional[dict] = None


class PredictRequest(BaseModel):
    signal: List[float]
    sample_rate: Optional[int] = 250
    threshold: Optional[float] = 0.5


@app.on_event("startup")
async def startup_event():
    get_model()


@app.get("/generate")
async def generate():
    sample, metadata = generate_dummy_ecg(duration_sec=5, fs=250)
    return {
        "signal": sample.tolist(),
        "metadata": metadata,
        "model_info": MODEL_INFO,
    }


@app.post("/predict")
async def predict(request: PredictRequest):
    if len(request.signal) < 100:
        raise HTTPException(status_code=400, detail="Signal harus memiliki setidaknya 100 sampel")

    result = predict_signal(request.signal, request.sample_rate, threshold=request.threshold)
    global last_prediction
    last_prediction = result
    return result


@app.get("/latest")
async def latest():
    return {
        "model_info": MODEL_INFO,
        "last_prediction": last_prediction,
    }
