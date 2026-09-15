import os
import tempfile
from datetime import datetime, timezone
from typing import Literal

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from common.config import NETWORK_TOPIC
from common.kafka import create_producer, send_json
from network_service.analyzer import analyze_pcap

app = FastAPI(
    title="Sahabino Network Analyzer",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", status_code=202)
async def analyze(
    application_id: int = Form(gt=0),
    scenario: Literal["upload", "download"] = Form(),
    pcap_file: UploadFile = File(),
):
    file_name = pcap_file.filename or "capture.pcap"

    if not file_name.lower().endswith((".pcap", ".pcapng")):
        raise HTTPException(
            status_code=400,
            detail="Only pcap or pcapng files are allowed",
        )

    temp_path = ""

    try:
        suffix = os.path.splitext(file_name)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp:
            temp_path = temp.name

            while chunk := await pcap_file.read(1024 * 1024):
                temp.write(chunk)

        metrics = analyze_pcap(temp_path)

        event = {
            "application_id": application_id,
            "scenario": scenario,
            "file_name": file_name,
            **metrics,
            "analyzed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        producer = create_producer()

        send_json(
            producer,
            NETWORK_TOPIC,
            f"{application_id}:{scenario}:{file_name}",
            event,
        )

        remaining = producer.flush(30)

        if remaining:
            raise RuntimeError("Kafka delivery timed out")

        return {
            "message": "File analyzed and queued",
            "metrics": metrics,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Could not analyze file: {exc}",
        ) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
