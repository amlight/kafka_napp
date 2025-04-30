"""
Module that controls domain-specific interactions with Kafka
"""

import asyncio
import json

from aiokafka import AIOKafkaProducer
from aiokafka.errors import (
    NodeNotReadyError,
    KafkaConnectionError,
    KafkaTimeoutError
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_combine,
    wait_fixed,
    wait_random,
    RetryError
)

from kytos.core import log

from ..jsonencoder import ComplexEncoder

from ..settings import (
    BOOTSTRAP_SERVERS,
    ACKS,
    ENABLE_ITEMPOTENCE,
    REQUEST_TIMEOUT_MS,
    ALLOWED_RETRIES,
    COMPRESSION_TYPE,
)


class KafkaSendOperations:
    """
    Class for sending Kafka operations
    """

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer = None
        self._lock = asyncio.Lock()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_combine(wait_fixed(2), wait_random(min=2, max=7)),
        retry=retry_if_exception_type(
            (KafkaTimeoutError, KafkaConnectionError, NodeNotReadyError)
        ),
    )
    async def _setup_producer(self) -> AIOKafkaProducer:
        """
        Setup the producer client and handle connection issues
        """
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                compression_type=COMPRESSION_TYPE,
                acks=ACKS,
                enable_idempotence=ENABLE_ITEMPOTENCE,
                request_timeout_ms=REQUEST_TIMEOUT_MS,
            )
            await asyncio.wait_for(producer.start(), 5)
            return producer
        except (
            NodeNotReadyError,
            KafkaConnectionError,
            KafkaTimeoutError,
        ) as exc:
            log.error("AIOKafka retrying connection...")
            raise exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_combine(wait_fixed(2), wait_random(min=2, max=7)),
        retry=retry_if_exception_type(
            (KafkaTimeoutError, KafkaConnectionError, NodeNotReadyError)
        ),
    )
    async def start_up(self) -> None:
        """
        AIOKafka requires a setup procedure
        """
        try:
            self._producer = await self._setup_producer()
        except (
            NodeNotReadyError,
            KafkaConnectionError,
            KafkaTimeoutError,
        ) as exc:
            log.error("AIOKafkaProducer could not establish a connection.")
            raise exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_combine(wait_fixed(2), wait_random(min=2, max=7)),
        retry=retry_if_exception_type(
            (KafkaTimeoutError, KafkaConnectionError, NodeNotReadyError)
        ),
    )
    async def shutdown(self):
        """
        Shutdown the producer
        """
        try:
            await self._producer.stop()
        except (
            NodeNotReadyError,
            KafkaConnectionError,
            KafkaTimeoutError,
        ) as exc:
            log.error("AIOKafka retrying shutdown procedure...")
            raise exc

    async def send_message(
        self, topic_name: str, event: str, key: str, message: any
    ) -> None:
        """
        Wrapper function to send to the specified topic name. Guarantees chronological
        message delivery by using a lock on the data.

        Scheduled tasks must wait to acquire a lock, but are free to serialize their data.
        This allows for some concurrency with chronological output.
        """
        json_message = json.dumps(
            {"event": event, "type": key, "message": message}, cls=ComplexEncoder
        ).encode()

        try:
            async with self._lock:
                await self._send_data(topic_name, json_message)
        except RetryError:
            log.error("Kafka could not be reached.")

    @retry(
        stop=stop_after_attempt(ALLOWED_RETRIES),
        wait=wait_combine(wait_fixed(2), wait_random(min=1, max=5)),
        retry=retry_if_exception_type(
            (KafkaTimeoutError, KafkaConnectionError, NodeNotReadyError)
        ),
    )
    async def _send_data(self, topic: str, value: bytes) -> None:
        """
        Send a message to the specified topic name. Retry on failure
        """
        try:
            await self._producer.send(topic=topic, value=value)
        except (
            NodeNotReadyError,
            KafkaConnectionError,
            KafkaTimeoutError,
        ) as exc:
            log.error(
                "AIOKafkaProducer could not send the data to the cluster. Retrying..."
            )
            raise exc
