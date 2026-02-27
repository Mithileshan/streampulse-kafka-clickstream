# StreamPulse — Kafka Clickstream Pipeline

Real-time clickstream pipeline using Kafka + Postgres to produce events, consume them, compute aggregates, and expose analytics-ready tables.

## Local Stack (Kafka + UI + Postgres)

### Prereqs
- Docker Desktop

### Run
```bash
cd infra
docker compose up -d
```

### Verify

* Kafka UI: http://localhost:8080
* Postgres: localhost:5432 (db/user/pass: streampulse)

### Stop

```bash
cd infra
docker compose down
```

## Next Phases

* Producer: emit click events to Kafka (`click-events`)
* Consumer: store raw events + compute aggregates in Postgres
* Analytics: API or dashboard for stats
