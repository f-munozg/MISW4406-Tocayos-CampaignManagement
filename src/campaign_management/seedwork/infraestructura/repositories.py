from abc import ABC, abstractmethod
from typing import Optional, List, Any
from uuid import UUID

class Repository(ABC):
    """Base repository interface"""
    pass

class CampaignRepository(Repository):
    """Port for campaign repository operations"""
    
    @abstractmethod
    def get_by_id(self, campaign_id: UUID) -> Optional[Any]:
        """Get campaign by ID"""
        raise NotImplementedError()
    
    @abstractmethod
    def save(self, campaign: Any) -> None:
        """Save campaign"""
        raise NotImplementedError()
    
    @abstractmethod
    def update(self, campaign: Any) -> None:
        """Update campaign"""
        raise NotImplementedError()

class CampaignReadRepository(Repository):
    """Port for campaign read model repository operations"""
    
    @abstractmethod
    def get_by_id(self, campaign_id: UUID) -> Optional[Any]:
        """Get campaign read model by ID"""
        raise NotImplementedError()
    
    @abstractmethod
    def save(self, campaign: Any) -> None:
        """Save campaign read model"""
        raise NotImplementedError()
    
    @abstractmethod
    def update(self, campaign: Any) -> None:
        """Update campaign read model"""
        raise NotImplementedError()
    
    @abstractmethod
    def get_by_marca(self, marca_id: UUID) -> List[Any]:
        """Get campaigns by marca ID"""
        raise NotImplementedError()
    
    @abstractmethod
    def get_by_estado(self, estado: str) -> List[Any]:
        """Get campaigns by estado"""
        raise NotImplementedError()

class OutboxRepository(Repository):
    """Port for outbox repository operations"""
    
    @abstractmethod
    def save(self, outbox_event: Any) -> None:
        """Save outbox event"""
        raise NotImplementedError()
    
    @abstractmethod
    def get_pending_events(self, limit: int = 100) -> List[Any]:
        """Get pending outbox events"""
        raise NotImplementedError()
    
    @abstractmethod
    def mark_as_published(self, event_id: UUID) -> None:
        """Mark event as published"""
        raise NotImplementedError()
    
    @abstractmethod
    def mark_as_failed(self, event_id: UUID) -> None:
        """Mark event as failed"""
        raise NotImplementedError()
