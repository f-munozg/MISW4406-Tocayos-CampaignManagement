"""DTOs para la gestión de campañas

En este archivo se definen los DTOs para la gestión de campañas

"""

from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class CampanaDTO:
    id: str
    id_marca: str
    nombre: str
    descripcion: str = ""
    tipo_campana: str = "afiliacion"
    objetivo: str = "ventas"
    estado: str = "borrador"
    fecha_inicio: str = ""
    fecha_fin: str = ""
    presupuesto_total: float = 0.0
    presupuesto_utilizado: float = 0.0
    meta_ventas: int = 0
    ventas_actuales: int = 0
    meta_engagement: int = 0
    engagement_actual: int = 0
    target_audiencia: str = ""
    canales_distribucion: str = ""
    terminos_condiciones: str = ""
    fecha_creacion: str = ""
    fecha_ultima_actividad: str = ""
    fecha_actualizacion: str = ""
