"""Factory for creating event handlers"""

import logging
from typing import Dict, Any, Optional

from campaign_management.seedwork.aplicacion.event_handlers import EventHandler
from campaign_management.modulos.campaign_management.aplicacion.handlers.campaign_read_event_handlers import CampaignReadEventHandler
from campaign_management.modulos.campaign_management.aplicacion.handlers.campaign_event_handlers import (
    CampaignCreatedEventHandler, 
    CampaignStatusChangedEventHandler
)
from campaign_management.infraestructura.repositories import (
    SQLAlchemyCampaignRepository,
    SQLAlchemyOutboxRepository,
    SQLAlchemyCampaignReadRepository
)
from campaign_management.config.db import db

logger = logging.getLogger(__name__)

class EventHandlerFactory:
    """Factory for creating event handlers"""
    
    @staticmethod
    def create_campaign_read_event_handler() -> EventHandler:
        """Create a campaign read event handler with repository"""
        try:
            campaign_read_repository = SQLAlchemyCampaignReadRepository(db.session)
            return CampaignReadEventHandler(campaign_read_repository)
        except Exception as e:
            logger.error(f"Error creating campaign read event handler: {e}")
            return CampaignReadEventHandler(None)  # Fallback to None repository
    
    @staticmethod
    def create_campaign_event_handler() -> EventHandler:
        """Create a campaign event handler with repositories"""
        try:
            campaign_repository = SQLAlchemyCampaignRepository(db.session)
            outbox_repository = SQLAlchemyOutboxRepository(db.session)
            return CampaignCreatedEventHandler(campaign_repository, outbox_repository)
        except Exception as e:
            logger.error(f"Error creating campaign event handler: {e}")
            return CampaignCreatedEventHandler(None, None)  # Fallback to None repositories
    
    @staticmethod
    def create_campaign_status_change_handler() -> EventHandler:
        """Create a campaign status change event handler with repositories"""
        try:
            campaign_repository = SQLAlchemyCampaignRepository(db.session)
            outbox_repository = SQLAlchemyOutboxRepository(db.session)
            return CampaignStatusChangedEventHandler(campaign_repository, outbox_repository)
        except Exception as e:
            logger.error(f"Error creating campaign status change handler: {e}")
            return CampaignStatusChangedEventHandler(None, None)  # Fallback to None repositories
    
    @staticmethod
    def handle_event(event_data: Dict[str, Any]) -> None:
        """Handle an event using the appropriate handler"""
        try:
            event_type = event_data.get("event_type")
            logger.info(f"Handling event: {event_type}")
            
            if event_type == "CampaignCreated":
                # Handle with both write model and read model handlers
                try:
                    # Write model handler (saves to campaigns table and outbox)
                    write_handler = EventHandlerFactory.create_campaign_event_handler()
                    write_handler.handle(event_data)
                    logger.info(f"CampaignCreated event handled by write model handler")
                except Exception as e:
                    logger.error(f"Error in write model handler: {e}")
                
                try:
                    # Read model handler (saves to campaigns_read table)
                    read_handler = EventHandlerFactory.create_campaign_read_event_handler()
                    read_handler.handle(event_data)
                    logger.info(f"CampaignCreated event handled by read model handler")
                except Exception as e:
                    logger.error(f"Error in read model handler: {e}")
                    
            elif event_type in ["CampaignActivated", "CampaignPaused", "CampaignFinalized"]:
                # Handle with both write model and read model handlers
                try:
                    # Write model handler (updates campaigns table and outbox)
                    write_handler = EventHandlerFactory.create_campaign_status_change_handler()
                    write_handler.handle(event_data)
                    logger.info(f"{event_type} event handled by write model handler")
                except Exception as e:
                    logger.error(f"Error in write model handler: {e}")
                
                try:
                    # Read model handler (updates campaigns_read table)
                    read_handler = EventHandlerFactory.create_campaign_read_event_handler()
                    read_handler.handle(event_data)
                    logger.info(f"{event_type} event handled by read model handler")
                except Exception as e:
                    logger.error(f"Error in read model handler: {e}")
            else:
                logger.info(f"No handler for event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            logger.error(f"Event data: {event_data}")
