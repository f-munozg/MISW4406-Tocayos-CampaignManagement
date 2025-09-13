"""Comandos para la gestión de campañas

En este archivo se definen los comandos para la gestión de campañas

"""

from dataclasses import dataclass
from campaign_management.seedwork.aplicacion.comandos import Comando
from campaign_management.modulos.campaign_management.dominio.entidades import TipoCampana, EstadoCampana, ObjetivoCampana
from datetime import datetime
import uuid

@dataclass
class CrearCampana(Comando):
    id: str
    id_marca: str
    nombre: str
    descripcion: str = ""
    tipo_campana: str = "afiliacion"
    objetivo: str = "ventas"
    presupuesto_total: float = 0.0
    meta_ventas: int = 0
    meta_engagement: int = 0
    target_audiencia: str = ""
    canales_distribucion: str = ""
    terminos_condiciones: str = ""
    fecha_creacion: str = ""
    fecha_actualizacion: str = ""

@dataclass
class ProgramarCampana(Comando):
    id_campana: str
    fecha_inicio: str
    fecha_fin: str
    fecha_actualizacion: str = ""

@dataclass
class ActivarCampana(Comando):
    id_campana: str
    fecha_actualizacion: str = ""

@dataclass
class PausarCampana(Comando):
    id_campana: str
    motivo: str = ""
    fecha_actualizacion: str = ""

@dataclass
class FinalizarCampana(Comando):
    id_campana: str
    motivo: str = ""
    fecha_actualizacion: str = ""

@dataclass
class CancelarCampana(Comando):
    id_campana: str
    motivo: str = ""
    fecha_actualizacion: str = ""

@dataclass
class ActualizarMetricasCampana(Comando):
    id_campana: str
    ventas: int = 0
    engagement: int = 0
    presupuesto_utilizado: float = 0.0
    fecha_actualizacion: str = ""
