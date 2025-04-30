# Overview

This NApp integrates Kafka with the Kytos SDN platform to enable event-driven messaging and real-time event streaming.

# Features

- Asynchronous Kafka producer with support for compression and acknowledgments.
- Automatic Kafka topic creation if it does not exist.
- Event listener for new switch connections, publishing events to Kafka.
- Resilient Kafka admin client with automatic retries for connectivity issues.
- Threaded asyncio loop to handle asynchronous tasks without blocking Kytos.
- Graceful shutdown ensuring Kafka producer cleanup and event loop termination.

# Requirements

- [aiokafka](https://aiokafka.readthedocs.io/en/stable/)

# Events

## Subscribed

- `kytos/mef_eline.*`
- `kytos/of_core.*`
- `kytos/flow_manager.*`
- `kytos/topology.*`
- `kytos/of_lldp.*`
- `kytos/pathfinder.*`
- `kytos/maintenance.*`

# Filtering

Event consumption and serialization follows the principle of `least privilege`, meaning events must be explicitly accepted to be allowed to be propagated to Kafka. Filtering logic uses `regex` to quickly accept or deny incoming events, based on preset patterns. Currently, you can use `wildcard` and `match` expressions, explained below:

## Wildcard

Allows all events that coming after a mandatory prefix.

```
{"pattern": "kytos/mef_eline.*", "type": "wildcard"} # Allows events like kytos/mef_eline.created, etc.
```

## Match

Allows only the exact event that fits its pattern

```
{"pattern": "kytos/simple_ui.example", "type": "match"} # Explicitly allows kytos/simple_ui.example, nothing more.
```

# Development

The following is a list of commands that allow you quickly download and run the NApp with Kytos. This assume that you have a MongoDB instance available.


```
git clone https://github.com/Auwate/kafka_napp.git

python3 -m venv venv
source venv/bin/activate

pip install -e git+https://github.com/kytos-ng/kytos.git#egg=kytos[dev]
pip install kafka-python-ng
pip install aiokafka

python3 kafka_napp/setup.py develop

cd kafka_napp/setup/
docker-compose up -d

export MONGO_PASSWORD=kytos
export MONGO_USERNAME=kytos
export MONGO_DBNAME=kytos
export MONGO_HOST_SEEDS=127.0.0.1:27017

kytosd -f -E --database mongodb
```
