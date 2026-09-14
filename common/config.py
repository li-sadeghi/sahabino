import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sahabino:sahabino@postgres:5432/sahabino",
)
