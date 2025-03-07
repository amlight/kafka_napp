"""Main module of Kafka/Kytos Network Application.
"""

import json
import asyncio
import time
from threading import Thread
from typing import Coroutine, Callable, Awaitable

from aiokafka import AIOKafkaProducer
from aiokafka.errors import (
    NodeNotReadyError as AsyncNodeNotReady,
    KafkaConnectionError as AsyncKafkaConnectionError,
    KafkaTimeoutError as AsyncKafkaTimeoutError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_combine,
    wait_fixed,
    wait_random,
)
from kafka import KafkaAdminClient
from kafka.admin.new_topic import NewTopic
from kafka.errors import (
    UnknownTopicOrPartitionError,
    NodeNotReadyError,
    KafkaConnectionError,
    KafkaTimeoutError,
)

from kytos.core import KytosNApp, log
from kytos.core.helpers import alisten_to

from kafka_napp.jsonencoder import ComplexEncoder
from kafka_napp.settings import (
    BOOTSTRAP_SERVERS,
    ACKS,
    DEFAULT_NUM_PARTITIONS,
    REPLICATION_FACTOR,
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

        self._send_ops = KafkaSendOperations(BOOTSTRAP_SERVERS, COMPRESSION_TYPE, ACKS)
        self._async_loop = AsyncScheduler(coroutine=self._send_ops.shutdown())

        # In the threaded async loop, run setup
        self._async_loop.run_callable_soon(self._send_ops.setup_dependencies)

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

        self._async_loop.run_coroutine(
            self._send_ops.send_message(
                TOPIC_NAME, event.name, event.name, event.content
            )
        )


class KafkaSendOperations:
    """
    Class for sending Kafka operations
    """

    def __init__(
        self,
        bootstrap_servers: str,
        compression_type: str | None = None,
        acks: int | str = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._compression_type = compression_type
        self._acks = acks

        self._producer: AIOKafkaProducer = None
        self._admin = self._setup_admin()

    async def setup_dependencies(self):
        """
        Start an asyncio loop in a separate thread, so Kytos can synchronously close
        """
        await self.start_up()

        if not await self.check_for_topic(TOPIC_NAME):
            await self.create_topic(TOPIC_NAME, DEFAULT_NUM_PARTITIONS)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_combine(wait_fixed(2), wait_random(min=2, max=7)),
        retry=retry_if_exception_type(
            (KafkaTimeoutError, KafkaConnectionError, NodeNotReadyError)
        ),
    )
    def _setup_admin(self) -> KafkaAdminClient:
        """
        Setup the admin client and handle NodeNotReadyIssues
        """
        try:
            return KafkaAdminClient(
                bootstrap_servers=self._bootstrap_servers, request_timeout_ms=10000
            )
        except (NodeNotReadyError, KafkaConnectionError, KafkaTimeoutError) as exc:
            log.error("Kafka-python retrying connection...")
            raise exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_combine(wait_fixed(2), wait_random(min=2, max=7)),
        retry=retry_if_exception_type(
            (AsyncKafkaTimeoutError, AsyncKafkaConnectionError, AsyncNodeNotReady)
        ),
    )
    async def _setup_producer(self) -> AIOKafkaProducer:
        """
        Setup the producer client and handle connection issues
        """
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                compression_type=self._compression_type,
                acks=self._acks,
                request_timeout_ms=10000,
            )
            await asyncio.wait_for(producer.start(), 11)
            return producer
        except (
            AsyncNodeNotReady,
            AsyncKafkaConnectionError,
            AsyncKafkaTimeoutError,
        ) as exc:
            log.error("AIOKafka retrying connection...")
            raise exc

    async def start_up(self) -> None:
        """
        AIOKafka requires a setup procedure
        """
        try:
            self._producer = await self._setup_producer()
        except (
            AsyncNodeNotReady,
            AsyncKafkaConnectionError,
            AsyncKafkaTimeoutError,
        ) as exc:
            log.error("AIOKafkaProducer could not establish a connection.")
            raise exc

    async def create_topic(self, topic_name: str, num_partitions: int) -> None:
        """Create a topic with a provided number of partitions"""
        self._admin.create_topics(
            NewTopic(
                name=topic_name,
                num_partitions=num_partitions,
                replication_factor=REPLICATION_FACTOR,
            )
        )

    async def check_for_topic(self, topic_name: str) -> bool:
        """Checks if a topic exists"""
        try:
            return self._admin.describe_topics([topic_name]) is not None
        except UnknownTopicOrPartitionError:
            return False
        except Exception as exc:
            raise exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_combine(wait_fixed(2), wait_random(min=2, max=7)),
        retry=retry_if_exception_type(
            (AsyncKafkaTimeoutError, AsyncKafkaConnectionError, AsyncNodeNotReady)
        ),
    )
    async def shutdown(self):
        """
        Shutdown the producer
        """
        try:
            await self._producer.stop()
        except (
            AsyncNodeNotReady,
            AsyncKafkaConnectionError,
            AsyncKafkaTimeoutError,
        ) as exc:
            log.error("AIOKafka retrying shutdown procedure...")
            raise exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_combine(wait_fixed(2), wait_random(min=1, max=2)),
        retry=retry_if_exception_type(
            (AsyncKafkaTimeoutError, AsyncKafkaConnectionError, AsyncNodeNotReady)
        ),
    )
    async def send_message(
        self, topic_name: str, event: str, key: str, message: any
    ) -> None:
        """
        Send a message to the specified topic name
        """
        json_message = json.dumps(
            {"event": event, "type": key, "message": message}, cls=ComplexEncoder
        ).encode()
        try:
            await self._producer.send(topic=topic_name, value=json_message)
        except (
            AsyncNodeNotReady,
            AsyncKafkaConnectionError,
            AsyncKafkaTimeoutError,
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
            thread
            if thread
            else Thread(target=self._run_loop, daemon=True, args=(coroutine,))
        )
        self._napp_context.start()

    def _run_loop(self, coroutine: Coroutine) -> None:
        """
        Run the loop in a thread until stop() is called.

        Args:
            coroutine (Coroutine): The function you'd like run in the event loop before the thread joins.
        """
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

        while self._loop.is_running():
            time.sleep(1)

        if coroutine:
            self._loop.run_until_complete(coroutine)

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

    def _submit_coro_soon_threadsafe(
        self, callable_function: Callable[..., Awaitable], *args
    ) -> asyncio.Future:
        """
        Enqueue an async callable to be executed soon in the event loop thread.

        Args:
            callable_function (Callable[..., Awaitable]): The async function to execute.
            *args: Arguments to pass to the async function.

        Returns:
            asyncio.Future: A Future representing the execution of the task.

        Raises:
            RuntimeError: If the event loop is closed.
        """
        future = asyncio.Future()
        log.info(callable_function)

        def _create_task() -> asyncio.Future:
            """
            Create the coroutine and return the future
            """
            try:
                task = asyncio.create_task(callable_function(*args))
                task.add_done_callback(
                    lambda t: (
                        future.set_result(t.result())
                        if not t.exception()
                        else future.set_exception(t.exception())
                    )
                )
            except Exception as exc:
                future.set_exception(exc)

        try:
            self._loop.call_soon_threadsafe(_create_task)
        except RuntimeError as exc:
            raise exc
        log.info(future)
        return future

    def run_callable_soon(
        self, callable_function: Callable[..., Awaitable], *args
    ) -> asyncio.Future:
        """
        REQUIRES A CALLABLE ASYNC FUNCTION

        Enqueue an async callable to be executed soon in the event loop thread and immediately
        return

        This method is used for scheduling a coroutine function to run within the loop safely.
        Example usage:

            self.run_coroutine_soon(my_async_function, arg1, arg2)

        Args:
            callable_function (Callable[..., Awaitable]): The async function to execute.
            *args: Arguments to pass to the async function.

        Returns:
            asyncio.Future: A Future representing the execution of the task.

        Raises:
            RuntimeError: If the event loop is closed.
        """
        try:
            return self._submit_coro_soon_threadsafe(callable_function, *args)
        except RuntimeError as exc:
            raise exc

    async def run_coroutine_soon_and_wait(
        self, callable_function: Callable[..., Awaitable], *args
    ) -> asyncio.Future:
        """
        Enqueue an async callable to be executed soon in the event loop thread and immediately
        return

        This method is used for scheduling a coroutine function to run within the loop safely.
        Example usage:

            self.run_coroutine_soon(my_async_function, arg1, arg2)

        Args:
            callable_function (Callable[..., Awaitable]): The async function to execute.
            *args: Arguments to pass to the async function.

        Returns:
            asyncio.Future: A Future representing the execution of the task.

        Raises:
            RuntimeError: If the event loop is closed.
        """
        try:
            return await self._submit_coro_soon_threadsafe(callable_function, *args)
        except RuntimeError as exc:
            raise exc

    def cancel_all_tasks(self) -> None:
        """
        Cancel all tasks that are pending in the asynchronous loop.
        """
        for task in asyncio.all_tasks(self._loop):
            try:
                task.cancel()
            except Exception as exc:
                log.warn(f"Task {task.get_name()} could not be canceled: {exc}")

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

    def close_thread(self) -> None:
        """
        Calls join() on the internal thread

        Raises:
            Exception: If an error occurs during the join() sequence, it will be returned.
        """
        try:
            self._napp_context.join()
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
