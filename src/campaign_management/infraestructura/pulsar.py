"""Configuración de Pulsar para eventos

En este archivo se define la configuración y utilidades para Pulsar

"""

import os
import json
import uuid
import logging
import pulsar
from typing import Dict, Any
from pulsar import Client, Producer, Consumer
from campaign_management.seedwork.dominio.eventos import EventoDominio

# Try to import ConsumerType, fallback to string if not available
try:
    from pulsar import ConsumerType
except ImportError:
    # Fallback: use string values for consumer types
    class ConsumerType:
        Shared = "Shared"
        Exclusive = "Exclusive"
        Failover = "Failover"
        KeyShared = "KeyShared"

logger = logging.getLogger(__name__)

class PulsarConfig:
    def __init__(self):
        self.service_url = os.getenv('PULSAR_SERVICE_URL', 'pulsar://localhost:6650')
        self.admin_url = os.getenv('PULSAR_ADMIN_URL', 'http://localhost:8080')        
        self.tenant = 'campaign-management'
        self.namespace = 'events'
        
    def get_topic_name(self, event_type: str) -> str:
        """Genera el nombre del topic basado en el tipo de evento"""
        if event_type.startswith('loyalty'):
            return f"persistent://loyalty-management/{self.namespace}/{event_type}"

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
    
    def publish_event(self, saga_id: uuid, evento: EventoDominio, event_type: str, status: str):
        """Publica un evento en Pulsar"""
        try:
            topic_name = self.config.get_topic_name(event_type)
            producer = self._get_producer(topic_name)
            
            # Serializar el evento
            event_dict = {
                'saga_id': saga_id,
                'service': 'Campaign',
                'status': status, 
                #'event_id': evento.id,
                'event_type': event_type,
                'event_data': evento.__dict__,
                #'timestamp': evento.fecha_evento.isoformat() if hasattr(evento, 'fecha_evento') else None
            }
            event_data=json.dumps(event_dict, default=str)
            
            # Publicar el evento
            producer.send(event_data.encode('utf-8'))
            logger.info(f"Evento publicado en {topic_name}: {evento.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Error publicando evento en Pulsar: {e}")
            raise
    
    def publish_json(self, saga_id: uuid, event_data: dict, event_type: str, status: str):
        """Publica un payload JSON en Pulsar"""
        try:
            topic_name = self.config.get_topic_name(event_type)
            producer = self._get_producer(topic_name)
            
            # Serializar el payload a JSON
            if event_data is None:
                event_data = {}

            event_dict = {
                'saga_id': saga_id,
                'service': 'Campaign',
                'status': status, 
                #'event_id': evento.id,
                'event_type': "EventCampaignCreated",
                'event_data': event_data,
                #'timestamp': evento.fecha_evento.isoformat() if hasattr(evento, 'fecha_evento') else None
            }

            json_data = json.dumps(event_dict, default=str)
            
            # Crear el mensaje con key si se proporciona
            message = json_data.encode('utf-8')

            logger.info(f"Evento a publicar desde campañas {message}")
            
            if saga_id:
                # Convertir key a string si es necesario (para UUIDs, etc.)
                partition_key = str(saga_id) if saga_id is not None else None
                producer.send(message, partition_key=partition_key)
                logger.info(f"JSON publicado en {topic_name} con key {partition_key}")
            else:
                producer.send(message)
                logger.info(f"JSON publicado en {topic_name}")
            
        except Exception as e:
            logger.error(f"Error publicando JSON en Pulsar: {e}")
            raise
    
    def close(self):
        """Cierra todas las conexiones del publisher"""
        try:
            for producer in self.producers.values():
                producer.close()
            if self.client:
                self.client.close()
            logger.info("Pulsar publisher connections closed")
        except Exception as e:
            logger.error(f"Error cerrando conexiones del publisher: {e}")

    def close(self):
        """Cierra todas las conexiones"""
        for producer in self.producers.values():
            producer.close()
        if self.client:
            self.client.close()

