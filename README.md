# StreamPulse — Kafka Clickstream Pipeline

Real-time clickstream analytics pipeline: events flow from a Python producer through Kafka, get consumed into Postgres, and are served by a TypeScript analytics API.

## Demo

```bash
cd infra
docker compose up -d --build
```

Then open:

| What | URL |
|------|-----|
| Kafka UI (live topic messages) | http://localhost:8090 |
| Top short codes by clicks | http://localhost:4000/stats/top |
| Stats for a specific code | http://localhost:4000/stats/abc123 |
| Trending in last 24h | http://localhost:4000/stats/trending?hours=24 |

Run the producer in a second terminal to see events flow live:

```bash
cd producer && python producer.py
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        PRODUCER                             │
│         Python + Faker — generates click events             │
└──────────────────────────┬──────────────────────────────────┘
                           │ JSON  { shortCode, ip, referrer, ... }
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    APACHE KAFKA 3.7                         │
│          topic: click-events  │  3 partitions               │
│                  KRaft mode (no ZooKeeper)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ confluent-kafka consumer
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       CONSUMER                              │
│                  Python + psycopg2                          │
│                           │                                 │
│            ┌──────────────┴──────────────┐                  │
│            ▼                             ▼                  │
│    click_events                  click_aggregates           │
│  (raw event log)            (per-shortcode counters)        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    ANALYTICS API                            │
│            Node.js 20 + TypeScript + Express                │
│                                                             │
│   GET /stats/:shortCode   →  clicks + referrers             │
│   GET /stats/top          →  top 10 by total clicks         │
│   GET /stats/trending     →  top 10 in last N hours         │
└─────────────────────────────────────────────────────────────┘
```

---

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

---

## Running the Pipeline

### 1. Start the stack

```bash
cd infra
docker compose up -d --build
```

### 2. Produce events

```bash
cd producer
pip install -r requirements.txt
python producer.py
```

### 3. Consume into Postgres

```bash
cd consumer
pip install -r requirements.txt
python consumer.py
```

### 4. Query the API

```bash
curl http://localhost:4000/stats/top
curl http://localhost:4000/stats/abc123
curl "http://localhost:4000/stats/trending?hours=24"
```

### Stop

```bash
cd infra
docker compose down
```

---

## API Reference

### GET /stats/:shortCode

```json
{
  "shortCode": "abc123",
  "totalClicks": 273,
  "last24Hours": 273,
  "lastSeen": "2026-02-27T01:28:57.920Z",
  "topReferrers": [
    { "referrer": "https://brown.com/", "clicks": 3 },
    { "referrer": "http://johnson.com/", "clicks": 3 }
  ]
}
```

### GET /stats/top

```json
[
  { "short_code": "abc123", "total_clicks": "273", "last_seen": "..." },
  { "short_code": "xyz789", "total_clicks": "268", "last_seen": "..." }
]
```

### GET /stats/trending?hours=24

```json
[
  { "short_code": "abc123", "clicks": "273" },
  { "short_code": "xyz789", "clicks": "268" }
]
```

### GET /health

```json
{ "status": "ok", "timestamp": "2026-02-27T01:26:36.698Z" }
```

---

## Ports

| Service       | URL                     |
|---------------|-------------------------|
| Kafka         | localhost:9092          |
| Kafka UI      | http://localhost:8090   |
| Postgres      | localhost:5433          |
| Analytics API | http://localhost:4000   |

---

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

---

## Author

**Mithileshan** — [GitHub](https://github.com/Mithileshan)
