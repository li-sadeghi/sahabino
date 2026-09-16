# Sahabino

This project collects Google Play data and network data. It uses small services,
Kafka, PostgreSQL, FastAPI, Docker and Metabase.

## Start

You need Docker and Docker Compose.

```bash
chmod +x scripts/*.sh
./scripts/start.sh
```

Open these pages:

- Application API: http://localhost:8000/docs
- Crawler API: http://localhost:8001/docs
- Network API: http://localhost:8002/docs
- Metabase: http://localhost:3000

The crawler runs at startup and then once every hour. You can also run it now:

```bash
./scripts/crawl-now.sh
```

Some Iranian apps may not be available in the selected Google Play country.
You can change their package name or disable them with the Application API.

## Test

```bash
./scripts/test.sh
```

For a PCAP file, open the Network API docs, choose `POST /analyze`, set the app
id and scenario (`upload` or `download`), and upload the file.

For Metabase, select PostgreSQL and use these values:

- Host: `postgres`
- Port: `5432`
- Database: `sahabino`
- User: `sahabino`
- Password: `sahabino`

Use the queries in `analytics/queries.sql` to make the required charts.

Stop the project:

```bash
./scripts/stop.sh
```

To remove all saved data too:

```bash
docker compose down -v
```
