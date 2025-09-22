import logging
import json
import os
from datetime import datetime
from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import CancelarCampana
from flask import current_app
from typing import Dict, Any

import uuid

from campaign_management.config.db import db
from campaign_management.infraestructura.pulsar import PulsarEventConsumer, PulsarConfig
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel
from campaign_management.infraestructura.outbox.model import OutboxEvent
from campaign_management.infraestructura.pulsar import pulsar_publisher

logger = logging.getLogger(__name__)

# TOPIC_CAMPAIGN = "campaign-events"
# SUBSCRIPTION  = "campaigns-read-projection"

class EventConsumerService:
    def __init__(self, app=None, service_name: str = None):
        self.config = PulsarConfig()
        self.consumers = {}
        self.running = False
        self.app = app
        self.service_name = service_name or os.getenv('SERVICE_NAME', 'campaign-management')
    
    def start_consuming(self):
        """Inicia el consumo de eventos para todos los módulos"""
        self.running = True
        
        # Eventos de programas de lealtad
        self._start_consumer('loyalty-events', self._on_message_loyalty)
        self._start_consumer('campaign-events', self._on_message_campaign)
        
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
            consumer = PulsarEventConsumer(service_name=self.service_name)
            topic_name = self.config.get_topic_name(event_type)
            subscription_name = f"campaign-management-subscription"
            consumer.subscribe_to_topic(topic_name, subscription_name, handler)
            self.consumers[event_type] = consumer
            logger.info(f"Consumidor iniciado para {event_type} con servicio {self.service_name}")
        except Exception as e:
            logger.error(f"Error iniciando consumidor para {event_type}: {e}")

    def _on_message_loyalty(self, event_data: Dict[str, Any]):
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

    def _on_message_campaign(self, event_data: Dict[str, Any]):
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
        event_status = event_data.get('status')
        saga_id = event_data.get('saga_id')
        event_payload = event_data.get('event_data', {})
        
        logger.info(f"Procesando evento de campañas: {event_type} con status: {event_status} y saga_id: {saga_id}")
        logger.info(f"Evento payload: {event_payload}")
        
        # Aquí se pueden agregar lógicas específicas para cada tipo de evento
        if event_type == 'CommandCreateCampaign' and event_status == "success":
            self._apply_campaign_created(event_payload, saga_id)
        elif event_type == 'EventCampaignCreated' and event_status == "failed":
            self._apply_campaign_reverse_created(event_payload, saga_id)
        else:
            logger.info("Evento ignorado: %s %s", event_type, event_status)

    def _apply_campaign_created(self, ev: dict, saga_id: str):
        data = ev.get("data", {})
        aggregate_id = data.get("id")
        if aggregate_id is None:
            aggregate_id = uuid.uuid4()
        version = int(ev.get("version", 1))

        with db.session.begin():
            existing: CampanaDBModel | None = db.session.get(CampanaDBModel, aggregate_id)
            if existing:
                return

            camp = CampanaDBModel(
                id=aggregate_id,
                id_marca=data.get("id_marca"),
                nombre=data.get("nombre"),
                tipo_campana=data.get("tipo_campana"),
                objetivo=data.get("objetivo", "ventas"),  # default value
                estado="borrador",
                fecha_inicio=self._parse_iso(data.get("fecha_inicio")),
                fecha_fin=self._parse_iso(data.get("fecha_fin")),
                presupuesto_total=0.0,
                presupuesto_utilizado=0.0,
                meta_ventas=0,
                ventas_actuales=0,
                meta_engagement=0,
                engagement_actual=0,
                fecha_ultima_actividad=datetime.utcnow()
            )

            if camp.id_marca is None:
                camp.id_marca = uuid.uuid4()

            if camp.nombre is None:
                camp.nombre = ""

            if camp.tipo_campana is None:
                camp.tipo_campana = ""
            
            db.session.add(camp)
            
            # Save to outbox table for event publishing
            outbox_event = OutboxEvent(
                saga_id = saga_id,
                aggregate_id=aggregate_id,
                aggregate_type='Campaign',
                event_type='EventCampaignCreated',
                payload=json.dumps(ev, default=str),
                status='PENDING'
            )
            db.session.add(outbox_event)

    def _apply_campaign_reverse_created(self, ev: dict, saga_id: str):
        data = ev.get("data", {})

        with db.session.begin():
            # buscar la campaña y cambiarle el estado
            outbox = db.session.query(OutboxEvent).filter(OutboxEvent.saga_id == saga_id).first()
            logger.info("outbox: %s", outbox)
            if outbox is None:
                logger.info(f"Clase: EventConsumerService | Metodo: _apply_campaign_reverse_created | Linea: 183")
                logger.info("Evento %s para saga_id inexistente %s", ev.get("event_type"), saga_id)
                return
            camp: CampanaDBModel | None = db.session.get(CampanaDBModel, outbox.aggregate_id)
            if camp is None:
                logger.info(f"Clase: EventConsumerService | Metodo: _apply_campaign_reverse_created | Linea: 178")
                logger.info("Evento %s para campaña inexistente %s", ev.get("event_type"), outbox.aggregate_id)
                return

            camp.estado = 'cancelada'
            camp.fecha_ultima_actividad = datetime.utcnow()
            
        # Publicar eventos después de cerrar la transacción
        evento = CancelarCampana(
            id_campana=outbox.aggregate_id if outbox else None,
            motivo='Se presento un error con la creacion de la campaña',
            saga_id=saga_id,
            fecha_actualizacion=datetime.now()
        )
        # escribir en la cola de loyalty
        pulsar_publisher.publish_event(evento, saga_id, 'loyalty-events', 'CommandCreateCampaign', 'failed')
        # escribir en la cola de campaigns
        evento.motivo = "Se ha actualizado el estado de la campaña a cancelado"
        pulsar_publisher.publish_event(evento, saga_id, 'campaign-events', 'EventCampaignRollbacked', 'success')
    
    def _apply_campaign_status_change(self, ev: dict, new_status: str):
        aggregate_id = ev.get("aggregate_id")
        version = int(ev.get("version", 1))

        with db.session.begin():
            # Update campaigns table (write model)
            camp: CampanaDBModel | None = db.session.get(CampanaDBModel, aggregate_id)
            if not camp:
                logger.warning("Evento %s para campaña inexistente %s", ev.get("event_type"), aggregate_id)
                return

            camp.estado = new_status
            camp.fecha_ultima_actividad = datetime.utcnow()
            db.session.add(camp)
            
            # Save to outbox table for event publishing
            outbox_event = OutboxEvent(
                aggregate_id=aggregate_id,
                aggregate_type='Campaign',
                event_type=ev.get("event_type"),
                payload=json.dumps(ev, default=str),
                status='PENDING'
            )
            db.session.add(outbox_event)

    @staticmethod
    def _parse_iso(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

event_consumer_service = EventConsumerService()
