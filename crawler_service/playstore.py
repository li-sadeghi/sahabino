import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from google_play_scraper import Sort, reviews
from google_play_scraper import app as playstore_app

from common.config import PLAYSTORE_COUNTRY, PLAYSTORE_LANGUAGE


def retry(
    call: Callable[[], Any],
    attempts: int = 3,
    base_delay: float = 2,
) -> Any:
    last_error = None

    for attempt in range(attempts):
        try:
            return call()
        except Exception as exc:
            last_error = exc

            if attempt < attempts - 1:
                time.sleep(base_delay * (2**attempt))

    raise last_error


def to_utc(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
    else:
        return str(value)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc).isoformat()


def fetch_stats(package_name: str) -> dict[str, Any]:
    raw = retry(
        lambda: playstore_app(
            package_name,
            lang=PLAYSTORE_LANGUAGE,
            country=PLAYSTORE_COUNTRY,
        )
    )

    return {
        "min_installs": raw.get("minInstalls"),
        "score": raw.get("score"),
        "ratings": raw.get("ratings"),
        "reviews": raw.get("reviews"),
        "updated": to_utc(raw.get("updated")),
        "version": raw.get("version"),
        "ad_supported": raw.get("adSupported"),
    }


def fetch_reviews(
    package_name: str,
    count: int = 1000,
) -> list[dict[str, Any]]:
    raw, _ = retry(
        lambda: reviews(
            package_name,
            lang=PLAYSTORE_LANGUAGE,
            country=PLAYSTORE_COUNTRY,
            sort=Sort.NEWEST,
            count=count,
        )
    )

    return [
        {
            "review_id": item["reviewId"],
            "at": to_utc(item.get("at")),
            "user_name": item.get("userName"),
            "thumbs_up_count": item.get("thumbsUpCount", 0),
            "score": item.get("score"),
            "content": item.get("content"),
        }
        for item in raw
    ]
