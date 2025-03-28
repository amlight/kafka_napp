"""Main module of Kafka/Kytos Network Application.
"""

import json
import asyncio
from threading import Thread
from typing import Coroutine, Callable, Awaitable

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

from kytos.core import KytosNApp, log
from kytos.core.helpers import alisten_to

from kafka_napp.jsonencoder import ComplexEncoder
from kafka_napp.settings import (
    BOOTSTRAP_SERVERS,
    ACKS,
    ENABLE_ITEMPOTENCE,
    REQUEST_TIMEOUT_MS,
    ALLOWED_RETRIES,
    TOPIC_NAME,
    COMPRESSION_TYPE,
    IGNORED_EVENTS,
)


class Main(KytosNApp):
    """
    Main class of the Kytos/Kafka NApp.
    """

    def setup(self):
        """
        Setup the Kafka/Kytos NApp
        """
        log.info("SETUP Kytos/Kafka")

        self._send_ops = KafkaSendOperations()
        self._async_loop = AsyncScheduler(coroutine=self._send_ops.shutdown())

        # In the threaded async loop, run setup
        self._ready = self._async_loop.run_coroutine(self._send_ops.start_up())

    def execute(self):
        """Execute once when the napp is running."""
        log.info("EXECUTE Kafka/Kytos NApp")

    def shutdown(self):
        """
        Execute when your napp is unloaded.
        """
        log.info("SHUTDOWN Kafka/Kytos")

        # Stops the loop, which upon stopping will close the Kafka producer
        try:
            log.info("Stopping loop...")
            self._async_loop.run_coroutine(self._async_loop.stop())

            log.info("Joining thread...")
            self._async_loop.close_thread()

        except Exception as exc:
            log.error(exc)

    @alisten_to(".*")
    async def handle_new_switch(self, event):
        """Handle the event of a new created switch"""
        # Optional logging:
        # log.info(f'handle_new_switch event={event} content={event.content}')

        if event.name in IGNORED_EVENTS:
            return

        if not self._ready.done():
            # Coroutines are not guaranteed to happen sequentially, so we should make sure
            # the producer is available before sending data.
            await self._ready

        self._async_loop.run_coroutine(
            self._send_ops.send_message(
                TOPIC_NAME, event.name, event.name, event.content
            )
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
            await asyncio.wait_for(producer.start(), 11)
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


class AsyncScheduler:
    """
    A class designed contain the loop running in a separate thread, as well as methods that
    interact with the loop.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        thread: Thread = None,
        coroutine: Coroutine = None,
    ):
        """
        Initializer for setting up the thread and loop running inside of it. Accepts a coroutine
        that can be run before the thread joins.
        """
        self._loop = loop if loop else asyncio.new_event_loop()
        self._napp_context = (
            thread if thread else Thread(target=self._run_loop, daemon=True, args=(coroutine,))
        )
        self._napp_context.start()

    def _run_loop(self, coroutine: Coroutine) -> None:
        """
        Run the loop in a thread until stop() is called.

        Args:
            coroutine (Coroutine): The function you'd like run in the event loop before the thread joins.
        """
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_forever()
        finally:
            if coroutine:
                self._loop.run_until_complete(coroutine)

        self._loop.stop()
        self._loop.close()

    def run_coroutine(self, coroutine: Coroutine) -> asyncio.Future:
        """
        Enqueue a coroutine to be executed in the event loop thread.

        Args:
            coroutine (Coroutine[..., None]): The coroutine function to execute.

        Returns:
            asyncio.Future: A Future representing the execution of the coroutine.

        Raises:
            RuntimeError: If the event loop is closed.
        """
        try:
            return asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        except RuntimeError as exc:
            raise exc

    async def stop(self) -> None:
        """
        Calls stop() on the internal async loop

        Raises:
            Exception: If an error occurs during the stop() sequence, it will be returned.
        """
        try:
            self._loop.stop()
        except Exception as exc:
            raise exc

    def close_thread(self, timeout: float = 5.0) -> None:
        """
        Calls join() on the internal thread

        Raises:
            Exception: If an error occurs during the join() sequence, it will be returned.
        """
        try:
            self._napp_context.join(timeout=timeout)
        except Exception as exc:
            raise exc

    async def close_loop(self) -> None:
        """
        Calls close() on the internal loop

        Raises:
            Exception: If an error occurs during the close() sequence, it will be returned.
        """
        try:
            self._loop.close()
        except Exception as exc:
            raise exc
