"""Comandos para la gestión de campañas

En este archivo se definen los comandos para la gestión de campañas

"""

from dataclasses import dataclass
from campaign_management.seedwork.aplicacion.comandos import Comando
from campaign_management.modulos.campaign_management.dominio.entidades import TipoCampana, EstadoCampana, ObjetivoCampana
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class CrearCampana(Comando):
    id: str
    saga_id: str
    id_marca: str
    nombre: str
    tipo_campana: str

    descripcion: str = ""
    objetivo: str = ""
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    presupuesto_total: Optional[float] = None
    meta_ventas: Optional[int] = None
    meta_engagement: Optional[int] = None
    target_audiencia: Optional[str] = None
    canales_distribucion: Optional[str] = None
    terminos_condiciones: Optional[str] = None
    fecha_creacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None

@dataclass
class ProgramarCampana(Comando):
    id_campana: str
    fecha_inicio: str
    fecha_fin: str
    fecha_actualizacion: Optional[str] = None

@dataclass
class ActivarCampana(Comando):
    id_campana: str
    fecha_actualizacion: Optional[str] = None

@dataclass
class PausarCampana(Comando):
    id_campana: str
    motivo: str = ""
    fecha_actualizacion: Optional[str] = None

@dataclass
class FinalizarCampana(Comando):
    id_campana: str
    motivo: str = ""
    fecha_actualizacion:Optional[str] = None

@dataclass
class CancelarCampana(Comando):
    id_campana: str
    saga_id: str
    motivo: str = ""
    fecha_actualizacion:Optional[str] = None

@dataclass
class ActualizarMetricasCampana(Comando):
    id_campana: str
    ventas: int = 0
    engagement: int = 0
    presupuesto_utilizado: float = 0.0
    fecha_actualizacion: Optional[str] = None
