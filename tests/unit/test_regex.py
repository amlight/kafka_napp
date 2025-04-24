"""
Test suite for testing the RegexOperations class
"""

import unittest

from re import Pattern

from ...managers.regex import RegexOperations

def quick_setup(regex: RegexOperations) -> list[Pattern]:
    """
    Call setup quickly
    """
    custom_rules: list[dict[str, str]] = [
        {"pattern": "kytos/mef_eline.*", "type": "wildcard"},
        {"pattern": "kytos/simple_ui.work", "type": "match"},
        {"pattern": "kytos/maintenance.*", "type": "wildcard"}
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
        custom_rules: list[dict[str, str]] = [
            {"pattern": "kytos/mef_eline.*", "type": "wildcard"},
            {"pattern": "kytos/simple_ui.work", "type": "match"}
        ]

        rules: list[Pattern] = self.regex._setup_rules(custom_rules)

        self.assertEqual("kytos/mef_eline\\..*", rules[0].pattern, rules[0])
        self.assertEqual("kytos/simple_ui.work", rules[1].pattern, rules[1])

    def test_wildcard_to_regex(self):
        """
        Should convert all Kytos specific KytosEvent names to their regex counterparts.

        Example: kytos/maintenance.* would translate to the regular expression
        "kytos/maintenance"[0 or more characters], which allows events like
        "kytos/maintenance1234.up", which is not correct.
        """
        self.assertEqual("kytos/maintenance\\..*",
                         self.regex._wildcard_to_regex("kytos/maintenance.*"))
        self.assertEqual("kytos/.*", self.regex._wildcard_to_regex("kytos/*"))

    def test_is_accepted_event(self):
        """
        Test that the public facing interface should return true if an event is contained within the
        regular expressions
        """
        rules: list[Pattern] = quick_setup(self.regex)
        self.regex._rules = rules

        self.assertTrue(self.regex.is_accepted_event("kytos/mef_eline.created"))
        self.assertFalse(self.regex.is_accepted_event("kytos/simple_ui.finished"))
        self.assertTrue(self.regex.is_accepted_event("kytos/maintenance.anything"))

    def test_base_functionality_allows_core_napps(self):
        """
        Test that the original settings allow for the core napps to have access to the event loop
        """
        self.assertTrue(self.regex.is_accepted_event("kytos/mef_eline.created"))
        self.assertTrue(self.regex.is_accepted_event("kytos/of_core.switch.interface.modified"))
        self.assertTrue(self.regex.is_accepted_event("kytos/flow_manager.messages.out.ofpt_barrier_request"))
        self.assertTrue(self.regex.is_accepted_event("kytos/topology.topology_loaded"))
        self.assertTrue(self.regex.is_accepted_event("kytos/of_lldp.messages.out.ofpt_packet_out"))
    {"pattern": "kytos/maintenance.*", "type": "wildcard"}
