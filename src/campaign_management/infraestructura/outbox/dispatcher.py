# src/campaign_management/infraestructura/outbox/dispatcher.py
# ------------------------------------------------------------
# Publica eventos PENDING de outbox en Pulsar y los marca como PUBLISHED
# Ahora crea la Flask app y usa app.app_context() para acceder a db/engine.
# ------------------------------------------------------------

import json
import time
import logging
from datetime import datetime
from sqlalchemy import text

from campaign_management.config.db import db
from campaign_management.infraestructura.pulsar import pulsar_publisher, PulsarConfig
from campaign_management.main import create_app  # <<< IMPORTANTE

logger = logging.getLogger(__name__)
cfg = PulsarConfig()

# Use proper topic names with tenant and namespace
TOPIC_CAMPAIGN = cfg.get_topic_name("campaign-events")
TOPIC_CONTENT = cfg.get_topic_name("content-events")

def _publish_one(conn, row):
    payload = json.loads(row["payload"])
    key = row["aggregate_id"]
    
    logger.info(f"Publishing to campaign topic: {TOPIC_CAMPAIGN}")
    pulsar_publisher.publish_json(TOPIC_CAMPAIGN, key=key, payload=payload)
    
    logger.info(f"Publishing to content topic: {TOPIC_CONTENT}")
    pulsar_publisher.publish_json(TOPIC_CONTENT, key=key, payload=payload)
    
    conn.execute(
        text("UPDATE outbox_events SET status='PUBLISHED', published_at=:ts WHERE id=:id"),
        {"id": row["id"], "ts": datetime.utcnow()}
    )

def publish_pending_batch(batch_size: int = 200):
    # db.engine requiere app context
    with db.engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT 
                    id,
                    saga_id, 
                    aggregate_type as service, 
                    status, 
                    aggregate_id as event_id, 
                    event_type, 
                    payload as event_data, 
                    occurred_at as timestamp
                FROM outbox_events
                WHERE status = 'PENDING'
                ORDER BY occurred_at
                LIMIT :n
                FOR UPDATE SKIP LOCKED
            """),
            {"n": batch_size}
        ).mappings().all()

        for r in rows:
            try:
                _publish_one(conn, r)
            except Exception:
                logger.exception("Error publicando outbox id=%s", r["id"])
                conn.execute(
                    text("UPDATE outbox_events " \
                         "SET status='FAILED', attempts=attempts+1 " \
                         "WHERE id=:id"),
                    {"id": r["id"]}
                )

def run_forever(interval_seconds: float = 1.0):
    logging.basicConfig(level=logging.INFO)
    logger.info("Outbox dispatcher iniciado (interval=%.1fs)", interval_seconds)
    logger.info("Campaign topic: %s", TOPIC_CAMPAIGN)
    logger.info("Content topic: %s", TOPIC_CONTENT)
    try:
        while True:
            publish_pending_batch()
            time.sleep(interval_seconds)
    finally:
        pulsar_publisher.close()

def main():
    # Crear app y abrir contexto antes de usar db.*
    app = create_app()
    with app.app_context():
        run_forever(1.0)

if __name__ == "__main__":
    main()
