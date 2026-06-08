from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from backend.config import AWS_REGION, DYNAMODB_CREATED_AT_INDEX, DYNAMODB_LATEST_SCAN_LIMIT, DYNAMODB_TABLE

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
    artifact_uris: Optional[dict] = None,
    sns_message_id: Optional[str] = None,
    prediction_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> dict:
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    item = {
        "prediction_id": prediction_id or str(uuid4()),
        "record_type": "prediction",
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
        "raw_signal_s3_uri": (artifact_uris or {}).get("raw_signal_s3_uri"),
        "report_s3_uri": (artifact_uris or {}).get("report_s3_uri"),
        "sns_message_id": sns_message_id,
    }

    get_table().put_item(Item=_to_dynamodb_value(item))
    return item


def get_latest_prediction() -> Optional[dict]:
    try:
        response = get_table().query(
            IndexName=DYNAMODB_CREATED_AT_INDEX,
            KeyConditionExpression=Key("record_type").eq("prediction"),
            ScanIndexForward=False,
            Limit=1,
        )
    except (BotoCoreError, ClientError):
        response = get_table().scan(Limit=DYNAMODB_LATEST_SCAN_LIMIT)

    items = response.get("Items", [])
    if not items:
        return None

    latest_item = max(items, key=lambda item: item["created_at"])
    return _from_dynamodb_value(latest_item)


def get_prediction_history(limit: int = 20) -> list[dict]:
    try:
        response = get_table().query(
            IndexName=DYNAMODB_CREATED_AT_INDEX,
            KeyConditionExpression=Key("record_type").eq("prediction"),
            ScanIndexForward=False,
            Limit=limit,
        )
    except (BotoCoreError, ClientError):
        response = get_table().scan(Limit=DYNAMODB_LATEST_SCAN_LIMIT)

    items = response.get("Items", [])
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return [_from_dynamodb_value(item) for item in items[:limit]]
