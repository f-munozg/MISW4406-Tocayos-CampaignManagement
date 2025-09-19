# src/campaign_management/infraestructura/event_consumer_service.py
# ----------------------------------------------------------------
# Consume eventos de Pulsar y actualiza la proyección (tabla campaigns).
# ----------------------------------------------------------------

import logging
import uuid
from datetime import datetime

from campaign_management.config.db import db
from campaign_management.infraestructura.pulsar import PulsarEventConsumer, PulsarConfig
from campaign_management.modulos.campaign_management.infraestructura.modelos_read import CampanaReadDBModel

# Import new event handlers (optional)
try:
    from campaign_management.modulos.campaign_management.aplicacion.handlers.event_handler_factory import EventHandlerFactory
    NEW_HANDLERS_AVAILABLE = True
except ImportError:
    NEW_HANDLERS_AVAILABLE = False

logger = logging.getLogger(__name__)

TOPIC_CAMPAIGN = "campaign-events"
SUBSCRIPTION  = "campaign-projection"

class EventConsumerService:
    def __init__(self, use_new_handlers: bool = False, app=None):
        self.config = PulsarConfig()
        self.consumer = PulsarEventConsumer()
        self.running = False
        self.use_new_handlers = use_new_handlers and NEW_HANDLERS_AVAILABLE
        self.app = app  # Store Flask app reference
        
        if self.use_new_handlers:
            logger.info("Using new event handlers")
        else:
            logger.info("Using legacy event handlers")
    
    def start_consuming(self):
        """Start consuming events with proper error handling"""
        try:
            topic_name = self.config.get_topic_name(TOPIC_CAMPAIGN)
            logger.info(f"Starting to consume from topic: {topic_name}")
            
            self.running = True
            self.consumer.subscribe_to_topic(topic_name, SUBSCRIPTION, self._on_message)
            logger.info("Successfully started consuming events")
            
        except Exception as e:
            logger.error(f"Failed to start consuming events: {e}")
            self.running = False
            # Don't re-raise the exception to prevent container restart
            # Instead, log the error and continue
    
    def stop_consuming(self):
        """Stop consuming events"""
        if not self.running:
            return
        
        self.running = False
        try:
            self.consumer.close()
            logger.info("Event consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping event consumer: {e}")

    # ----- Dispatcher por tipo de evento -----
    def _on_message(self, payload: dict):
        """Handle incoming messages with error recovery"""
        try:
            if not self.running:
                logger.info("Consumer stopped, ignoring message")
                return
                
            et = payload.get("event_type")
            logger.info(f"Processing event: {et}")
            logger.info(f"Full payload structure: {payload}")
            
            # Use new handlers if available and enabled
            if self.use_new_handlers:
                # Ensure we're in a Flask app context when using new handlers
                if self.app:
                    with self.app.app_context():
                        EventHandlerFactory.handle_event(payload)
                else:
                    logger.warning("No Flask app context available for new handlers, falling back to legacy")
                    # Fall back to legacy handlers
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
            else:
                # Use legacy handlers
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
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Message payload: {payload}")
            # Don't re-raise to prevent consumer crash

    # ----- Aplicadores (proyección) -----
    def _apply_campaign_created(self, ev: dict):
        """Apply CampaignCreated event to read model with error handling"""
        try:
            logger.info(f"Processing CampaignCreated event: {ev}")
            
            # Try multiple ways to get the campaign ID
            aggregate_id = None
            
            # Method 1: From data.id (expected structure)
            data = ev.get("data", {})
            if data and data.get("id"):
                aggregate_id = data.get("id")
                logger.info(f"Found campaign ID in data.id: {aggregate_id}")
            
            # Method 2: From aggregate_id (alternative structure)
            if not aggregate_id and ev.get("aggregate_id"):
                aggregate_id = ev.get("aggregate_id")
                logger.info(f"Found campaign ID in aggregate_id: {aggregate_id}")
            
            # Method 3: From event_data.id (direct structure)
            if not aggregate_id and ev.get("id"):
                aggregate_id = ev.get("id")
                logger.info(f"Found campaign ID in event.id: {aggregate_id}")
            
            version = int(ev.get("version", 1))

            if not aggregate_id:
                logger.warning("Campaign ID not found in event data")
                logger.warning(f"Available keys in event: {list(ev.keys())}")
                if data:
                    logger.warning(f"Available keys in data: {list(data.keys())}")
                return

            with db.session.begin():
                # Save to campaigns_read table (read model)
                existing: CampanaReadDBModel | None = db.session.get(CampanaReadDBModel, aggregate_id)
                if existing:
                    # idempotencia: si ya existe y la versión aplicada >= versión del evento, ignorar
                    if existing.last_version >= version:
                        logger.info(f"Campaign {aggregate_id} already up to date (version {version})")
                        return
                    # si existe pero con menor versión, actualizar campos básicos
                    existing.nombre = data.get("nombre") or existing.nombre
                    existing.tipo_campana = data.get("tipo_campana") or existing.tipo_campana
                    existing.fecha_inicio = self._parse_iso(data.get("fecha_inicio")) or existing.fecha_inicio
                    existing.fecha_fin = self._parse_iso(data.get("fecha_fin")) or existing.fecha_fin
                    existing.last_version = version
                    existing.fecha_ultima_actividad = datetime.utcnow()
                    db.session.add(existing)
                    logger.info(f"Updated existing campaign {aggregate_id}")
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
                if row.id_marca is None:
                    row.id_marca = uuid.uuid4()

                if row.nombre is None:
                    row.nombre = ""

                if row.tipo_campana is None:
                    row.tipo_campana = ""
                
                db.session.add(row)
                logger.info(f"Created new campaign read model {aggregate_id}")
                
        except Exception as e:
            logger.error(f"Error applying CampaignCreated event: {e}")
            logger.error(f"Event data: {ev}")
            # Rollback the transaction
            db.session.rollback()
            raise

    def _apply_campaign_status_change(self, ev: dict, new_status: str):
        """Apply campaign status change event to read model with error handling"""
        try:
            aggregate_id = ev.get("aggregate_id")
            version = int(ev.get("version", 1))

            if not aggregate_id:
                logger.warning("Campaign ID not found in status change event")
                return

            with db.session.begin():
                # Update campaigns_read table (read model)
                row: CampanaReadDBModel | None = db.session.get(CampanaReadDBModel, aggregate_id)
                if not row:
                    logger.warning("Evento %s para campaña inexistente %s", ev.get("event_type"), aggregate_id)
                    return
                if row.last_version >= version:
                    logger.info(f"Campaign {aggregate_id} already up to date (version {version})")
                    return

                row.estado = new_status
                row.last_version = version
                row.fecha_ultima_actividad = datetime.utcnow()
                db.session.add(row)
                logger.info(f"Updated campaign {aggregate_id} status to {new_status}")
                
        except Exception as e:
            logger.error(f"Error applying campaign status change event: {e}")
            logger.error(f"Event data: {ev}")
            # Rollback the transaction
            db.session.rollback()
            raise

    @staticmethod
    def _parse_iso(s: str | None):
        if not s:
            return None
        try:
            # 2025-01-01T00:00:00Z o sin 'Z'
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

# singleton - will be created with Flask app context
event_consumer_service = None

def create_event_consumer_service(app, use_new_handlers=True):
    """Create the event consumer service with Flask app context"""
    global event_consumer_service
    if event_consumer_service is None:
        event_consumer_service = EventConsumerService(use_new_handlers=use_new_handlers, app=app)
    return event_consumer_service
