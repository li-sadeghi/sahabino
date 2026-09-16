#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

docker compose up -d --build

echo "Waiting for services..."
for _ in {1..60}; do
  if curl -fsS http://localhost:8000/health >/dev/null \
    && curl -fsS http://localhost:8001/health >/dev/null \
    && curl -fsS http://localhost:8002/health >/dev/null \
    && curl -fsS http://localhost:3000/api/health >/dev/null; then
    echo "Sahabino is ready."
    echo "Application API: http://localhost:8000/docs"
    echo "Crawler API:     http://localhost:8001/docs"
    echo "Network API:     http://localhost:8002/docs"
    echo "Metabase:        http://localhost:3000"
    exit 0
  fi
  sleep 3
done

echo "Services did not become ready. Run: docker compose logs"
exit 1
