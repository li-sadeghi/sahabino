import json
import time
from typing import Any

from confluent_kafka import Producer

from common.config import KAFKA_BOOTSTRAP_SERVERS


def create_producer(retries: int = 20, delay: int = 3) -> Producer:
    last_error = None

    for _ in range(retries):
        try:
            producer = Producer(
                {
                    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
                    "client.id": "sahabino-producer",
                }
            )
            producer.list_topics(timeout=5)
            return producer
        except Exception as exc:
            last_error = exc
            time.sleep(delay)

    raise RuntimeError(f"Kafka is not ready: {last_error}")


def send_json(
    producer: Producer,
    topic: str,
    key: str,
    value: dict[str, Any],
) -> None:
    producer.produce(
        topic,
        key=key.encode("utf-8"),
        value=json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        ).encode("utf-8"),
    )
    producer.poll(0)
