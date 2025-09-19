"""SQLAlchemy implementations of repository interfaces"""

import logging
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

from campaign_management.seedwork.infraestructura.repositories import (
    CampaignRepository, 
    OutboxRepository, 
    CampaignReadRepository
)
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel
from campaign_management.modulos.campaign_management.infraestructura.modelos_read import CampanaReadDBModel
from campaign_management.infraestructura.outbox.model import OutboxEvent

logger = logging.getLogger(__name__)

class SQLAlchemyCampaignRepository(CampaignRepository):
    """SQLAlchemy implementation of CampaignRepository"""
    
    def __init__(self, session):
        self.session = session
    
    def get_by_id(self, campaign_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get campaign by ID"""
        try:
            campaign = self.session.get(CampanaDBModel, campaign_id)
            if campaign:
                return self._model_to_dict(campaign)
            return None
        except Exception as e:
            logger.error(f"Error getting campaign {campaign_id}: {e}")
            raise
    
    def save(self, campaign_data: Dict[str, Any]) -> None:
        """Save campaign"""
        try:
            campaign = self._dict_to_model(campaign_data)
            self.session.add(campaign)
            self.session.flush()  # Flush to get the ID
            logger.info(f"Campaign {campaign.id} saved successfully")
        except Exception as e:
            logger.error(f"Error saving campaign: {e}")
            self.session.rollback()
            raise
    
    def update(self, campaign_id: uuid.UUID, updates: Dict[str, Any]) -> None:
        """Update campaign"""
        try:
            campaign = self.session.get(CampanaDBModel, campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            for key, value in updates.items():
                if hasattr(campaign, key):
                    setattr(campaign, key, value)
            
            campaign.fecha_actualizacion = datetime.utcnow()
            self.session.add(campaign)
            logger.info(f"Campaign {campaign_id} updated successfully")
        except Exception as e:
            logger.error(f"Error updating campaign {campaign_id}: {e}")
            self.session.rollback()
            raise
    
    def delete(self, campaign_id: uuid.UUID) -> None:
        """Delete campaign"""
        try:
            campaign = self.session.get(CampanaDBModel, campaign_id)
            if campaign:
                self.session.delete(campaign)
                logger.info(f"Campaign {campaign_id} deleted successfully")
            else:
                logger.warning(f"Campaign {campaign_id} not found for deletion")
        except Exception as e:
            logger.error(f"Error deleting campaign {campaign_id}: {e}")
            self.session.rollback()
            raise
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all campaigns"""
        try:
            campaigns = self.session.query(CampanaDBModel).all()
            return [self._model_to_dict(campaign) for campaign in campaigns]
        except Exception as e:
            logger.error(f"Error getting all campaigns: {e}")
            raise
    
    def _model_to_dict(self, campaign: CampanaDBModel) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": campaign.id,
            "id_marca": campaign.id_marca,
            "nombre": campaign.nombre,
            "descripcion": campaign.descripcion,
            "tipo_campana": campaign.tipo_campana,
            "objetivo": campaign.objetivo,
            "estado": campaign.estado,
            "fecha_inicio": campaign.fecha_inicio,
            "fecha_fin": campaign.fecha_fin,
            "presupuesto_total": campaign.presupuesto_total,
            "presupuesto_utilizado": campaign.presupuesto_utilizado,
            "meta_ventas": campaign.meta_ventas,
            "ventas_actuales": campaign.ventas_actuales,
            "meta_engagement": campaign.meta_engagement,
            "engagement_actual": campaign.engagement_actual,
            "target_audiencia": campaign.target_audiencia,
            "canales_distribucion": campaign.canales_distribucion,
            "terminos_condiciones": campaign.terminos_condiciones,
            "fecha_creacion": campaign.fecha_creacion,
            "fecha_ultima_actividad": campaign.fecha_ultima_actividad,
            "fecha_actualizacion": campaign.fecha_actualizacion
        }
    
    def _dict_to_model(self, data: Dict[str, Any]) -> CampanaDBModel:
        """Convert dictionary to model"""
        return CampanaDBModel(
            id=data.get("id"),
            id_marca=data.get("id_marca"),
            nombre=data.get("nombre"),
            descripcion=data.get("descripcion"),
            tipo_campana=data.get("tipo_campana"),
            objetivo=data.get("objetivo"),
            estado=data.get("estado"),
            fecha_inicio=data.get("fecha_inicio"),
            fecha_fin=data.get("fecha_fin"),
            presupuesto_total=data.get("presupuesto_total", 0.0),
            presupuesto_utilizado=data.get("presupuesto_utilizado", 0.0),
            meta_ventas=data.get("meta_ventas", 0),
            ventas_actuales=data.get("ventas_actuales", 0),
            meta_engagement=data.get("meta_engagement", 0),
            engagement_actual=data.get("engagement_actual", 0),
            target_audiencia=data.get("target_audiencia"),
            canales_distribucion=data.get("canales_distribucion"),
            terminos_condiciones=data.get("terminos_condiciones")
        )


