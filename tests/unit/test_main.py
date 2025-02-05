from ...main import Main

import unittest
import time
from unittest.mock import patch

class TestMain(unittest.TestCase):
    """
    Test suite for main
    """

    @patch("main.KytosNApp")
    @patch("main.Main._setup_dependencies")
    def test_setup_complete(self, _, setup_mock):
        """
        Test that the setup function correct instantiates 
        """

        def mocked_setup_function():
            """
            Do nothing
            """
            return

        setup_mock.side_effect = mocked_setup_function

        target = Main()

        time.sleep(1)

        self.assertIsNotNone(target._send_ops)
        self.assertTrue(target._loop.is_running())
        self.assertTrue(target._napp_context.is_alive())

        target._loop.call_soon_threadsafe(target._loop.stop)
        target._napp_context.join()
        target._loop.close()
