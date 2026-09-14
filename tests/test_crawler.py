from datetime import datetime, timezone

from crawler_service import playstore
from crawler_service.playstore import retry, to_utc


def test_retry_returns_after_temporary_failures():
    calls = {"count": 0}

    def sometimes_fails():
        calls["count"] += 1

        if calls["count"] < 3:
            raise RuntimeError("temporary")

        return "ok"

    assert retry(
        sometimes_fails,
        attempts=3,
        base_delay=0,
    ) == "ok"
    assert calls["count"] == 3


def test_to_utc_converts_datetime():
    value = datetime(
        2026,
        1,
        2,
        3,
        4,
        tzinfo=timezone.utc,
    )

    assert to_utc(value) == "2026-01-02T03:04:00+00:00"


def test_to_utc_accepts_unix_timestamp():
    assert to_utc(0) == "1970-01-01T00:00:00+00:00"


def test_fetch_stats_keeps_required_fields(monkeypatch):
    monkeypatch.setattr(
        playstore,
        "playstore_app",
        lambda *args, **kwargs: {
            "minInstalls": 100,
            "score": 4.2,
            "ratings": 20,
            "reviews": 10,
            "updated": 0,
            "version": "1.2.3",
            "adSupported": True,
        },
    )

    result = playstore.fetch_stats("com.example.test")

    assert result == {
        "min_installs": 100,
        "score": 4.2,
        "ratings": 20,
        "reviews": 10,
        "updated": "1970-01-01T00:00:00+00:00",
        "version": "1.2.3",
        "ad_supported": True,
    }


def test_fetch_reviews_maps_review_id(monkeypatch):
    def fake_reviews(*args, **kwargs):
        assert kwargs["count"] == 1000

        return (
            [
                {
                    "reviewId": "review-1",
                    "at": datetime(
                        2026,
                        1,
                        1,
                        tzinfo=timezone.utc,
                    ),
                    "userName": "Ali",
                    "thumbsUpCount": 4,
                    "score": 5,
                    "content": "Good",
                }
            ],
            None,
        )

    monkeypatch.setattr(playstore, "reviews", fake_reviews)

    result = playstore.fetch_reviews(
        "com.example.test",
        count=1000,
    )

    assert result[0]["review_id"] == "review-1"
    assert result[0]["thumbs_up_count"] == 4
