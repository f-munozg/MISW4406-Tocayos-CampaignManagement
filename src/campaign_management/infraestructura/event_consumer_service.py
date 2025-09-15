import logging
from datetime import datetime
from flask import current_app
import uuid

from campaign_management.config.db import db
from campaign_management.infraestructura.pulsar import pulsar_consumer
from campaign_management.modulos.campaign_management.infraestructura.modelos_read import CampanaReadDBModel

logger = logging.getLogger(__name__)

TOPIC_CAMPAIGN = "campaign-events"
SUBSCRIPTION  = "campaigns-read-projection"

class EventConsumerService:
    def __init__(self, app=None):
        self.app = app
    
    def start_consuming(self):
        pulsar_consumer.subscribe(TOPIC_CAMPAIGN, SUBSCRIPTION, self._on_message)

    def _on_message(self, payload: dict):
        # Use Flask application context when processing messages
        with self.app.app_context():
            et = payload.get("event_type")
            if et == "CampaignCreated":
                self._apply_campaign_created(payload)
            elif et == "CampaignActivated":
                self._apply_campaign_status_change(payload, "activa")
            elif et == "CampaignPaused":
                self._apply_campaign_status_change(payload, "pausada")
            elif et == "CampaignFinalized":
                self._apply_campaign_status_change(payload, "finalizada")
            else:
                logger.info("Evento ignorado: %s", et)

    def _apply_campaign_created(self, ev: dict):
        data = ev.get("data", {})
        aggregate_id = data.get("id")
        if aggregate_id is None:
            aggregate_id = uuid.uuid4()
        version = int(ev.get("version", 1))

        with db.session.begin():
            existing: CampanaReadDBModel | None = db.session.get(CampanaReadDBModel, aggregate_id)
            if existing:
                # idempotencia: si ya existe y la versión aplicada >= versión del evento, ignorar
                if existing.last_version >= version:
                    return
                # si existe pero con menor versión (poco probable al crear), actualizar campos básicos
                existing.nombre = data.get("nombre") or existing.nombre
                existing.tipo_campana = data.get("tipo_campana") or existing.tipo_campana
                existing.fecha_inicio = self._parse_iso(data.get("fecha_inicio")) or existing.fecha_inicio
                existing.fecha_fin = self._parse_iso(data.get("fecha_fin")) or existing.fecha_fin
                existing.last_version = version
                existing.fecha_ultima_actividad = datetime.utcnow()
                db.session.add(existing)
                return

            row = CampanaReadDBModel(
                id=aggregate_id,
                id_marca=data.get("id_marca"),
                nombre=data.get("nombre"),
                tipo_campana=data.get("tipo_campana"),
                estado="borrador",
                fecha_inicio=self._parse_iso(data.get("fecha_inicio")),
                fecha_fin=self._parse_iso(data.get("fecha_fin")),
                presupuesto_total=0.0,
                presupuesto_utilizado=0.0,
                meta_ventas=0,
                ventas_actuales=0,
                meta_engagement=0,
                engagement_actual=0,
                last_version=version,
                fecha_ultima_actividad=datetime.utcnow()
            )
            db.session.add(row)

    def _apply_campaign_status_change(self, ev: dict, new_status: str):
        aggregate_id = ev.get("aggregate_id")
        version = int(ev.get("version", 1))

        with db.session.begin():
            row: CampanaReadDBModel | None = db.session.get(CampanaReadDBModel, aggregate_id)
            if not row:
                logger.warning("Evento %s para campaña inexistente %s", ev.get("event_type"), aggregate_id)
                return
            if row.last_version >= version:
                return

            row.estado = new_status
            row.last_version = version
            row.fecha_ultima_actividad = datetime.utcnow()
            db.session.add(row)

    @staticmethod
    def _parse_iso(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

event_consumer_service = EventConsumerService()
