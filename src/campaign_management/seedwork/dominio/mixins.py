"""Mixins reusables parte del seedwork del proyecto

En este archivo usted encontrará los mixins reusables parte del seedwork del proyecto

"""

from abc import ABC, abstractmethod
from .reglas import ReglaNegocio, ReglaNegocioExcepcion

class ValidarReglasMixin(ABC):

    def validar_regla(self, regla: ReglaNegocio):
        if not regla.es_valido():
            raise ReglaNegocioExcepcion(regla)
