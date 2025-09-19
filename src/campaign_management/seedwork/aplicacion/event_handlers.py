from abc import ABC, abstractmethod
from typing import Dict, Any

class EventHandler(ABC):
    """Port for handling domain events"""
    
    @abstractmethod
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Handle a domain event"""
        raise NotImplementedError()

class EventConsumer(ABC):
    """Port for consuming events from external sources"""
    
    @abstractmethod
    def start_consuming(self) -> None:
        """Start consuming events"""
        raise NotImplementedError()
    
    @abstractmethod
    def stop_consuming(self) -> None:
        """Stop consuming events"""
        raise NotImplementedError()
