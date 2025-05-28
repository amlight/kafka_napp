"""Main module of kafka_events/Kytos Network Application.
"""

import asyncio

from re import error as RegexException

from kytos.core import KytosNApp, log, KytosEvent, rest
from kytos.core.rest_api import JSONResponse, Request, aget_json_or_400, HTTPException
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
        self._regex_ready = self._async_loop.create_task(self._rule_ops.start_up())
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

        if not self._ready.done():
            await self._ready
        if not self._regex_ready.done():
            await self._regex_ready

        if not await self._rule_ops.is_accepted_event(event.name):
            return

        self._async_loop.create_task(
            self._send_ops.send_message(
                TOPIC_NAME, event.name, event.name, event.content
            )
        )

    @rest("v1/filters/", methods=['POST'])
    async def create_filter(self, request: Request) -> JSONResponse:
        """
        Tests a potential filter and adds it to the rule dictionary

        Requires 1 provided value in the content section called "pattern". Accepts 1 optional
        value called "description"
        """
        try:
            content = await aget_json_or_400(request)
            pattern = content.get("pattern")
            description = content.get("description", "N/A")

            log.debug(
                "Request received at /v1/create with pattern: %s desc: %s",
                pattern,
                description
            )

            filter_obj: dict[str, dict[str, str]] = await self._rule_ops.create_filter(
                pattern, description
            )
            status: int = 201

            return JSONResponse(
                filter_obj,
                status_code=status
            )
        except (ValueError, RegexException) as exc:
            log.debug("Exception thrown: %s", exc)
            raise HTTPException(400, detail=str(exc))
        except KeyError as exc:
            log.debug("Exception thrown: %s", exc)
            raise HTTPException(400, detail="Pattern was not provided in request body.")

    @rest("v1/filters/", methods=['GET'])
    async def list_filters(self, _: Request) -> JSONResponse:
        """
        Returns a list of dictionaries that summarize the created filters.

        Does not require json data
        """
        log.debug("Request received at /v1/list")
        status: int = 200

        return JSONResponse(
            await self._rule_ops.list_filters(),
            status_code=status
        )

    @rest("v1/filters/{filter_id}", methods=['DELETE'])
    async def delete_filter(self, request: Request) -> JSONResponse:
        """
        Checks if a given pattern is present in the rule dictionary. If it is, delete it.
        Otherwise, raise an exception and return the error to the user.
        """
        try:
            filter_id = request.path_params["filter_id"]

            log.debug("Request received at /v1/delete/%s", filter_id)

            filter_obj: dict[str, str] = await self._rule_ops.delete_filter(filter_id)
            status: int = 200

            return JSONResponse(
                    {filter_id: filter_obj},
                    status_code=status
            )
        except ValueError as exc:
            log.debug("/v1/filters result: %s %s", exc, 400)
            raise HTTPException(400, detail=str(exc))
        except KeyError as exc:
            log.debug("/v1/filters result: %s %s", exc, 404)
            raise HTTPException(404, detail=str(exc))