class PulsarEventConsumer:
    def __init__(self, service_name: str = None):
        self.config = PulsarConfig()
        self.client = None
        self.consumers = {}
        self.service_name = service_name or os.getenv('SERVICE_NAME', 'campaign-management')
        
    def _get_client(self) -> Client:
        """Obtiene o crea el cliente de Pulsar"""
        if self.client is None:
            self.client = Client(self.config.service_url)
        return self.client
    
    def subscribe_to_topic(self, topic_name: str, subscription_name: str, callback):
        """Se suscribe a un topic específico con mejor manejo de errores"""
        try:
            # Create unique subscription name using service name
            unique_subscription_name = f"{self.service_name}-{subscription_name}"
            
            logger.info(f"Attempting to subscribe to topic: {topic_name}")
            logger.info(f"Using subscription: {unique_subscription_name}")
            logger.info(f"Pulsar service URL: {self.config.service_url}")
            
            client = self._get_client()
            logger.info("Pulsar client created successfully")
            
            consumer = client.subscribe(
                topic=topic_name, 
                subscription_name=unique_subscription_name, 
                consumer_type=ConsumerType.Shared
            )
            logger.info("Pulsar consumer created successfully")
            
            self.consumers[topic_name] = consumer
            
            # Procesar mensajes en un hilo separado
            import threading
            thread = threading.Thread(target=self._process_messages, args=(consumer, callback))
            thread.daemon = True
            thread.start()
            
            logger.info(f"Successfully subscribed to topic {topic_name} with subscription {unique_subscription_name}")
            
        except Exception as e:
            logger.error(f"Error suscribiéndose al topic {topic_name}: {e}")
            logger.error(f"Topic name: {topic_name}")
            logger.error(f"Subscription name: {unique_subscription_name}")
            logger.error(f"Service URL: {self.config.service_url}")
            raise
    
    def _process_messages(self, consumer, callback):
        """Procesa mensajes del consumer con mejor manejo de errores"""
        logger.info("Starting message processing loop")
        try:
            while True:
                try:
                    msg = consumer.receive(timeout_millis=1000)
                    # Deserializar el mensaje
                    event_data = json.loads(msg.data().decode('utf-8'))
                    logger.debug(f"Received message: {event_data.get('event_type', 'unknown')}")
                    callback(event_data)
                    consumer.acknowledge(msg)
                    logger.debug("Message acknowledged successfully")
                except Exception as e:
                    # Check if it's a timeout exception (normal behavior when no messages)
                    if "TimeOut" in str(e) or "timeout" in str(e).lower():
                        # This is normal - no messages available, continue waiting
                        continue
                    else:
                        # This is an actual error processing a message
                        logger.error(f"Error procesando mensaje: {e}")
                        logger.error(f"Exception type: {type(e).__name__}")
                        if 'msg' in locals():
                            try:
                                consumer.negative_acknowledge(msg)
                                logger.info("Message negatively acknowledged")
                            except Exception as nack_error:
                                logger.error(f"Error in negative acknowledge: {nack_error}")
        except Exception as e:
            logger.error(f"Error en el procesamiento de mensajes: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            # Don't re-raise to prevent consumer crash
    
    def publish_event(self, evento: EventoDominio, topic: str, event_type: str, status: str):
        """Publica un evento en Pulsar"""
        try:
            topic_name = self.config.get_topic_name(topic)
            producer = self._get_producer(topic_name)
            
            # Serializar el evento
            event_dict = {
                'saga_id': uuid.uuid4(),
                'service': 'Loyalty',
                'status': status, 
                'event_id': evento.id,
                'event_type': event_type,
                'event_data': evento.__dict__,
                'timestamp': evento.fecha_evento.isoformat() if hasattr(evento, 'fecha_evento') else None
            }
            event_data=json.dumps(event_dict, default=str)
            
            # Publicar el evento
            producer.send(event_data.encode('utf-8'))
            logger.info(f"Evento publicado en {topic_name}: {evento.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Error publicando evento en Pulsar: {e}")
            raise

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
