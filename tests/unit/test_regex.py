"""
Test suite for testing the RegexOperations class
"""

import unittest

from re import error as RegexException

from ...managers.regex import RegexOperations
from ...models.filter import Filter

def quick_setup(regex: RegexOperations) -> dict[str, Filter]:
    """
    Call setup quickly
    """
    custom_rules: list[dict[str, str]] = [
        {"pattern": r"^base/simple_ui.work$", "description": "Test"},
        {"pattern": r"kytos[.](.*)", "description": "Test2"}
    ]

    return regex._setup_rules(custom_rules)

class TestRegexOperations(unittest.TestCase):
    """
    Test cases
    """
    def setUp(self):
        self.regex = RegexOperations()

    def test_setup_rules_success(self):
        """
        Test that _setup_rules correctly sets up Kytos-specific regex
        """
        rules: dict[str, Filter] = quick_setup(self.regex)

        self.assertEqual("^base/simple_ui.work$", rules["^base/simple_ui.work$"].pattern.pattern)
        self.assertNotEqual("kytos[\\.](.*)", rules["kytos[.](.*)"].pattern.pattern)

    def test_is_accepted_event(self):
        """
        Test that the public facing interface should return true if an event is contained within the
        regular expressions
        """
        self.assertTrue(self.regex.is_accepted_event("kytos/mef_eline.created"))
        self.assertFalse(self.regex.is_accepted_event("base/simple_ui.finished"))
        self.assertTrue(self.regex.is_accepted_event("kytos.core.start"))

    def test_base_functionality_allows_core_napps(self):
        """
        Test that the original settings allow for the core napps to have access to the event loop
        """
        self.assertTrue(self.regex.is_accepted_event("kytos/mef_eline.created"))
        self.assertTrue(self.regex.is_accepted_event("kytos/of_core.switch.interface.modified"))
        self.assertTrue(self.regex.is_accepted_event(
            "kytos/flow_manager.messages.out.ofpt_barrier_request"
        ))
        self.assertTrue(self.regex.is_accepted_event("kytos/topology.topology_loaded"))
        self.assertTrue(self.regex.is_accepted_event("kytos/of_lldp.messages.out.ofpt_packet_out"))
        self.assertTrue(self.regex.is_accepted_event("kytos.core.any_napp"))

    def test_base_functionality_does_not_allow_non_core_napps(self):
        """
        Test that the original settings do not allow messages from non-core NApps
        """
        self.assertFalse(self.regex.is_accepted_event("base/ui.started"))
        self.assertFalse(self.regex.is_accepted_event("extra.of_l2ls.work"))
        self.assertFalse(self.regex.is_accepted_event("kaytos/kronos.end"))

    def test_can_create_new_filters(self):
        """
        Test that RegexOperations can create filters
        """
        self.assertFalse(self.regex.is_accepted_event("base/simple_ui.not_added"))
        self.regex.create_filter("^base/simple_ui.not_added$", "N/A")
        self.assertTrue(self.regex.is_accepted_event("base/simple_ui.not_added"))

    def test_can_delete_filters(self):
        """
        Test that RegexOperations can delete filters
        """
        self.regex.create_filter("^base/simple_ui.not_added$", "N/A")
        self.assertTrue(self.regex.is_accepted_event("base/simple_ui.not_added"))
        self.regex.delete_filter("^base/simple_ui.not_added$")
        self.assertFalse(self.regex.is_accepted_event("base/simple_ui.not_added"))

    def test_can_list_filters(self):
        """
        Test that RegexOperations can list filters
        """
        self.regex.create_filter("^base/simple_ui.created$", "N/A")
        self.regex.create_filter("base[/.].*", "N/A")
        self.assertEqual(3, len(self.regex.list_filters()))

    def test_can_only_delete_mutable_values(self):
        """
        Test that deletions can only occur on mutable Filters
        """
        with self.assertRaises(ValueError):
            self.regex.delete_filter("kytos[./](.*)")

        self.regex.create_filter("test[./]something[./](.*)", "Test")
        self.regex.delete_filter("test[./]something[./](.*)")
        self.assertEqual(1, len(self.regex.list_filters()))

    def test_cannot_create_duplicate_patterns(self):
        """
        Test that creations cannot overlap
        """
        with self.assertRaises(ValueError):
            self.regex.create_filter("kytos[./](.*)", "Test")

        self.regex.create_filter("^test/base$", "Test")

        with self.assertRaises(ValueError):
            self.regex.create_filter("^test/base$", "N/A")

    def test_cannot_delete_nonexistent_patterns(self):
        """
        Test that deletions cannot remove nonexistent keys
        """
        with self.assertRaises(KeyError):
            self.regex.delete_filter("test/dne")

    def test_cannot_create_invalid_patterns(self):
        """
        Test that creations cannot compile invalid patterns
        """
        with self.assertRaises(RegexException):
            self.regex.create_filter("[kytos[[.*]][", "Test")
