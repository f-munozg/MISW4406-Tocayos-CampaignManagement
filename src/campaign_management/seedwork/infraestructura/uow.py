"""Unidad de Trabajo con integración de Pulsar

En este archivo se define la Unidad de Trabajo con publicación de eventos

"""

from abc import ABC, abstractmethod
from typing import List, Callable, Any
from campaign_management.seedwork.dominio.eventos import EventoDominio
from campaign_management.infraestructura.pulsar import pulsar_publisher
import logging

logger = logging.getLogger(__name__)

class Batch:
    def __init__(self, operacion: Callable, *args, **kwargs):
        self.operacion = operacion
        self.args = args
        self.kwargs = kwargs

class UnidadTrabajo(ABC):
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.rollback()
    
    @abstractmethod
    def _limpiar_batches(self):
        raise NotImplementedError
    
    @abstractmethod
    def batches(self) -> List[Batch]:
        raise NotImplementedError
    
    @abstractmethod
    def agregar_batch(self, operacion: Callable, *args, **kwargs):
        raise NotImplementedError
    
    @abstractmethod
    def commit(self):
        raise NotImplementedError
    
    @abstractmethod
    def rollback(self):
        raise NotImplementedError
    
    @abstractmethod
    def savepoint(self):
        raise NotImplementedError
    
    @abstractmethod
    def rollback_to_savepoint(self, savepoint):
        raise NotImplementedError

class UnidadTrabajoPuerto:
    
    @staticmethod
    def commit():
        uow = UnidadTrabajoPuerto._uow
        uow.commit()
        UnidadTrabajoPuerto._limpiar_batches()
        UnidadTrabajoPuerto._publicar_eventos()
    
    @staticmethod
    def rollback():
        uow = UnidadTrabajoPuerto._uow
        uow.rollback()
        UnidadTrabajoPuerto._limpiar_batches()
    
    @staticmethod
    def savepoint():
        uow = UnidadTrabajoPuerto._uow
        return uow.savepoint()
    
    @staticmethod
    def rollback_to_savepoint(savepoint):
        uow = UnidadTrabajoPuerto._uow
        uow.rollback_to_savepoint(savepoint)
        UnidadTrabajoPuerto._limpiar_batches()
    
    @staticmethod
    def dar_batches():
        uow = UnidadTrabajoPuerto._uow
        return uow.batches()
    
    @staticmethod
    def agregar_batch(operacion: Callable, *args, **kwargs):
        uow = UnidadTrabajoPuerto._uow
        uow.agregar_batch(operacion, *args, **kwargs)
    
    @staticmethod
    def _limpiar_batches():
        uow = UnidadTrabajoPuerto._uow
        uow._limpiar_batches()
    
    @staticmethod
    def _publicar_eventos():
        """Publica todos los eventos pendientes en Pulsar"""
        try:
            eventos_pendientes = UnidadTrabajoPuerto._eventos_pendientes.copy()
            UnidadTrabajoPuerto._eventos_pendientes.clear()
            
            for evento, event_type in eventos_pendientes:
                pulsar_publisher.publish_event(evento, event_type)
                logger.info(f"Evento publicado en Pulsar: {evento.__class__.__name__}")
                
        except Exception as e:
            logger.error(f"Error publicando eventos en Pulsar: {e}")
            # Re-agregar eventos fallidos para reintento posterior
            for evento, event_type in eventos_pendientes:
                UnidadTrabajoPuerto._eventos_pendientes.append((evento, event_type))
    
    @staticmethod
    def agregar_evento(evento: EventoDominio, event_type: str):
        """Agrega un evento para ser publicado después del commit"""
        UnidadTrabajoPuerto._eventos_pendientes.append((evento, event_type))
        logger.info(f"Evento agregado para publicación: {evento.__class__.__name__}")

# Variables de clase para el estado global
UnidadTrabajoPuerto._uow = None
UnidadTrabajoPuerto._eventos_pendientes: List[tuple] = []

def set_unidad_trabajo(uow: UnidadTrabajo):
    """Establece la unidad de trabajo actual"""
    UnidadTrabajoPuerto._uow = uow
