"""
Test suite for interactions with kafka
"""

import random
import unittest
import asyncio

from unittest.mock import patch, MagicMock

from aiokafka.errors import KafkaConnectionError
from tenacity import RetryError

from ...settings import ALLOWED_RETRIES
from ...managers.kafka_ops import KafkaSendOperations

async def skip_sleep(*_: any) -> None:
    """ An async function to use for retry.sleep """
    return 0

async def throw_exception(**_):
    """
    Throw a KafkaConnectionError
    """
    raise KafkaConnectionError()

class TestKafkaSendOperations(unittest.TestCase):
    """ Test suite for KafkaSendOperations """

    @patch("kafka_napp.main.AIOKafkaProducer")
    def test_setup_producer_retries(self, producer_mock_cls):
        """
        Test that the producer will retry 3 times (by default)
        """
        producer_mock = MagicMock()
        producer_mock.start.side_effect = throw_exception

        producer_mock_cls.return_value = producer_mock

        send_ops = KafkaSendOperations()
        send_ops._setup_producer.retry.sleep = skip_sleep

        async def run_test() -> None:
            """ Wrapper to run tests """
            with self.assertRaises(RetryError):
                await send_ops._setup_producer()

        asyncio.run(run_test())

        self.assertEqual(producer_mock.start.call_count, 3)

    def test_send_message_retries(self):
        """
        Test that the producer will retry ALLOWED_RETRIES times.
        """
        producer_mock = MagicMock()
        producer_mock.send.side_effect = throw_exception

        send_ops = KafkaSendOperations()
        send_ops._producer = producer_mock
        send_ops._send_data.retry.sleep = skip_sleep

        async def run_test() -> None:
            """ Wrapper to run tests """
            await send_ops.send_message(
                "Test topic",
                "Test event",
                "Test key",
                "Test message"
            )

        asyncio.run(run_test())

        self.assertEqual(producer_mock.send.call_count, ALLOWED_RETRIES)

    def test_messages_are_chronological(self):
        """
        Test that messages sent to "send_messages" are sent out in chronological order,
        """
        async def wait_one_second(**_):
            """ A mock function to wait one second (simulate network delay) """
            await asyncio.sleep(1)

            if random.choice([False, False, False, True]):
                raise KafkaConnectionError()

        completion_order: list[str] = []

        producer_mock = MagicMock()
        producer_mock.send.side_effect = wait_one_second

        send_ops = KafkaSendOperations()
        send_ops._producer = producer_mock
        send_ops._send_data.retry.sleep = skip_sleep

        async def test_and_record(coroutine_id: int) -> None:
            """ Run the test, then record when it finished using time.time() """
            await send_ops.send_message("Test", "Test", "Test", "Test Message")
            completion_order.append(coroutine_id)

        async def run_test() -> None:
            """ Wrapper to run tests """
            await asyncio.gather(
                test_and_record("1"),
                test_and_record("2"),
                test_and_record("3"),
                test_and_record("4"),
                test_and_record("5"),
                test_and_record("6"),
                test_and_record("7"),
                test_and_record("8")
            )

        asyncio.run(run_test())

        self.assertEqual("".join(completion_order), "12345678", completion_order)
