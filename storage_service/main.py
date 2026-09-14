import json
import logging
import signal
import time

from confluent_kafka import Consumer, KafkaError

from common.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    NETWORK_TOPIC,
    REVIEWS_TOPIC,
    STATS_TOPIC,
)
from storage_service.repository import HANDLERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

running = True


def stop(*_args):
    global running
    running = False


def create_consumer() -> Consumer:
    while True:
        try:
            consumer = Consumer(
                {
                    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
                    "group.id": "sahabino-storage",
                    "auto.offset.reset": "earliest",
                    "enable.auto.commit": False,
                }
            )
            consumer.subscribe(
                [
                    STATS_TOPIC,
                    REVIEWS_TOPIC,
                    NETWORK_TOPIC,
                ]
            )
            return consumer
        except Exception:
            logger.exception("Kafka is not ready; retrying")
            time.sleep(3)


def run() -> None:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    consumer = create_consumer()

    try:
        while running:
            message = consumer.poll(1.0)

            if message is None:
                continue

            if message.error():
                if message.error().code() != KafkaError._PARTITION_EOF:
                    logger.error("Kafka error: %s", message.error())
                continue

            try:
                event = json.loads(
                    message.value().decode("utf-8")
                )
                HANDLERS[message.topic()](event)

                consumer.commit(
                    message=message,
                    asynchronous=False,
                )
            except Exception:
                logger.exception(
                    "Could not store message from %s",
                    message.topic(),
                )
    finally:
        consumer.close()


if __name__ == "__main__":
    run()
