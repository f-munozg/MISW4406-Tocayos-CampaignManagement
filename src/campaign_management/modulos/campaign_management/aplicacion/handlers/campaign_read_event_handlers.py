"""Event handlers for campaign read model projections"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from campaign_management.seedwork.aplicacion.event_handlers import EventHandler
from campaign_management.seedwork.infraestructura.repositories import CampaignReadRepository

logger = logging.getLogger(__name__)

class CampaignReadEventHandler(EventHandler):
    """Handles events for campaign read model projections"""
    
    def __init__(self, campaign_read_repository: CampaignReadRepository = None):
        self.campaign_read_repository = campaign_read_repository
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Handle campaign events for read model"""
        try:
            if not self.campaign_read_repository:
                logger.warning("CampaignReadRepository not available - event will be logged only")
                logger.info(f"Event data: {event_data}")
                return
                
            event_type = event_data.get("event_type")
            event_status = event_data.get("status")
            
            if event_type == "CommandCreateCampaign" and event_status == "success":
                self._handle_campaign_created(event_data)
            elif event_type in ["CampaignActivated", "CampaignPaused", "CampaignFinalized"]:
                self._handle_campaign_status_change(event_data)
            else:
                logger.info(f"Event type {event_type} ignored for read model with status {event_status}")
                
        except Exception as e:
            logger.error(f"Error handling campaign read event: {e}")
            raise
    
    def _handle_campaign_created(self, event_data: Dict[str, Any]) -> None:
        """Handle CampaignCreated event for read model"""
        # Try multiple ways to get the data structure
        data = event_data.get("data", {})
        if not data:
            data = event_data.get("event_data", {})
        if not data:
            data = event_data  # fallback to the whole event_data
        
        aggregate_id = data.get("id")
        version = int(event_data.get("version", 1))
        
        if not aggregate_id:
            logger.warning("Campaign ID not found in event data")
            return
        
        # Check if read model already exists (idempotency)
        existing = self.campaign_read_repository.get_by_id(aggregate_id)
        if existing:
            # Check version for idempotency
            if existing.get("last_version", 0) >= version:
                logger.info(f"Campaign {aggregate_id} read model already up to date")
                return
            
            # Update existing read model
            updates = {
                "nombre": data.get("nombre") or existing.get("nombre"),
                "tipo_campana": data.get("tipo_campana") or existing.get("tipo_campana"),
                "fecha_inicio": self._parse_iso(data.get("fecha_inicio")) or existing.get("fecha_inicio"),
                "fecha_fin": self._parse_iso(data.get("fecha_fin")) or existing.get("fecha_fin"),
                "last_version": version,
                "fecha_ultima_actividad": datetime.utcnow()
            }
            self.campaign_read_repository.update(aggregate_id, updates)
            return
        
        # Create new read model
        # Handle different event data structures (loyalty vs campaign events)
        read_model_data = {
            "id": aggregate_id,
            "id_marca": data.get("id_marca") or data.get("marca") or uuid.uuid4(),
            "nombre": data.get("nombre") or data.get("categoria", "Campaign"),
            "tipo_campana": data.get("tipo_campana") or data.get("tipo", "lealtad"),
            "estado": "borrador",
            "fecha_inicio": self._parse_iso(data.get("fecha_inicio") or data.get("inicio_campania")),
            "fecha_fin": self._parse_iso(data.get("fecha_fin") or data.get("final_campania")),
            "presupuesto_total": 0.0,
            "presupuesto_utilizado": 0.0,
            "meta_ventas": 0,
            "ventas_actuales": 0,
            "meta_engagement": 0,
            "engagement_actual": 0,
            "last_version": version,
            "fecha_ultima_actividad": datetime.utcnow()
        }
        
        # Set defaults for required fields
        if not read_model_data["id_marca"]:
            read_model_data["id_marca"] = uuid.uuid4()
        if not read_model_data["nombre"]:
            read_model_data["nombre"] = ""
        if not read_model_data["tipo_campana"]:
            read_model_data["tipo_campana"] = ""
        
        self.campaign_read_repository.save(read_model_data)
        logger.info(f"Campaign {aggregate_id} read model created")
    
    def _handle_campaign_status_change(self, event_data: Dict[str, Any]) -> None:
        """Handle campaign status change events for read model"""
        aggregate_id = event_data.get("aggregate_id")
        version = int(event_data.get("version", 1))
        new_status = self._get_new_status(event_data.get("event_type"))
        
        if not aggregate_id or not new_status:
            logger.warning(f"Invalid status change event data: {event_data}")
            return
        
        # Get existing read model
        read_model = self.campaign_read_repository.get_by_id(aggregate_id)
        if not read_model:
            logger.warning(f"Campaign {aggregate_id} read model not found for status change")
            return
        
        # Check version for idempotency
        if read_model.get("last_version", 0) >= version:
            logger.info(f"Campaign {aggregate_id} read model already up to date")
            return
        
        # Update read model
        updates = {
            "estado": new_status,
            "last_version": version,
            "fecha_ultima_actividad": datetime.utcnow()
        }
        
        self.campaign_read_repository.update(aggregate_id, updates)
        logger.info(f"Campaign {aggregate_id} read model status updated to {new_status}")
    
    def _get_new_status(self, event_type: str) -> str:
        """Map event type to new status"""
        status_mapping = {
            "CampaignActivated": "activa",
            "CampaignPaused": "pausada",
            "CampaignFinalized": "finalizada"
        }
        return status_mapping.get(event_type, "borrador")
    
    @staticmethod
    def _parse_iso(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
