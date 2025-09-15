import json
import logging
from collections import defaultdict
from datetime import datetime

from pulsar import Client, InitialPosition, ConsumerType
from campaign_management.infraestructura.pulsar import PulsarConfig
from campaign_management.config.db import db
from campaign_management.modulos.campaign_management.infraestructura.modelos_read import CampanaReadDBModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify")

TOPIC_CAMPAIGN = "campaign-events"
SUBSCRIPTION  = "verification-tmp-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

def build_expected_state_from_events():
    cfg = PulsarConfig()
    client = Client(cfg.service_url)
    consumer = client.subscribe(
        cfg.topic(TOPIC_CAMPAIGN),
        subscription_name=SUBSCRIPTION,
        consumer_type=ConsumerType.Exclusive,
        initial_position=InitialPosition.Earliest,
    )
    expected = {}  # id -> {"last_version": v, "estado": s}
    try:
        while True:
            msg = consumer.receive(timeout_millis=1500)
            try:
                ev = json.loads(msg.data().decode("utf-8"))
                et = ev.get("event_type")
                version = int(ev.get("version", 1))
                if et == "CampaignCreated":
                    cid = ev["data"]["id"]
                    cur = expected.get(cid)
                    if not cur or version > cur["last_version"]:
                        expected[cid] = {"last_version": version, "estado": "borrador"}
                elif et == "CampaignActivated":
                    cid = ev["aggregate_id"]
                    cur = expected.get(cid, {"last_version": 0, "estado": "borrador"})
                    if version > cur["last_version"]:
                        expected[cid] = {"last_version": version, "estado": "activa"}
                elif et == "CampaignPaused":
                    cid = ev["aggregate_id"]
                    cur = expected.get(cid, {"last_version": 0, "estado": "borrador"})
                    if version > cur["last_version"]:
                        expected[cid] = {"last_version": version, "estado": "pausada"}
                elif et == "CampaignFinalized":
                    cid = ev["aggregate_id"]
                    cur = expected.get(cid, {"last_version": 0, "estado": "borrador"})
                    if version > cur["last_version"]:
                        expected[cid] = {"last_version": version, "estado": "finalizada"}
                consumer.acknowledge(msg)
            except Exception:
                consumer.negative_acknowledge(msg)
    except Exception:
        # timeout normal: cortamos consumo
        pass
    finally:
        consumer.close()
        client.close()
    return expected

def compare_projection(expected: dict):
    mismatches = []
    missing = []
    extra = []

    # leer proyección
    rows = db.session.query(CampanaReadDBModel).all()
    proj = {r.id: {"last_version": r.last_version, "estado": r.estado} for r in rows}

    # comparar
    for cid, est in expected.items():
        if cid not in proj:
            missing.append(cid)
        else:
            if proj[cid]["last_version"] != est["last_version"] or proj[cid]["estado"] != est["estado"]:
                mismatches.append((cid, est, proj[cid]))
    for cid in proj.keys():
        if cid not in expected:
            extra.append(cid)

    return mismatches, missing, extra

def main():
    expected = build_expected_state_from_events()
    mismatches, missing, extra = compare_projection(expected)

    print("\n--- Verificación campaigns_read vs. eventos ---")
    print(f"Total campañas según eventos: {len(expected)}")
    print(f"Total campañas en proyección: {len(expected) + len(extra) - len(missing)}")

    if missing:
        print(f"\n[Missing en proyección] {len(missing)} ids (ejemplos): {missing[:10]}")
    if extra:
        print(f"\n[Extra en proyección] {len(extra)} ids no vistos en eventos (ejemplos): {extra[:10]}")
    if mismatches:
        print(f"\n[Mismatches] {len(mismatches)} filas con diferencias de estado o versión (primeros 5):")
        for cid, exp, pr in mismatches[:5]:
            print(f"  - {cid}: expected={exp}, projection={pr}")
    if not (missing or extra or mismatches):
        print("\n✅ Proyección consistente con los eventos.")

if __name__ == "__main__":
    main()
