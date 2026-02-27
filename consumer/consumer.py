import json
import os
import psycopg2
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv

load_dotenv()

# ── Postgres connection ────────────────────────────────────────────────────────
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    dbname=os.getenv("POSTGRES_DB", "streampulse"),
    user=os.getenv("POSTGRES_USER", "streampulse"),
    password=os.getenv("POSTGRES_PASSWORD", "streampulse"),
)
conn.autocommit = True
cur = conn.cursor()

# ── Create tables if not exists ───────────────────────────────────────────────
cur.execute("""
    CREATE TABLE IF NOT EXISTS click_events (
        id          SERIAL PRIMARY KEY,
        short_code  TEXT        NOT NULL,
        user_id     INTEGER,
        ip          TEXT,
        referrer    TEXT,
        user_agent  TEXT,
        occurred_at TIMESTAMPTZ NOT NULL
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS click_aggregates (
        short_code   TEXT PRIMARY KEY,
        total_clicks BIGINT      NOT NULL DEFAULT 0,
        last_seen    TIMESTAMPTZ NOT NULL
    );
""")

print("Tables ready.")

# ── Kafka consumer ─────────────────────────────────────────────────────────────
consumer = Consumer({
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'group.id':          'streampulse-consumer',
    'auto.offset.reset': 'earliest',
})
consumer.subscribe([os.getenv("KAFKA_TOPIC_CLICK_EVENTS", "click-events")])

print("Consuming click events... (Ctrl+C to stop)")

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print(f"Error: {msg.error()}")
            continue

        event = json.loads(msg.value().decode("utf-8"))

        short_code = event.get("shortCode")
        user_id    = event.get("userId")
        ip         = event.get("ip")
        referrer   = event.get("referrer")
        user_agent = event.get("userAgent")
        occurred_at = event.get("timestamp")

        # Insert raw event
        cur.execute("""
            INSERT INTO click_events (short_code, user_id, ip, referrer, user_agent, occurred_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (short_code, user_id, ip, referrer, user_agent, occurred_at))

        # Upsert aggregate
        cur.execute("""
            INSERT INTO click_aggregates (short_code, total_clicks, last_seen)
            VALUES (%s, 1, %s)
            ON CONFLICT (short_code)
            DO UPDATE SET
                total_clicks = click_aggregates.total_clicks + 1,
                last_seen    = EXCLUDED.last_seen
        """, (short_code, occurred_at))

        print(f"Stored: {short_code} | user={user_id} | ip={ip}")

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    consumer.close()
    cur.close()
    conn.close()
