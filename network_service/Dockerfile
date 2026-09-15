FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY network_service ./network_service

CMD ["uvicorn", "network_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
