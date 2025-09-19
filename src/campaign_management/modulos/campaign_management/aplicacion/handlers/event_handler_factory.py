"""Factory for creating event handlers"""

import logging
from typing import Dict, Any

from campaign_management.seedwork.aplicacion.event_handlers import EventHandler
from campaign_management.modulos.campaign_management.aplicacion.handlers.campaign_read_event_handlers import CampaignReadEventHandler

logger = logging.getLogger(__name__)

class EventHandlerFactory:
    """Factory for creating event handlers"""
    
    @staticmethod
    def create_campaign_read_event_handler() -> EventHandler:
        """Create a campaign read event handler"""
        # For now, we'll create a simple handler that logs events
        # In a full implementation, this would use repository interfaces
        return CampaignReadEventHandler(None)  # TODO: Inject repository
    
    @staticmethod
    def handle_event(event_data: Dict[str, Any]) -> None:
        """Handle an event using the appropriate handler"""
        try:
            event_type = event_data.get("event_type")
            logger.info(f"Handling event: {event_type}")
            
            if event_type in ["CampaignCreated", "CampaignActivated", "CampaignPaused", "CampaignFinalized"]:
                handler = EventHandlerFactory.create_campaign_read_event_handler()
                handler.handle(event_data)
            else:
                logger.info(f"No handler for event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            logger.error(f"Event data: {event_data}")
