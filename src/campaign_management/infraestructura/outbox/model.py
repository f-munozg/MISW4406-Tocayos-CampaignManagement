"""Modelo para eventos de outbox

En este archivo se define el modelo para eventos de outbox
"""

from campaign_management.config.db import db
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class OutboxEvent(db.Model):
    __tablename__ = "outbox_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    aggregate_type = Column(String(50), nullable=False, default='Campaign')
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='PENDING')  # PENDING|PUBLISHED|FAILED
    attempts = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f"<OutboxEvent {self.event_type} ({self.status})>"