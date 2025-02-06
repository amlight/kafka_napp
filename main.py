"""Main module of Kafka/Kytos Network Application.
"""

import json
import asyncio
from threading import Thread

from aiokafka import AIOKafkaProducer
from kafka import KafkaAdminClient
from kafka.admin.new_topic import NewTopic
from kafka.errors import UnknownTopicOrPartitionError

from kytos.core.rest_api import JSONResponse, Request
from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import alisten_to

from .jsonencoder import ComplexEncoder
from .settings import (
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
        self._loop = asyncio.new_event_loop()
        self._napp_context = Thread(target=self._run_loop, daemon=True)
        self._napp_context.start()

        # In the threaded async loop, run setup
        self._loop.call_soon_threadsafe(
            lambda: asyncio.create_task(self._setup_dependencies())
        )

    def _run_loop(self):
        """
        Run the loop in a thread
        """
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

        # When stop() is called, run the shutdown phase
        self._loop.run_until_complete(self._send_ops.shutdown())
        self._loop.close()

    async def _setup_dependencies(self):
        """
        Start an asyncio loop in a separate thread, so Kytos can synchronously close
        """
        await self._send_ops.start_up()

        if not await self._send_ops.check_for_topic(TOPIC_NAME):
            await self._send_ops.create_topic(TOPIC_NAME, DEFAULT_NUM_PARTITIONS)

    def execute(self):
        """Execute once when the napp is running."""
        log.info("EXECUTE Kafka/Kytos NApp")

    def shutdown(self):
        """
        Execute when your napp is unloaded.
        """
        log.info("SHUTDOWN Kafka/Kytos")

        log.info("Closing loop...")

        for task in asyncio.all_tasks(self._loop):
            try:
                task.cancel()
            except Exception:
                log.warn("Task could not be canceled.")


        # Stops the loop, which upon stopping will close the Kafka producer
        self._loop.call_soon_threadsafe(self._loop.stop)

        log.info("Joining thread...")

        self._napp_context.join()

    @rest("/v1/", methods=["GET"])
    def handle_get(self, request: Request) -> JSONResponse:
        """Endpoint to return nothing."""
        log.info("GET /v1/testnapp")
        return JSONResponse({"result": "Napp is running!", "Count": self._event_count})

    @rest("/v1/", methods=["POST"])
    def handle_post(self, request: Request) -> JSONResponse:
        """Endpoint to return nothing."""
        return JSONResponse("Operation successful", status_code=201)

    @alisten_to(".*")
    async def handle_new_switch(self, event):
        """Handle the event of a new created switch"""
        # Optional logging:
        # log.info(f'handle_new_switch event={event} content={event.content}')

        if event.name in IGNORED_EVENTS:
            return

        asyncio.run_coroutine_threadsafe(
            self._send_ops.send_message(
                TOPIC_NAME, event.name, event.name, event.content
            ),
            self._loop
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
        self._admin = KafkaAdminClient(bootstrap_servers=bootstrap_servers)

    async def start_up(self) -> None:
        """
        AIOKafka requires a setup procedure
        """
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            compression_type=self._compression_type,
            acks=self._acks,
        )
        await self._producer.start()

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

    async def shutdown(self):
        """
        Shutdown the producer
        """
        await self._producer.stop()
        self._producer = None

    async def send_message(
        self, topic_name: str, event: str, key: str, message: any
    ) -> None:
        """
        Send a message to the specified topic name
        """
        json_message = json.dumps(
            {"event": event, "type": key, "message": message}, cls=ComplexEncoder
        ).encode()

        await self._producer.send(topic=topic_name, value=json_message)
