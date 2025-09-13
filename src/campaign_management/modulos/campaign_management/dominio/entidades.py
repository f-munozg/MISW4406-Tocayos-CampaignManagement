"""Entidades del dominio de Campaign Management

En este archivo se definen las entidades del dominio para la gestión de campañas

"""

from dataclasses import dataclass, field
from enum import Enum
from campaign_management.seedwork.dominio.entidades import AgregacionRaiz
from campaign_management.seedwork.dominio.eventos import EventoDominio
from datetime import datetime
import uuid

class EstadoCampana(Enum):
    BORRADOR = "borrador"
    PROGRAMADA = "programada"
    ACTIVA = "activa"
    PAUSADA = "pausada"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"

class TipoCampana(Enum):
    AFILIACION = "afiliacion"
    INFLUENCER = "influencer"
    LEALTAD = "lealtad"
    B2B = "b2b"
    MIXTA = "mixta"

class ObjetivoCampana(Enum):
    VENTAS = "ventas"
    BRAND_AWARENESS = "brand_awareness"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"
    CONVERSION = "conversion"

@dataclass
class Campana(AgregacionRaiz):
    id_marca: uuid.UUID = field(default=None)
    nombre: str = field(default="")
    descripcion: str = field(default="")
    tipo_campana: TipoCampana = field(default=TipoCampana.AFILIACION)
    objetivo: ObjetivoCampana = field(default=ObjetivoCampana.VENTAS)
    estado: EstadoCampana = field(default=EstadoCampana.BORRADOR)
    fecha_inicio: datetime = field(default=None)
    fecha_fin: datetime = field(default=None)
    presupuesto_total: float = field(default=0.0)
    presupuesto_utilizado: float = field(default=0.0)
    meta_ventas: int = field(default=0)
    ventas_actuales: int = field(default=0)
    meta_engagement: int = field(default=0)
    engagement_actual: int = field(default=0)
    target_audiencia: str = field(default="")
    canales_distribucion: str = field(default="")
    terminos_condiciones: str = field(default="")
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_ultima_actividad: datetime = field(default_factory=datetime.now)
    
    def programar_campana(self, fecha_inicio: datetime, fecha_fin: datetime):
        if self.estado == EstadoCampana.BORRADOR:
            self.estado = EstadoCampana.PROGRAMADA
            self.fecha_inicio = fecha_inicio
            self.fecha_fin = fecha_fin
            self.fecha_ultima_actividad = datetime.now()
            self.agregar_evento(CampanaProgramada(
                id_campana=self.id,
                id_marca=self.id_marca,
                nombre=self.nombre,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                fecha_programacion=datetime.now()
            ))
    
    def activar_campana(self):
        if self.estado == EstadoCampana.PROGRAMADA:
            self.estado = EstadoCampana.ACTIVA
            self.fecha_ultima_actividad = datetime.now()
            self.agregar_evento(CampanaActivada(
                id_campana=self.id,
                id_marca=self.id_marca,
                nombre=self.nombre,
                fecha_activacion=datetime.now()
            ))
    
    def pausar_campana(self, motivo: str = ""):
        if self.estado == EstadoCampana.ACTIVA:
            self.estado = EstadoCampana.PAUSADA
            self.fecha_ultima_actividad = datetime.now()
            self.agregar_evento(CampanaPausada(
                id_campana=self.id,
                id_marca=self.id_marca,
                nombre=self.nombre,
                motivo=motivo,
                fecha_pausa=datetime.now()
            ))
    
    def finalizar_campana(self, motivo: str = ""):
        if self.estado in [EstadoCampana.ACTIVA, EstadoCampana.PAUSADA]:
            self.estado = EstadoCampana.FINALIZADA
            self.fecha_ultima_actividad = datetime.now()
            self.agregar_evento(CampanaFinalizada(
                id_campana=self.id,
                id_marca=self.id_marca,
                nombre=self.nombre,
                motivo=motivo,
                fecha_finalizacion=datetime.now()
            ))
    
    def cancelar_campana(self, motivo: str = ""):
        if self.estado in [EstadoCampana.BORRADOR, EstadoCampana.PROGRAMADA, EstadoCampana.ACTIVA, EstadoCampana.PAUSADA]:
            self.estado = EstadoCampana.CANCELADA
            self.fecha_ultima_actividad = datetime.now()
            self.agregar_evento(CampanaCancelada(
                id_campana=self.id,
                id_marca=self.id_marca,
                nombre=self.nombre,
                motivo=motivo,
                fecha_cancelacion=datetime.now()
            ))
    
    def actualizar_metricas(self, ventas: int = 0, engagement: int = 0, presupuesto_utilizado: float = 0.0):
        if self.estado == EstadoCampana.ACTIVA:
            self.ventas_actuales += ventas
            self.engagement_actual += engagement
            self.presupuesto_utilizado += presupuesto_utilizado
            self.fecha_ultima_actividad = datetime.now()
            self.agregar_evento(MetricasCampanaActualizadas(
                id_campana=self.id,
                id_marca=self.id_marca,
                nombre=self.nombre,
                ventas_actuales=self.ventas_actuales,
                engagement_actual=self.engagement_actual,
                presupuesto_utilizado=self.presupuesto_utilizado,
                fecha_actualizacion=datetime.now()
            ))

@dataclass
class CampanaCreada(EventoDominio):
    id_campana: uuid.UUID = None
    id_marca: uuid.UUID = None
    nombre: str = None
    tipo_campana: str = None
    objetivo: str = None
    fecha_creacion: datetime = None

@dataclass
class CampanaProgramada(EventoDominio):
    id_campana: uuid.UUID = None
    id_marca: uuid.UUID = None
    nombre: str = None
    fecha_inicio: datetime = None
    fecha_fin: datetime = None
    fecha_programacion: datetime = None

@dataclass
class CampanaActivada(EventoDominio):
    id_campana: uuid.UUID = None
    id_marca: uuid.UUID = None
    nombre: str = None
    fecha_activacion: datetime = None

@dataclass
class CampanaPausada(EventoDominio):
    id_campana: uuid.UUID = None
    id_marca: uuid.UUID = None
    nombre: str = None
    motivo: str = None
    fecha_pausa: datetime = None

@dataclass
class CampanaFinalizada(EventoDominio):
    id_campana: uuid.UUID = None
    id_marca: uuid.UUID = None
    nombre: str = None
    motivo: str = None
    fecha_finalizacion: datetime = None

@dataclass
class CampanaCancelada(EventoDominio):
    id_campana: uuid.UUID = None
    id_marca: uuid.UUID = None
    nombre: str = None
    motivo: str = None
    fecha_cancelacion: datetime = None

@dataclass
class MetricasCampanaActualizadas(EventoDominio):
    id_campana: uuid.UUID = None
    id_marca: uuid.UUID = None
    nombre: str = None
    ventas_actuales: int = None
    engagement_actual: int = None
    presupuesto_utilizado: float = None
    fecha_actualizacion: datetime = None
