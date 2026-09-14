from storage_service.repository import HANDLERS


def test_all_kafka_topics_have_a_handler():
    assert set(HANDLERS) == {
        "playstore-stats",
        "playstore-reviews",
        "network-metrics",
    }


def test_review_query_uses_upsert():
    import inspect

    from storage_service.repository import save_review

    source = inspect.getsource(save_review)

    assert (
        "ON CONFLICT (application_id, review_id) DO UPDATE"
        in source
    )
