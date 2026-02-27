import json
import time
import random
from datetime import datetime
from confluent_kafka import Producer
from faker import Faker
from dotenv import load_dotenv
import os

load_dotenv()
fake = Faker()

conf = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
}

producer = Producer(conf)
topic = os.getenv("KAFKA_TOPIC_CLICK_EVENTS", "click-events")

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}]")

def generate_event():
    return {
        "shortCode": random.choice(["abc123", "xyz789", "url456"]),
        "userId": random.randint(1, 10),
        "timestamp": datetime.utcnow().isoformat(),
        "referrer": fake.url(),
        "userAgent": fake.user_agent(),
        "ip": fake.ipv4_public()
    }

print("Producing click events... (Ctrl+C to stop)")

while True:
    event = generate_event()
    producer.produce(topic, json.dumps(event), callback=delivery_report)
    producer.poll(0)
    time.sleep(0.2)
