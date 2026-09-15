FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY app_service ./app_service

CMD ["uvicorn", "app_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
