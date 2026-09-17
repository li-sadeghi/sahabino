import logging
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import BackgroundTasks, FastAPI

from common.config import (
    APP_SERVICE_URL,
    CRAWL_INTERVAL_SECONDS,
    REVIEWS_TOPIC,
    STATS_TOPIC,
)
from common.kafka import create_producer, send_json
from crawler_service.playstore import fetch_reviews, fetch_stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

crawl_lock = threading.Lock()


def crawl_once() -> None:
    if not crawl_lock.acquire(blocking=False):
        logger.info("A crawl is already running")
        return

    producer = None

    try:
        producer = create_producer()

        response = httpx.get(
            f"{APP_SERVICE_URL}/applications",
            params={"active_only": "true"},
            timeout=30,
        )
        response.raise_for_status()
        applications = response.json()

        for application in applications:
            crawled_at = datetime.now(timezone.utc).isoformat()

            try:
                stats = fetch_stats(application["package_name"])

                send_json(
                    producer,
                    STATS_TOPIC,
                    str(application["id"]),
                    {
                        "application_id": application["id"],
                        "package_name": application["package_name"],
                        "crawled_at": crawled_at,
                        "data": stats,
                    },
                )

                reviews = fetch_reviews(
                    application["package_name"],
                    count=1000,
                )

                for review in reviews:
                    send_json(
                        producer,
                        REVIEWS_TOPIC,
                        f"{application['id']}:{review['review_id']}",
                        {
                            "application_id": application["id"],
                            "package_name": application["package_name"],
                            "crawled_at": crawled_at,
                            "data": review,
                        },
                    )

                producer.flush(30)
                logger.info("Crawled %s", application["name"])
                time.sleep(1)

            except Exception:
                logger.exception(
                    "Could not crawl %s",
                    application["name"],
                )
    finally:
        if producer is not None:
            producer.flush(10)

        crawl_lock.release()


def scheduler_loop(stop_event: threading.Event) -> None:
    next_run_at = time.monotonic()

    while not stop_event.is_set():
        wait_seconds = max(
            0,
            next_run_at - time.monotonic(),
        )

        if stop_event.wait(wait_seconds):
            break

        logger.info("Starting scheduled crawl")

        crawl_once()

        next_run_at += CRAWL_INTERVAL_SECONDS
        now = time.monotonic()

        if next_run_at <= now:
            logger.warning(
                "Crawl exceeded the configured interval; "
                "scheduling the next crawl one interval from now"
            )
            next_run_at = now + CRAWL_INTERVAL_SECONDS

        logger.info(
            "Next scheduled crawl in %.1f seconds",
            next_run_at - now,
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop_event = threading.Event()

    thread = threading.Thread(
        target=scheduler_loop,
        args=(stop_event,),
        daemon=True,
    )
    thread.start()

    yield

    stop_event.set()
    thread.join(timeout=5)


app = FastAPI(
    title="Sahabino Crawler Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "crawl_running": crawl_lock.locked(),
    }


@app.post("/crawl", status_code=202)
def start_crawl(background_tasks: BackgroundTasks):
    background_tasks.add_task(crawl_once)
    return {"message": "Crawl started"}
