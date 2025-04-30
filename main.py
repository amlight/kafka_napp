"""Main module of kafka_events/Kytos Network Application.
"""

import asyncio

from kytos.core import KytosNApp, log, KytosEvent
from kytos.core.helpers import alisten_to

from .settings import (
    TOPIC_NAME
)

from .managers.kafka_ops import KafkaSendOperations
from .managers.regex import RegexOperations


class Main(KytosNApp):
    """
    Main class of the Kytos/kafka_events NApp.
    """

    def setup(self):
        """
        Setup the kafka_events/Kytos NApp
        """
        log.info("SETUP Kytos/kafka_events")

        self._send_ops = KafkaSendOperations()
        self._async_loop = asyncio.get_running_loop()
        self._rule_ops = RegexOperations()

        # Because the NApp partially runs in a synchronous context, we cannot block/await
        # until the producer is ready. Thus, we need to check if it's not ready in the
        # async contexts.
        self._ready = self._async_loop.create_task(self._send_ops.start_up())

    def execute(self):
        """Execute once when the napp is running."""
        log.info("EXECUTE kafka_events/Kytos NApp")

    def shutdown(self):
        """
        Execute when your napp is unloaded.
        """
        log.info("SHUTDOWN kafka_events/Kytos")

        for task in asyncio.all_tasks(self._async_loop):
            task.cancel()

        # Future: shutdown the NApp asynchronously (await producer.shutdown())

    @alisten_to(".*")
    async def handle_events(self, event: KytosEvent):
        """Handle events"""
        # Optional logging:
        # log.info(f'handle_new_switch event={event} content={event.content}')

        if not self._rule_ops.is_accepted_event(event.name):
            return

        if not self._ready.done():
            await self._ready

        self._async_loop.create_task(
            self._send_ops.send_message(
                TOPIC_NAME, event.name, event.name, event.content
            )
        )
