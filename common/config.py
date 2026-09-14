import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sahabino:sahabino@postgres:5432/sahabino",
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka:9092",
)
APP_SERVICE_URL = os.getenv(
    "APP_SERVICE_URL",
    "http://app-service:8000",
)
CRAWL_INTERVAL_SECONDS = int(
    os.getenv("CRAWL_INTERVAL_SECONDS", "3600")
)
PLAYSTORE_LANGUAGE = os.getenv("PLAYSTORE_LANGUAGE", "en")
PLAYSTORE_COUNTRY = os.getenv("PLAYSTORE_COUNTRY", "us")

STATS_TOPIC = "playstore-stats"
REVIEWS_TOPIC = "playstore-reviews"
NETWORK_TOPIC = "network-metrics"
