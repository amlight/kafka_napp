"""Main module of Kafka/Kytos Network Application.
"""

import asyncio

from kytos.core import KytosNApp, log
from kytos.core.helpers import alisten_to

from .settings import (
    TOPIC_NAME,
    IGNORED_EVENTS
)

from .managers.kafka_ops import KafkaSendOperations


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
        self._async_loop = asyncio.get_running_loop()

        # Because the NApp partially runs in a synchronous context, we cannot block/await
        # until the producer is ready. Thus, we need to check if it's not ready in the
        # async contexts.
        self._ready = self._async_loop.create_task(self._send_ops.start_up())

    def execute(self):
        """Execute once when the napp is running."""
        log.info("EXECUTE Kafka/Kytos NApp")

    def shutdown(self):
        """
        Execute when your napp is unloaded.
        """
        log.info("SHUTDOWN Kafka/Kytos")

        for task in asyncio.all_tasks(self._async_loop):
            task.cancel()

        # Future: shutdown the NApp asynchronously (await producer.shutdown())

    @alisten_to(".*")
    async def handle_events(self, event):
        """Handle events"""
        # Optional logging:
        # log.info(f'handle_new_switch event={event} content={event.content}')

        if event.name in IGNORED_EVENTS:
            return

        if not self._ready.done():
            await self._ready

        self._async_loop.create_task(
            self._send_ops.send_message(
                TOPIC_NAME, event.name, event.name, event.content
            )
        )
