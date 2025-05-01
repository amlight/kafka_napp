"""Main module of kafka_events/Kytos Network Application.
"""

import asyncio

from re import error as RegexException

from kytos.core import KytosNApp, log, KytosEvent, rest
from kytos.core.rest_api import JSONResponse, Request, aget_json_or_400
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

    @rest("v1/create", methods=['POST'])
    async def create_filter(self, request: Request) -> JSONResponse:
        """
        Tests a potential filter and adds it to the rule dictionary

        Requires 1 provided value in the content section called "pattern". Accepts 1 optional
        value called "description"
        """
        log.info("Request received at /v1/create")

        try:
            content = await aget_json_or_400(request)
            pattern = content.get("pattern")
            description = content.get("description", "N/A")
            self._rule_ops.create_filter(pattern, description)

            return JSONResponse(
                {
                    "status": "200",
                    "response": f"Pattern {pattern} created with description {description}"
                }
            )
        except (ValueError, RegexException) as exc:
            return JSONResponse({"status": "400", "response": exc})

    @rest("v1/list", methods=['GET'])
    async def list_filters(self, _: Request) -> JSONResponse:
        """
        Returns a list of dictionaries that summarize the created filters.

        Does not require json data
        """
        log.info("Request received at /v1/list")

        return JSONResponse(
            {
                "status": "200",
                "response": self._rule_ops.list_filters()
            }
        )

    @rest("v1/delete", methods=['POST'])
    async def delete_filter(self, request: Request) -> JSONResponse:
        """
        Checks if a given pattern is present in the rule dictionary. If it is, delete it.
        Otherwise, raise an exception and return the error to the user.

        Requires 1 provided value in the content section called "pattern".
        """
        log.info("Request received at /v1/delete")

        try:
            content = await aget_json_or_400(request)
            pattern = content.get("pattern")
            self._rule_ops.delete_filter(pattern)

            return JSONResponse(
                {
                    "status": "200",
                    "response": f"Pattern {pattern} deleted."
                }
            )
        except (KeyError, ValueError) as exc:
            return JSONResponse({"status": "400", "response": exc})
