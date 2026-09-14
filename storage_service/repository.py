from typing import Any

from common.db import connection


def save_stats(event: dict[str, Any]) -> None:
    data = event["data"]

    query = """
        INSERT INTO app_stats(
            application_id,
            min_installs,
            score,
            ratings,
            reviews,
            playstore_updated_at,
            version,
            ad_supported,
            crawled_at
        ) VALUES (
            %(application_id)s,
            %(min_installs)s,
            %(score)s,
            %(ratings)s,
            %(reviews)s,
            %(updated)s,
            %(version)s,
            %(ad_supported)s,
            %(crawled_at)s
        )
    """

    params = {
        "application_id": event["application_id"],
        "crawled_at": event["crawled_at"],
        **data,
    }

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, params)


def save_review(event: dict[str, Any]) -> None:
    data = event["data"]

    query = """
        INSERT INTO app_reviews(
            application_id,
            review_id,
            review_at,
            user_name,
            thumbs_up_count,
            score,
            content,
            crawled_at
        ) VALUES (
            %(application_id)s,
            %(review_id)s,
            %(at)s,
            %(user_name)s,
            %(thumbs_up_count)s,
            %(score)s,
            %(content)s,
            %(crawled_at)s
        )
        ON CONFLICT (application_id, review_id) DO UPDATE SET
            review_at = EXCLUDED.review_at,
            user_name = EXCLUDED.user_name,
            thumbs_up_count = EXCLUDED.thumbs_up_count,
            score = EXCLUDED.score,
            content = EXCLUDED.content,
            crawled_at = EXCLUDED.crawled_at
    """

    params = {
        "application_id": event["application_id"],
        "crawled_at": event["crawled_at"],
        **data,
    }

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, params)


def save_network_metrics(event: dict[str, Any]) -> None:
    query = """
        INSERT INTO network_measurements(
            application_id,
            scenario,
            file_name,
            handshake_rtt_ms,
            retransmission_count,
            zero_window_count,
            tcp_reset_count,
            total_bytes,
            payload_bytes,
            overhead_ratio,
            analyzed_at
        ) VALUES (
            %(application_id)s,
            %(scenario)s,
            %(file_name)s,
            %(handshake_rtt_ms)s,
            %(retransmission_count)s,
            %(zero_window_count)s,
            %(tcp_reset_count)s,
            %(total_bytes)s,
            %(payload_bytes)s,
            %(overhead_ratio)s,
            %(analyzed_at)s
        )
    """

    with connection() as conn, conn.cursor() as cur:
        cur.execute(query, event)


HANDLERS = {
    "playstore-stats": save_stats,
    "playstore-reviews": save_review,
    "network-metrics": save_network_metrics,
}
