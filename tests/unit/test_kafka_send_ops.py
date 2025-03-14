"""
Test suite for interactions with kafka
"""
from unittest.mock import patch, MagicMock

import pytest
from aiokafka.errors import KafkaConnectionError
from tenacity import RetryError

import kafka_napp.settings
from ...main import KafkaSendOperations


@pytest.mark.asyncio
@patch("kafka_napp.main.AIOKafkaProducer.start")
async def test_setup_producer_retries(start_mock):
    """
    Test that the producer will retry 3 times (by default)
    """
    send_ops = KafkaSendOperations()

    def throw_exception():
        """
        Throw a KafkaConnectionError
        """
        raise KafkaConnectionError()

    start_mock.side_effect = throw_exception

    with pytest.raises(RetryError):
        await send_ops._setup_producer()

    assert start_mock.call_count == 3

@pytest.mark.asyncio
@patch("kafka_napp.main.ALLOWED_RETRIES", 2)
@patch("kafka_napp.main.AIOKafkaProducer")
async def test_send_message_retries(producer_mock):
    """
    Test that the producer will retry 3 times (by default)
    """
    async def throw_exception(**kwargs):
        """
        Throw a KafkaConnectionError
        """
        raise KafkaConnectionError()


    send_ops = KafkaSendOperations()
    send_ops._producer = producer_mock
    producer_mock.send.side_effect = throw_exception

    with pytest.raises(RetryError):
        await send_ops.send_message(
            "Test topic",
            "Test event",
            "Test key",
            "Test message"
        )

    assert producer_mock.send.call_count == 2
