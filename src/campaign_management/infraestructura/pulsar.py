"""Configuración de Pulsar para eventos

En este archivo se define la configuración y utilidades para Pulsar

"""

import os
import json
import logging
from typing import Dict, Any
from pulsar import Client, Producer, Consumer
from campaign_management.seedwork.dominio.eventos import EventoDominio

logger = logging.getLogger(__name__)

class PulsarConfig:
    def __init__(self):
        self.service_url = os.getenv('PULSAR_SERVICE_URL', 'pulsar://localhost:6650')
        self.admin_url = os.getenv('PULSAR_ADMIN_URL', 'http://localhost:8080')        
        self.tenant = 'campaign-management'
        self.namespace = 'events'
        
    def get_topic_name(self, event_type: str) -> str:
        """Genera el nombre del topic basado en el tipo de evento"""
        if event_type.startswith('content'):
            return f"persistent://content-management/{self.namespace}/{event_type}"

        return f"persistent://{self.tenant}/{self.namespace}/{event_type}"

class PulsarEventPublisher:
    def __init__(self):
        self.config = PulsarConfig()
        self.client = None
        self.producers: Dict[str, Producer] = {}
        
    def _get_client(self) -> Client:
        """Obtiene o crea el cliente de Pulsar"""
        if self.client is None:
            self.client = Client(self.config.service_url)
        return self.client
    
    def _get_producer(self, topic_name: str) -> Producer:
        """Obtiene o crea un producer para el topic especificado"""
        if topic_name not in self.producers:
            client = self._get_client()
            self.producers[topic_name] = client.create_producer(topic_name)
        return self.producers[topic_name]
    
    def publish_event(self, evento: EventoDominio, event_type: str):
        """Publica un evento en Pulsar"""
        try:
            topic_name = self.config.get_topic_name(event_type)
            producer = self._get_producer(topic_name)
            
            # Serializar el evento
            event_data = self._serialize_event(evento)

            if event_type == 'campaign-events':
                event_data = self._alternate_serialize_event(evento)
            
            # Publicar el evento
            producer.send(event_data.encode('utf-8'))
            logger.info(f"Evento publicado en {topic_name}: {evento.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Error publicando evento en Pulsar: {e}")
            raise
    
    def _serialize_event(self, evento: EventoDominio) -> str:
        """Serializa un evento a JSON"""
        event_dict = {
            'event_type': evento.__class__.__name__,
            'event_data': evento.__dict__,
            'timestamp': evento.fecha_evento.isoformat() if hasattr(evento, 'fecha_evento') else None
        }
        return json.dumps(event_dict, default=str)
    
    def _alternate_serialize_event(self, evento: EventoDominio) -> str:
        """Serializa un evento a JSON alternativo"""
        event_dict = {
            'event_type': evento.__class__.__name__,
            'event_data': evento.__dict__,
            'timestamp': evento.fecha_evento.isoformat() if hasattr(evento, 'fecha_evento') else None
        }

        if evento.__class__.__name__ == 'ProgramaLealtadActivado':
            event_dict['event_type'] = 'CampaignActivated'
        elif evento.__class__.__name__ == 'ProgramaLealtadRegistrado':
            event_dict['event_type'] = 'CampaignCreated'

        return json.dumps(event_dict, default=str)

    def close(self):
        """Cierra todas las conexiones"""
        for producer in self.producers.values():
            producer.close()
        if self.client:
            self.client.close()

class PulsarEventConsumer:
    def __init__(self):
        self.config = PulsarConfig()
        self.client = None
        self.consumers = {}
        
    def _get_client(self) -> Client:
        """Obtiene o crea el cliente de Pulsar"""
        if self.client is None:
            self.client = Client(self.config.service_url)
        return self.client
    
    def subscribe_to_topic(self, topic_name: str, subscription_name: str, callback):
        """Se suscribe a un topic específico"""
        try:
            client = self._get_client()
            consumer = client.subscribe(topic_name, subscription_name)
            self.consumers[topic_name] = consumer
            
            # Procesar mensajes en un hilo separado
            import threading
            thread = threading.Thread(target=self._process_messages, args=(consumer, callback))
            thread.daemon = True
            thread.start()
            
            logger.info(f"Suscrito al topic {topic_name} con subscription {subscription_name}")
            
        except Exception as e:
            logger.error(f"Error suscribiéndose al topic {topic_name}: {e}")
            raise
    
    def _process_messages(self, consumer, callback):
        """Procesa mensajes del consumer"""
        try:
            while True:
                msg = consumer.receive(timeout_millis=1000)
                try:
                    # Deserializar el mensaje
                    event_data = json.loads(msg.data().decode('utf-8'))
                    callback(event_data)
                    consumer.acknowledge(msg)
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {e}")
                    consumer.negative_acknowledge(msg)
        except Exception as e:
            logger.error(f"Error en el procesamiento de mensajes: {e}")
    
    def close(self):
        """Cierra todas las conexiones"""
        for consumer in self.consumers.values():
            consumer.close()
        if self.client:
            self.client.close()

# Instancia global del publisher
pulsar_publisher = PulsarEventPublisher()

# Instancia global del consumer
pulsar_consumer = PulsarEventConsumer()
