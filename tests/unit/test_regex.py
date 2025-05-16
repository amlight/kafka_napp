"""
Test suite for testing the RegexOperations class
"""

import unittest
import asyncio

from re import error as RegexException

from ...managers.regex import RegexOperations
from ...models.filter import Filter

async def quick_setup(regex: RegexOperations) -> dict[str, Filter]:
    """
    Call setup quickly

    RegexOperations is async-based, so usage of asyncio is necessary.
    """
    custom_rules: list[dict[str, str]] = [
        {"pattern": r"^base/simple_ui.work$", "description": "Test"},
        {"pattern": r"kytos[.](.*)", "description": "Test2"}
    ]

    return await regex._setup_rules(custom_rules)

class TestRegexOperations(unittest.TestCase):
    """
    Test cases
    """
    def setUp(self):
        self.regex = RegexOperations()

        async def run_setup() -> None:
            """ Wrapper to run async setup """
            await self.regex.start_up()

        asyncio.run(run_setup())

    def test_setup_rules_success(self):
        """
        Test that _setup_rules correctly sets up Kytos-specific regex
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            rules: dict[str, Filter] = await quick_setup(self.regex)
            patterns: list[str] = [x.pattern.pattern for x in rules.values()]

            self.assertTrue("^base/simple_ui.work$" in patterns)
            self.assertFalse("kytos[\\.](.*)" in patterns)

        asyncio.run(run_test())

    def test_is_accepted_event(self):
        """
        Test that the public facing interface should return true if an event is contained within the
        regular expressions
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            self.assertTrue(await self.regex.is_accepted_event("kytos/mef_eline.created"))
            self.assertFalse(await self.regex.is_accepted_event("base/simple_ui.finished"))
            self.assertTrue(await self.regex.is_accepted_event("kytos.core.start"))

        asyncio.run(run_test())

    def test_base_functionality_allows_core_napps(self):
        """
        Test that the original settings allow for the core napps to have access to the event loop
        """

        async def run_test() -> None:
            """ Wrapper to run async tests """
            self.assertTrue(await self.regex.is_accepted_event("kytos/mef_eline.created"))
            self.assertTrue(await self.regex.is_accepted_event("kytos/of_core.switch.interface.modified"))
            self.assertTrue(await self.regex.is_accepted_event(
                "kytos/flow_manager.messages.out.ofpt_barrier_request"
            ))
            self.assertTrue(await self.regex.is_accepted_event("kytos/topology.topology_loaded"))
            self.assertTrue(await self.regex.is_accepted_event("kytos/of_lldp.messages.out.ofpt_packet_out"))
            self.assertTrue(await self.regex.is_accepted_event("kytos.core.any_napp"))

        asyncio.run(run_test())

    def test_base_functionality_does_not_allow_non_core_napps(self):
        """
        Test that the original settings do not allow messages from non-core NApps
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            self.assertFalse(await self.regex.is_accepted_event("base/ui.started"))
            self.assertFalse(await self.regex.is_accepted_event("extra.of_l2ls.work"))
            self.assertFalse(await self.regex.is_accepted_event("kaytos/kronos.end"))

        asyncio.run(run_test())

    def test_can_create_new_filters(self):
        """
        Test that RegexOperations can create filters
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            self.assertFalse(await self.regex.is_accepted_event("base/simple_ui.not_added"))
            filter_obj: dict[str, str] = await self.regex.create_filter("^base/simple_ui.not_added$", "N/A")
            self.assertTrue(await self.regex.is_accepted_event("base/simple_ui.not_added"))
            self.assertTrue(filter_obj["id"] in self.regex.rules)

        asyncio.run(run_test())

    def test_can_delete_filters(self):
        """
        Test that RegexOperations can delete filters
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            filter_obj: dict[str, str] = await self.regex.create_filter("^base/simple_ui.not_added$", "N/A")
            self.assertTrue(await self.regex.is_accepted_event("base/simple_ui.not_added"))
            self.assertTrue(filter_obj["id"] in self.regex.rules)

            await self.regex.delete_filter(filter_obj["id"])
            self.assertFalse(await self.regex.is_accepted_event("base/simple_ui.not_added"))
            self.assertFalse(filter_obj["id"] in self.regex.rules)

        asyncio.run(run_test())

    def test_can_list_filters(self):
        """
        Test that RegexOperations can list filters
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            await self.regex.create_filter("^base/simple_ui.created$", "N/A")
            await self.regex.create_filter("base[/.].*", "N/A")
            self.assertEqual(3, len(await self.regex.list_filters()))

        asyncio.run(run_test())

    def test_can_only_delete_mutable_values(self):
        """
        Test that deletions can only occur on mutable Filters
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            immutable_id: str = ""

            for key in self.regex.rules:
                # Get the first key in the dictionary.
                immutable_id = key
                break

            filter_obj = await self.regex.create_filter("test[./]something[./](.*)", "Test")
            await self.regex.delete_filter(filter_obj["id"])

            with self.assertRaises(ValueError):
                await self.regex.delete_filter(immutable_id)

            self.assertEqual(1, len(await self.regex.list_filters()))

        asyncio.run(run_test())

    def test_cannot_create_duplicate_patterns(self):
        """
        Test that creations cannot overlap
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            with self.assertRaises(ValueError):
                await self.regex.create_filter("kytos[./](.*)", "Test")

            await self.regex.create_filter("^test/base$", "Test")

            with self.assertRaises(ValueError):
                await self.regex.create_filter("^test/base$", "N/A")

        asyncio.run(run_test())

    def test_cannot_delete_nonexistent_patterns(self):
        """
        Test that deletions cannot remove nonexistent keys
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            with self.assertRaises(KeyError):
                await self.regex.delete_filter("8UNA8ZHAWU80A98") # UUID to Hex example

        asyncio.run(run_test())

    def test_cannot_create_invalid_patterns(self):
        """
        Test that creations cannot compile invalid patterns
        """
        async def run_test() -> None:
            """ Wrapper to run async tests """
            with self.assertRaises(RegexException):
                await self.regex.create_filter("[kytos[[.*]][", "Test")

        asyncio.run(run_test())
