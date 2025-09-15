import os
import json
import logging
from typing import Callable, Optional
from pulsar import Client, ConsumerType, InitialPosition

logger = logging.getLogger(__name__)

class PulsarConfig:
    def __init__(self):
        self.service_url = os.getenv("PULSAR_SERVICE_URL", "pulsar://localhost:6650")
        self.namespace   = os.getenv("PULSAR_NAMESPACE", "campaign-management/events")

    def topic(self, short_name: str) -> str:
        if short_name.startswith("persistent://"):
            return short_name
        return f"persistent://{self.namespace}/{short_name}"

class PulsarEventPublisher:

    def __init__(self, config: Optional[PulsarConfig] = None):
        self.cfg = config or PulsarConfig()
        self._client: Optional[Client] = None
        self._producers = {}  # topic -> producer

    def _client_get(self) -> Client:
        if self._client is None:
            self._client = Client(self.cfg.service_url)
        return self._client

    def _producer_get(self, topic: str):
        if topic not in self._producers:
            client = self._client_get()
            self._producers[topic] = client.create_producer(topic)
        return self._producers[topic]

    def publish_raw(self, topic_short: str, key: str, value: bytes):
        topic = self.cfg.topic(topic_short)
        prod = self._producer_get(topic)
        prod.send(value, partition_key=key)
        logger.debug("Pulsar published topic=%s key=%s bytes=%d", topic, key, len(value))

    def publish_json(self, topic_short: str, key: str, payload: dict):
        self.publish_raw(topic_short, key, json.dumps(payload).encode("utf-8"))

    def close(self):
        try:
            for p in self._producers.values():
                p.close()
            self._producers.clear()
        finally:
            if self._client:
                self._client.close()
                self._client = None

class PulsarEventConsumer:
    def __init__(self, config: Optional[PulsarConfig] = None):
        self.cfg = config or PulsarConfig()
        self._client: Optional[Client] = None
        self._consumer = None

    def _client_get(self) -> Client:
        if self._client is None:
            self._client = Client(self.cfg.service_url)
        return self._client

    def subscribe(self, topic_short: str, subscription: str, on_message: Callable[[dict], None]):
        topic = self.cfg.topic(topic_short)
        client = self._client_get()
        self._consumer = client.subscribe(
            topic,
            subscription_name=subscription,
            consumer_type=ConsumerType.Shared,
            initial_position=InitialPosition.Earliest,
        )
        logger.info("Pulsar subscribed topic=%s subscription=%s", topic, subscription)

        while True:
            msg = self._consumer.receive()
            try:
                payload = json.loads(msg.data().decode("utf-8"))
                on_message(payload)
                self._consumer.acknowledge(msg)
            except Exception as e:
                logger.exception("Error procesando mensaje Pulsar: %s", e)
                self._consumer.negative_acknowledge(msg)

    def close(self):
        if self._consumer:
            self._consumer.close()
            self._consumer = None
        if self._client:
            self._client.close()
            self._client = None

_pcfg = PulsarConfig()
pulsar_publisher = PulsarEventPublisher(_pcfg)
pulsar_consumer  = PulsarEventConsumer(_pcfg)