class SQLAlchemyOutboxRepository(OutboxRepository):
    """SQLAlchemy implementation of OutboxRepository"""
    
    def __init__(self, session):
        self.session = session
    
    def save(self, outbox_data: Dict[str, Any]) -> None:
        """Save outbox event"""
        try:
            outbox_event = self._dict_to_model(outbox_data)
            self.session.add(outbox_event)
            self.session.flush()  # Flush to get the ID
            logger.info(f"Outbox event {outbox_event.id} saved successfully")
        except Exception as e:
            logger.error(f"Error saving outbox event: {e}")
            self.session.rollback()
            raise
    
    def get_pending_events(self) -> List[Dict[str, Any]]:
        """Get pending outbox events"""
        try:
            events = self.session.query(OutboxEvent).filter(
                OutboxEvent.status == 'PENDING'
            ).all()
            return [self._model_to_dict(event) for event in events]
        except Exception as e:
            logger.error(f"Error getting pending outbox events: {e}")
            raise
    
    def mark_as_published(self, event_id: uuid.UUID) -> None:
        """Mark outbox event as published"""
        try:
            event = self.session.get(OutboxEvent, event_id)
            if event:
                event.status = 'PUBLISHED'
                event.published_at = datetime.utcnow()
                self.session.add(event)
                logger.info(f"Outbox event {event_id} marked as published")
            else:
                logger.warning(f"Outbox event {event_id} not found")
        except Exception as e:
            logger.error(f"Error marking outbox event {event_id} as published: {e}")
            self.session.rollback()
            raise
    
    def mark_as_failed(self, event_id: uuid.UUID, error_message: str = None) -> None:
        """Mark outbox event as failed"""
        try:
            event = self.session.get(OutboxEvent, event_id)
            if event:
                event.status = 'FAILED'
                event.attempts += 1
                self.session.add(event)
                logger.info(f"Outbox event {event_id} marked as failed")
            else:
                logger.warning(f"Outbox event {event_id} not found")
        except Exception as e:
            logger.error(f"Error marking outbox event {event_id} as failed: {e}")
            self.session.rollback()
            raise
    
    def _model_to_dict(self, event: OutboxEvent) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": event.id,
            "aggregate_id": event.aggregate_id,
            "aggregate_type": event.aggregate_type,
            "event_type": event.event_type,
            "payload": event.payload,
            "occurred_at": event.occurred_at,
            "published_at": event.published_at,
            "status": event.status,
            "attempts": event.attempts
        }
    
    def _dict_to_model(self, data: Dict[str, Any]) -> OutboxEvent:
        """Convert dictionary to model"""
        return OutboxEvent(
            id=data.get("id"),
            aggregate_id=data.get("aggregate_id"),
            aggregate_type=data.get("aggregate_type", "Campaign"),
            event_type=data.get("event_type"),
            payload=data.get("payload"),
            status=data.get("status", "PENDING"),
            attempts=data.get("attempts", 0)
        )


