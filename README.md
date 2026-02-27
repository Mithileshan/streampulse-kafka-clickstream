# StreamPulse — Kafka Clickstream Pipeline

Real-time clickstream analytics pipeline: events flow from a Python producer through Kafka, get consumed into Postgres, and are served by a TypeScript analytics API.

## Architecture

```
Producer (Python)
      │
      ▼ JSON events
   Kafka (click-events topic, 3 partitions)
      │
      ▼ confluent-kafka consumer
Consumer (Python) ──► Postgres
                          │
                          ├── click_events      (raw event log)
                          └── click_aggregates  (per-shortcode counts)
                                    │
                                    ▼
                          Analytics API (Node.js/Express)
                                    │
                          GET /stats/:shortCode
                          GET /stats/top
                          GET /stats/trending
```

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Message Broker | Apache Kafka 3.7 (KRaft, no ZK)    |
| Producer       | Python + confluent-kafka + Faker    |
| Consumer       | Python + confluent-kafka + psycopg2 |
| Storage        | Postgres 16                         |
| Analytics API  | Node.js 20 + TypeScript + Express   |
| Monitoring     | Kafka UI                            |
| Container      | Docker + Docker Compose             |

## Local Stack

### Prerequisites
- Docker Desktop

### Start everything

```bash
cd infra
docker compose up -d
```

### Ports

| Service       | URL                     |
|---------------|-------------------------|
| Kafka         | localhost:9092          |
| Kafka UI      | http://localhost:8090   |
| Postgres      | localhost:5433          |
| Analytics API | http://localhost:4000   |

### Stop

```bash
cd infra
docker compose down
```

## Running the Pipeline

### Producer (emit click events)

```bash
cd producer
pip install -r requirements.txt
python producer.py
```

### Consumer (store events in Postgres)

```bash
cd consumer
pip install -r requirements.txt
python consumer.py
```

### Analytics API (local dev)

```bash
cd analytics
npm install
npm run dev
```

## API Reference

### GET /stats/:shortCode
Returns total clicks, last 24h clicks, and top referrers for a short code.

```json
{
  "shortCode": "abc123",
  "totalClicks": 94,
  "last24Hours": 94,
  "lastSeen": "2026-02-27T01:08:33.522Z",
  "topReferrers": [
    { "referrer": "http://dixon.com/", "clicks": 2 }
  ]
}
```

### GET /stats/top
Returns top 10 short codes by total clicks.

### GET /stats/trending?hours=24
Returns top 10 short codes by clicks in the last N hours.

### GET /health
Returns `{ "status": "ok" }`.

## Environment Variables

Copy `.env.example` to `.env`:

| Variable                 | Default        |
|--------------------------|----------------|
| KAFKA_BOOTSTRAP_SERVERS  | localhost:9092 |
| KAFKA_TOPIC_CLICK_EVENTS | click-events   |
| POSTGRES_HOST            | localhost      |
| POSTGRES_PORT            | 5433           |
| POSTGRES_DB              | streampulse    |
| POSTGRES_USER            | streampulse    |
| POSTGRES_PASSWORD        | streampulse    |

## Author

**Mithileshan** — [GitHub](https://github.com/Mithileshan)
