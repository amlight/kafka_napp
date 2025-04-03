"""
Test suite for main.py
"""

import unittest
from unittest.mock import patch

from kafka_napp.main import Main


class TestMain(unittest.TestCase):
    """
    Test suite for main
    """

    @patch("kafka_napp.main.KafkaSendOperations.shutdown")
    @patch("kafka_napp.main.KafkaSendOperations.start_up")
    def test_startup_complete(self, start_mock, shutdown_mock):
        """
        Test that the start up function correct instantiates 
        """

        async def mocked_function():
            """
            Do nothing
            """
            return

        start_mock.side_effect = mocked_function
        shutdown_mock.side_effect = mocked_function

        target = Main(None)

        self.assertIsNotNone(target._send_ops)
        self.assertTrue(target._async_loop._loop.is_running())
        self.assertTrue(target._async_loop._napp_context.is_alive())

        target.shutdown()
