import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from backend.config import (
    APP_NAME,
    AWS_REGION,
    PREDICTION_S3_BUCKET,
    PREDICTION_S3_PREFIX,
    SNS_ALERT_ON_LABEL,
    SNS_TOPIC_ARN,
)


logger = logging.getLogger(__name__)

_s3_client = None
_sns_client = None


class AwsIntegrationError(RuntimeError):
    pass


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", region_name=AWS_REGION)
    return _s3_client


def get_sns_client():
    global _sns_client
    if _sns_client is None:
        _sns_client = boto3.client("sns", region_name=AWS_REGION)
    return _sns_client


def json_default(value: Any):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def upload_prediction_artifacts(
    prediction_id: str,
    signal: list[float],
    prediction: dict,
    metadata: Optional[dict] = None,
) -> dict:
    if not PREDICTION_S3_BUCKET:
        return {}

    created_date = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    base_key = f"{PREDICTION_S3_PREFIX}/{created_date}/{prediction_id}"
    raw_key = f"{base_key}/raw_signal.json"
    report_key = f"{base_key}/prediction_report.json"

    raw_body = {
        "prediction_id": prediction_id,
        "signal": signal,
        "metadata": metadata or {},
    }
    report_body = {
        "prediction_id": prediction_id,
        "prediction": prediction,
        "metadata": metadata or {},
    }

    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=PREDICTION_S3_BUCKET,
            Key=raw_key,
            Body=json.dumps(raw_body, default=json_default).encode("utf-8"),
            ContentType="application/json",
        )
        s3.put_object(
            Bucket=PREDICTION_S3_BUCKET,
            Key=report_key,
            Body=json.dumps(report_body, default=json_default).encode("utf-8"),
            ContentType="application/json",
        )
    except (BotoCoreError, ClientError) as exc:
        raise AwsIntegrationError(f"Gagal menyimpan artefak prediksi ke S3: {exc}") from exc

    return {
        "raw_signal_s3_uri": f"s3://{PREDICTION_S3_BUCKET}/{raw_key}",
        "report_s3_uri": f"s3://{PREDICTION_S3_BUCKET}/{report_key}",
    }


def publish_afib_alert(saved_item: dict) -> Optional[str]:
    if not SNS_TOPIC_ARN:
        return None
    if saved_item.get("label") != SNS_ALERT_ON_LABEL:
        return None

    message = {
        "app": APP_NAME,
        "event": "AFIB_DETECTED",
        "prediction_id": saved_item.get("prediction_id"),
        "created_at": saved_item.get("created_at"),
        "probability": saved_item.get("probability"),
        "bpm": saved_item.get("bpm"),
        "source": saved_item.get("source"),
        "raw_signal_s3_uri": saved_item.get("raw_signal_s3_uri"),
        "report_s3_uri": saved_item.get("report_s3_uri"),
    }

    try:
        response = get_sns_client().publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="AFIB detected by ECG backend",
            Message=json.dumps(message, default=json_default),
        )
    except (BotoCoreError, ClientError) as exc:
        raise AwsIntegrationError(f"Gagal publish alert AFIB ke SNS: {exc}") from exc

    message_id = response.get("MessageId")
    logger.info("Published AFIB SNS alert", extra={"prediction_id": saved_item.get("prediction_id")})
    return message_id
