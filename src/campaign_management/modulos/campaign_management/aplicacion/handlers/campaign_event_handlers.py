"""Event handlers for campaign domain events"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any

from campaign_management.seedwork.aplicacion.event_handlers import EventHandler
from campaign_management.seedwork.infraestructura.repositories import CampaignRepository, OutboxRepository

logger = logging.getLogger(__name__)

class CampaignCreatedEventHandler(EventHandler):
    """Handles CampaignCreated events"""
    
    def __init__(self, campaign_repository: CampaignRepository = None, outbox_repository: OutboxRepository = None):
        self.campaign_repository = campaign_repository
        self.outbox_repository = outbox_repository
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Handle CampaignCreated event"""
        try:
            if not self.campaign_repository or not self.outbox_repository:
                logger.warning("Repositories not available - event will be logged only")
                logger.info(f"CampaignCreated event data: {event_data}")
                return
                
            data = event_data.get("data", {})
            aggregate_id = data.get("id")
            if aggregate_id is None:
                aggregate_id = uuid.uuid4()
            
            # Check if campaign already exists (idempotency)
            existing = self.campaign_repository.get_by_id(aggregate_id)
            if existing:
                logger.info(f"Campaign {aggregate_id} already exists, skipping creation")
                return
            
            # Create campaign entity (this would be done through a factory or builder)
            # For now, we'll assume the event data contains all necessary information
            campaign_data = {
                "id": aggregate_id,
                "id_marca": data.get("id_marca"),
                "nombre": data.get("nombre"),
                "tipo_campana": data.get("tipo_campana"),
                "objetivo": data.get("objetivo", "ventas"),
                "estado": "borrador",
                "fecha_inicio": self._parse_iso(data.get("fecha_inicio")),
                "fecha_fin": self._parse_iso(data.get("fecha_fin")),
                "presupuesto_total": 0.0,
                "presupuesto_utilizado": 0.0,
                "meta_ventas": 0,
                "ventas_actuales": 0,
                "meta_engagement": 0,
                "engagement_actual": 0,
                "fecha_ultima_actividad": datetime.utcnow()
            }
            
            # Save to write model
            self.campaign_repository.save(campaign_data)
            
            # Save to outbox for event publishing
            outbox_event = {
                "aggregate_id": aggregate_id,
                "aggregate_type": "Campaign",
                "event_type": "CampaignCreated",
                "payload": json.dumps(event_data, default=str),
                "status": "PENDING"
            }
            self.outbox_repository.save(outbox_event)
            
            logger.info(f"Campaign {aggregate_id} created successfully")
            
        except Exception as e:
            logger.error(f"Error handling CampaignCreated event: {e}")
            raise

    @staticmethod
    def _parse_iso(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

class CampaignStatusChangedEventHandler(EventHandler):
    """Handles campaign status change events"""
    
    def __init__(self, campaign_repository: CampaignRepository = None, outbox_repository: OutboxRepository = None):
        self.campaign_repository = campaign_repository
        self.outbox_repository = outbox_repository
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Handle campaign status change event"""
        try:
            if not self.campaign_repository or not self.outbox_repository:
                logger.warning("Repositories not available - event will be logged only")
                logger.info(f"Campaign status change event data: {event_data}")
                return
                
            aggregate_id = event_data.get("aggregate_id")
            new_status = self._get_new_status(event_data.get("event_type"))
            
            if not aggregate_id or not new_status:
                logger.warning(f"Invalid event data: {event_data}")
                return
            
            # Get existing campaign
            campaign = self.campaign_repository.get_by_id(aggregate_id)
            if not campaign:
                logger.warning(f"Campaign {aggregate_id} not found for status change")
                return
            
            # Update campaign status
            updates = {
                "estado": new_status,
                "fecha_ultima_actividad": datetime.utcnow()
            }
            self.campaign_repository.update(aggregate_id, updates)
            
            # Save to outbox for event publishing
            outbox_event = {
                "aggregate_id": aggregate_id,
                "aggregate_type": "Campaign",
                "event_type": event_data.get("event_type"),
                "payload": json.dumps(event_data, default=str),
                "status": "PENDING"
            }
            self.outbox_repository.save(outbox_event)
            
            logger.info(f"Campaign {aggregate_id} status changed to {new_status}")
            
        except Exception as e:
            logger.error(f"Error handling campaign status change event: {e}")
            raise
    
    def _get_new_status(self, event_type: str) -> str:
        """Map event type to new status"""
        status_mapping = {
            "CampaignActivated": "activa",
            "CampaignPaused": "pausada",
            "CampaignFinalized": "finalizada"
        }
        return status_mapping.get(event_type, "borrador")
