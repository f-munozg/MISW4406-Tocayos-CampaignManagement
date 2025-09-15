from campaign_management.config.db import db
from sqlalchemy import Column, String, DateTime, Float, Integer
from sqlalchemy.dialects.postgresql import UUID

class CampanaReadDBModel(db.Model):
    __tablename__ = "campaigns_read"

    id = Column(UUID(as_uuid=True), primary_key=True)
    id_marca = Column(UUID(as_uuid=True), nullable=False)
    nombre = Column(String(255), nullable=False)
    tipo_campana = Column(String(50), nullable=False)
    estado = Column(String(30), nullable=False, default="borrador")
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    presupuesto_total = Column(Float, nullable=False, default=0.0)
    presupuesto_utilizado = Column(Float, nullable=False, default=0.0)
    meta_ventas = Column(Integer, nullable=False, default=0)
    ventas_actuales = Column(Integer, nullable=False, default=0)
    meta_engagement = Column(Integer, nullable=False, default=0)
    engagement_actual = Column(Integer, nullable=False, default=0)

    last_version = Column(Integer, nullable=False, default=0)
    fecha_ultima_actividad = Column(DateTime, nullable=True)
