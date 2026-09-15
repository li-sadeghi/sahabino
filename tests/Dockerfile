FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pytest.ini .
COPY common ./common
COPY app_service ./app_service
COPY crawler_service ./crawler_service
COPY storage_service ./storage_service
COPY network_service ./network_service
COPY tests ./tests

CMD ["pytest"]
