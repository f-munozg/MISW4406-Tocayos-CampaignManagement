from flask import Blueprint, jsonify
from sqlalchemy import text
from campaign_management.config.db import db
from campaign_management.infraestructura.pulsar import PulsarConfig
from pulsar import Client

bp = Blueprint("health", __name__, url_prefix="/health")

@bp.route("", methods=["GET"])
def health():
    # DB check
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Pulsar check
    try:
        cfg = PulsarConfig()
        client = Client(cfg.service_url)
        client.close()
        pulsar_ok = True
    except Exception:
        pulsar_ok = False

    return jsonify({"db": db_ok, "pulsar": pulsar_ok}), 200 if (db_ok and pulsar_ok) else 503
