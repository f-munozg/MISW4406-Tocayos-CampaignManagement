from functools import singledispatch
from abc import ABC, abstractmethod

class Query:
    ...

class QueryHandler(ABC):
    @abstractmethod
    def handle(self, query: Query):
        raise NotImplementedError()

@singledispatch
def ejecutar_query(query):
    raise NotImplementedError(f'No existe implementación para la query de tipo {type(query).__name__}')