class SQLAlchemyCampaignReadRepository(CampaignReadRepository):
    """SQLAlchemy implementation of CampaignReadRepository"""
    
    def __init__(self, session):
        self.session = session
    
    def get_by_id(self, campaign_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get campaign read model by ID"""
        try:
            campaign = self.session.get(CampanaReadDBModel, campaign_id)
            if campaign:
                return self._model_to_dict(campaign)
            return None
        except Exception as e:
            logger.error(f"Error getting campaign read model {campaign_id}: {e}")
            raise
    
    def save(self, campaign_data: Dict[str, Any]) -> None:
        """Save campaign read model"""
        try:
            campaign = self._dict_to_model(campaign_data)
            self.session.add(campaign)
            self.session.flush()  # Flush to get the ID
            logger.info(f"Campaign read model {campaign.id} saved successfully")
        except Exception as e:
            logger.error(f"Error saving campaign read model: {e}")
            self.session.rollback()
            raise
    
    def update(self, campaign_id: uuid.UUID, updates: Dict[str, Any]) -> None:
        """Update campaign read model"""
        try:
            campaign = self.session.get(CampanaReadDBModel, campaign_id)
            if not campaign:
                raise ValueError(f"Campaign read model {campaign_id} not found")
            
            for key, value in updates.items():
                if hasattr(campaign, key):
                    setattr(campaign, key, value)
            
            self.session.add(campaign)
            logger.info(f"Campaign read model {campaign_id} updated successfully")
        except Exception as e:
            logger.error(f"Error updating campaign read model {campaign_id}: {e}")
            self.session.rollback()
            raise
    
    def delete(self, campaign_id: uuid.UUID) -> None:
        """Delete campaign read model"""
        try:
            campaign = self.session.get(CampanaReadDBModel, campaign_id)
            if campaign:
                self.session.delete(campaign)
                logger.info(f"Campaign read model {campaign_id} deleted successfully")
            else:
                logger.warning(f"Campaign read model {campaign_id} not found for deletion")
        except Exception as e:
            logger.error(f"Error deleting campaign read model {campaign_id}: {e}")
            self.session.rollback()
            raise
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all campaign read models"""
        try:
            campaigns = self.session.query(CampanaReadDBModel).all()
            return [self._model_to_dict(campaign) for campaign in campaigns]
        except Exception as e:
            logger.error(f"Error getting all campaign read models: {e}")
            raise
    
    def _model_to_dict(self, campaign: CampanaReadDBModel) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": campaign.id,
            "id_marca": campaign.id_marca,
            "nombre": campaign.nombre,
            "tipo_campana": campaign.tipo_campana,
            "estado": campaign.estado,
            "fecha_inicio": campaign.fecha_inicio,
            "fecha_fin": campaign.fecha_fin,
            "presupuesto_total": campaign.presupuesto_total,
            "presupuesto_utilizado": campaign.presupuesto_utilizado,
            "meta_ventas": campaign.meta_ventas,
            "ventas_actuales": campaign.ventas_actuales,
            "meta_engagement": campaign.meta_engagement,
            "engagement_actual": campaign.engagement_actual,
            "last_version": campaign.last_version,
            "fecha_ultima_actividad": campaign.fecha_ultima_actividad
        }
    
    def _dict_to_model(self, data: Dict[str, Any]) -> CampanaReadDBModel:
        """Convert dictionary to model"""
        return CampanaReadDBModel(
            id=data.get("id"),
            id_marca=data.get("id_marca"),
            nombre=data.get("nombre"),
            tipo_campana=data.get("tipo_campana"),
            estado=data.get("estado"),
            fecha_inicio=data.get("fecha_inicio"),
            fecha_fin=data.get("fecha_fin"),
            presupuesto_total=data.get("presupuesto_total", 0.0),
            presupuesto_utilizado=data.get("presupuesto_utilizado", 0.0),
            meta_ventas=data.get("meta_ventas", 0),
            ventas_actuales=data.get("ventas_actuales", 0),
            meta_engagement=data.get("meta_engagement", 0),
            engagement_actual=data.get("engagement_actual", 0),
            last_version=data.get("last_version", 0),
            fecha_ultima_actividad=data.get("fecha_ultima_actividad")
        )
