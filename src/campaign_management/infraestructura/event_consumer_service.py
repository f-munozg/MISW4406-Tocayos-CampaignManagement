import logging
from datetime import datetime
from flask import current_app
from typing import Dict, Any

import uuid

from campaign_management.config.db import db
from campaign_management.infraestructura.pulsar import PulsarEventConsumer, PulsarConfig
from campaign_management.modulos.campaign_management.infraestructura.modelos_read import CampanaReadDBModel

logger = logging.getLogger(__name__)

# TOPIC_CAMPAIGN = "campaign-events"
# SUBSCRIPTION  = "campaigns-read-projection"

class EventConsumerService:
    def __init__(self, app=None):
        self.config = PulsarConfig()
        self.consumers = {}
        self.running = False
        self.app = app
    
    def start_consuming(self):
        """Inicia el consumo de eventos para todos los módulos"""
        self.running = True
        
        # Eventos de programas de lealtad
        self._start_consumer('campaign-events', self._on_message)
        
        logger.info("Servicio de consumo de eventos iniciado")

    def stop_consuming(self):
        """Detiene el consumo de eventos"""
        if not self.running:
            return  # Ya está detenido
        
        self.running = False
        for event_type, consumer in self.consumers.items():
            try:
                consumer.close()
                logger.info(f"Consumidor {event_type} cerrado")
            except Exception as e:
                logger.error(f"Error cerrando consumidor {event_type}: {e}")
        
        self.consumers.clear()
        logger.info("Servicio de consumo de eventos detenido")

    def _start_consumer(self, event_type: str, handler):
        """Inicia un consumidor para un tipo específico de evento"""
        try:
            consumer = PulsarEventConsumer()
            topic_name = self.config.get_topic_name(event_type)
            subscription_name = f"{event_type}-subscription"
            consumer.subscribe_to_topic(topic_name, subscription_name, handler)
            self.consumers[event_type] = consumer
            logger.info(f"Consumidor iniciado para {event_type}")
        except Exception as e:
            logger.error(f"Error iniciando consumidor para {event_type}: {e}")

    def _on_message(self, event_data: Dict[str, Any]):
        try:
            # Ensure we have Flask application context
            if self.app:
                with self.app.app_context():
                    self._process_event(event_data)
            else:
                # Fallback: try to get current app context
                try:
                    with current_app.app_context():
                        self._process_event(event_data)
                except RuntimeError:
                    logger.error("No Flask application context available for event processing")
                    return
        except Exception as e:
            logger.error(f"Error procesando evento de programa de lealtad: {e}")

    def _process_event(self, event_data: Dict[str, Any]):
        """Process the event within Flask application context"""
        event_type = event_data.get('event_type')
        event_payload = event_data.get('event_data', {})
        
        logger.info(f"Procesando evento de campañas: {event_type}")
        
        # Aquí se pueden agregar lógicas específicas para cada tipo de evento
        if event_type == 'CampaignCreated':
            self._apply_campaign_created(event_payload)
        elif event_type == 'CampaignActivated':
           self._apply_campaign_status_change(event_payload, "activa")
        elif event_type == 'CampaignPaused':
            self._apply_campaign_status_change(event_payload, "pausada")
        elif event_type == 'CampaignFinalized':
            self._apply_campaign_status_change(event_payload, "finalizada")
        else:
            logger.info("Evento ignorado: %s", event_type)

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
                existing.tipo_campana = data.get("tipo") or existing.tipo_campana
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
                tipo_campana=data.get("tipo"),
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
            if row.id_marca is None:
                row.id_marca = uuid.uuid4()

            if row.nombre is None:
                row.nombre = ""

            if row.tipo_campana is None:
                row.tipo_campana = ""
            
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
