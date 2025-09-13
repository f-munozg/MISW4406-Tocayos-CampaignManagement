"""Modelos de base de datos para campañas

En este archivo se definen los modelos de base de datos para campañas

"""

from campaign_management.config.db import db
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from enum import Enum as PyEnum

class TipoCampanaEnum(PyEnum):
    AFILIACION = "afiliacion"
    INFLUENCER = "influencer"
    LEALTAD = "lealtad"
    B2B = "b2b"
    MIXTA = "mixta"

class EstadoCampanaEnum(PyEnum):
    BORRADOR = "borrador"
    PROGRAMADA = "programada"
    ACTIVA = "activa"
    PAUSADA = "pausada"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"

class ObjetivoCampanaEnum(PyEnum):
    VENTAS = "ventas"
    BRAND_AWARENESS = "brand_awareness"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"
    CONVERSION = "conversion"

class CampanaDBModel(db.Model):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_marca = Column(UUID(as_uuid=True), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo_campana = Column(String(50), nullable=False)
    objetivo = Column(String(50), nullable=False)
    estado = Column(String(50), nullable=False, default='borrador')
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    presupuesto_total = Column(Float, nullable=False, default=0.0)
    presupuesto_utilizado = Column(Float, nullable=False, default=0.0)
    meta_ventas = Column(Integer, nullable=False, default=0)
    ventas_actuales = Column(Integer, nullable=False, default=0)
    meta_engagement = Column(Integer, nullable=False, default=0)
    engagement_actual = Column(Integer, nullable=False, default=0)
    target_audiencia = Column(Text, nullable=True)
    canales_distribucion = Column(Text, nullable=True)
    terminos_condiciones = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_ultima_actividad = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Campana {self.nombre} ({self.estado})>"
