# src/campaign_management/infraestructura/event_consumer_service.py
# ----------------------------------------------------------------
# Consume eventos de Pulsar y actualiza la proyección (tabla campaigns).
# ----------------------------------------------------------------

import logging
from datetime import datetime

from campaign_management.config.db import db
from campaign_management.infraestructura.pulsar import pulsar_consumer
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel

logger = logging.getLogger(__name__)

TOPIC_CAMPAIGN = "campaign-events"
SUBSCRIPTION  = "campaign-projection"

class EventConsumerService:
    def start_consuming(self):
        pulsar_consumer.subscribe(TOPIC_CAMPAIGN, SUBSCRIPTION, self._on_message)

    # ----- Dispatcher por tipo de evento -----
    def _on_message(self, payload: dict):
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

    # ----- Aplicadores (proyección) -----
    def _apply_campaign_created(self, ev: dict):
        data = ev.get("data", {})
        aggregate_id = data.get("id")
        version = int(ev.get("version", 1))

        with db.session.begin():
            # Si ya existe y version >= guardada, no duplicar
            camp: CampanaDBModel | None = db.session.get(CampanaDBModel, aggregate_id)
            if camp:
                # Idempotencia básica: no reinsertar
                return

            camp = CampanaDBModel(
                id=aggregate_id,
                id_marca=data.get("id_marca"),
                nombre=data.get("nombre"),
                tipo_campana=data.get("tipo_campana"),
                estado="borrador",
                fecha_inicio=self._parse_iso(data.get("fecha_inicio")),
                fecha_fin=self._parse_iso(data.get("fecha_fin")),
                # iniciales:
                presupuesto_total=0.0,
                presupuesto_utilizado=0.0,
                meta_ventas=0,
                ventas_actuales=0,
                meta_engagement=0,
                engagement_actual=0,
                # pista mínima para idempotencia por evento
                fecha_ultima_actividad=datetime.utcnow()
            )
            db.session.add(camp)

    def _apply_campaign_status_change(self, ev: dict, new_status: str):
        aggregate_id = ev.get("aggregate_id")
        version = int(ev.get("version", 1))

        with db.session.begin():
            camp: CampanaDBModel | None = db.session.get(CampanaDBModel, aggregate_id)
            if not camp:
                logger.warning("Evento %s para campaña inexistente %s", ev.get("event_type"), aggregate_id)
                return

            # Actualizar la proyección
            camp.estado = new_status
            camp.fecha_ultima_actividad = datetime.utcnow()
            db.session.add(camp)

    @staticmethod
    def _parse_iso(s: str | None):
        if not s:
            return None
        try:
            # 2025-01-01T00:00:00Z o sin 'Z'
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

# singleton
event_consumer_service = EventConsumerService()
