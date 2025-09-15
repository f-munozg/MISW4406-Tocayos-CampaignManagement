"""Queries para la gestión de campañas

En este archivo se definen las queries para la gestión de campañas
"""

from dataclasses import dataclass

@dataclass
class ObtenerCampana:
    id_campana: str

@dataclass
class ObtenerCampanasPorMarca:
    id_marca: str

@dataclass
class ObtenerCampanasPorTipo:
    tipo_campana: str

@dataclass
class ObtenerCampanasPorEstado:
    estado: str

@dataclass
class ObtenerCampanasActivas:
    pass