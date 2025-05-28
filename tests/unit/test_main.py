"""
Test suite for main.py
"""

import asyncio
import unittest
from unittest.mock import patch

from ...main import Main

from kytos.core import KytosEvent

async def mocked_function():
    """
    Do nothing
    """
    return

class TestMain(unittest.TestCase):
    """
    Test suite for main
    """

    @patch("kafka_napp.main.KafkaSendOperations.start_up")
    def test_startup_complete(self, start_mock):
        """
        Test that the start up function correct instantiates 
        """

        async def test():
            start_mock.side_effect = mocked_function

            target = Main(None)

            self.assertIsNotNone(target._send_ops)
            self.assertTrue(target._async_loop.is_running())
            self.assertIsNotNone(target._rule_ops)

        asyncio.run(test())

    @patch("kafka_napp.main.KafkaSendOperations.send_message")
    @patch("kafka_napp.main.KafkaSendOperations.start_up")
    def test_unwanted_events_are_filtered_out(self, start_mock, send_message):
        """
        Main should ignore any events not listed in its _regex_ops object
        """
        async def test():
            start_mock.side_effect = mocked_function
            send_message.side_effect = mocked_function

            target = Main(None)

            target.handle_events(KytosEvent(
                name='invalid_message/of_stats.messages.out.ofpt_stats_request',
                content={}))

            self.assertTrue(start_mock.called)
            self.assertFalse(send_message.called)

        asyncio.run(test())
