"""Servicio de Consumo de Eventos

En este archivo se define el servicio principal para consumir eventos de Pulsar

"""

import json
import logging
import threading
from typing import Dict, Any
from campaign_management.infraestructura.pulsar import PulsarEventConsumer, PulsarConfig

logger = logging.getLogger(__name__)

class EventConsumerService:
    def __init__(self):
        self.config = PulsarConfig()
        self.consumers = {}
        self.running = False
        
    def start_consuming(self):
        """Inicia el consumo de eventos para todos los módulos"""
        self.running = True
        
        # Eventos de campañas
        self._start_consumer('campaign-events', self._handle_campaign_event)
        
        logger.info("Servicio de consumo de eventos iniciado")
    
    def stop_consuming(self):
        """Detiene el consumo de eventos"""
        self.running = False
        for consumer in self.consumers.values():
            consumer.close()
        logger.info("Servicio de consumo de eventos detenido")
    
    def _start_consumer(self, event_type: str, handler):
        """Inicia un consumidor para un tipo específico de evento"""
        try:
            consumer = PulsarEventConsumer()
            topic_name = self.config.get_topic_name(event_type)
            subscription_name = f"{event_type}-subscription"
            consumer.subscribe_to_topic(topic_name, subscription_name, handler)
            self.consumers[event_type] = consumer
            logger.info(f"Consumidor iniciado para {event_type}")
        except Exception as e:
            logger.error(f"Error iniciando consumidor para {event_type}: {e}")
    
    def _handle_campaign_event(self, event_data: Dict[str, Any]):
        """Maneja eventos de campañas"""
        try:
            event_type = event_data.get('event_type')
            event_payload = event_data.get('event_data', {})
            
            logger.info(f"Procesando evento de campaña: {event_type}")
            
            # Aquí se pueden agregar lógicas específicas para cada tipo de evento
            if event_type == 'CampanaCreada':
                self._process_campana_creada(event_payload)
            elif event_type == 'CampanaActivada':
                self._process_campana_activada(event_payload)
            elif event_type == 'CampanaPausada':
                self._process_campana_pausada(event_payload)
            elif event_type == 'CampanaFinalizada':
                self._process_campana_finalizada(event_payload)
                
        except Exception as e:
            logger.error(f"Error procesando evento de campaña: {e}")
    
    # Métodos de procesamiento específicos para cada evento
    def _process_campana_creada(self, payload):
        logger.info(f"Campaña creada: {payload.get('id_campana')}")
    
    def _process_campana_activada(self, payload):
        logger.info(f"Campaña activada: {payload.get('id_campana')}")
    
    def _process_campana_pausada(self, payload):
        logger.info(f"Campaña pausada: {payload.get('id_campana')}")
    
    def _process_campana_finalizada(self, payload):
        logger.info(f"Campaña finalizada: {payload.get('id_campana')}")

# Instancia global del servicio
event_consumer_service = EventConsumerService()
