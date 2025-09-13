"""Queries para la gestión de campañas

En este archivo se definen las queries para la gestión de campañas

"""

from dataclasses import dataclass
from abc import ABC, abstractmethod

class Query:
    ...

class QueryHandler(ABC):
    @abstractmethod
    def handle(self, query: Query):
        raise NotImplementedError()

@dataclass
class ObtenerCampana(Query):
    id_campana: str

@dataclass
class ObtenerCampanasPorMarca(Query):
    id_marca: str

@dataclass
class ObtenerCampanasPorTipo(Query):
    tipo_campana: str

@dataclass
class ObtenerCampanasPorEstado(Query):
    estado: str

@dataclass
class ObtenerCampanasActivas(Query):
    pass

@dataclass
class ObtenerCampanasPorObjetivo(Query):
    objetivo: str

@dataclass
class ObtenerCampanasPorRangoFechas(Query):
    fecha_inicio: str
    fecha_fin: str

@dataclass
class ObtenerCampanasPorPresupuesto(Query):
    presupuesto_minimo: float
    presupuesto_maximo: float
