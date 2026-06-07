import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

import boto3


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "ecg_predictions")

_table = None


def _to_dynamodb_value(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [_to_dynamodb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dynamodb_value(item) for key, item in value.items()}
    return value


def _from_dynamodb_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, list):
        return [_from_dynamodb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _from_dynamodb_value(item) for key, item in value.items()}
    return value


def get_table():
    global _table
    if _table is None:
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        _table = dynamodb.Table(DYNAMODB_TABLE)
    return _table


def save_prediction(
    prediction: dict,
    source: str,
    sample_rate: int,
    signal_length: int,
    metadata: Optional[dict] = None,
) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    item = {
        "prediction_id": str(uuid4()),
        "created_at": created_at,
        "source": source,
        "sample_rate": sample_rate,
        "signal_length": signal_length,
        "label": prediction["label"],
        "probability": prediction["probability"],
        "threshold": prediction["threshold"],
        "bpm": prediction["bpm"],
        "model_info": prediction["model_info"],
        "metadata": metadata or {},
    }

    get_table().put_item(Item=_to_dynamodb_value(item))
    return item


def get_latest_prediction() -> Optional[dict]:
    response = get_table().scan(Limit=50)
    items = response.get("Items", [])
    if not items:
        return None

    latest_item = max(items, key=lambda item: item["created_at"])
    return _from_dynamodb_value(latest_item)


def get_prediction_history(limit: int = 20) -> list[dict]:
    response = get_table().scan(Limit=limit)
    items = response.get("Items", [])
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return [_from_dynamodb_value(item) for item in items[:limit]]
