# Overview

This NApp integrates Kafka with the Kytos SDN platform to enable event-driven messaging and real-time event streaming.

# Features

- Asynchronous Kafka producer with support for compression and acknowledgments.
- Event listener for new KytosEvents, which then serializes and publishes events to Kafka.
- Resilient Kafka client with automatic retries for connectivity issues.
- Uses Main asyncio loop to handle asynchronous tasks serialization and publishing.
- Regex filtering logic to handle serialization permission easily and efficiently.
- Endpoints to dynamically add, list, and remove serialization permissions.

# Requirements

- [aiokafka](https://aiokafka.readthedocs.io/en/stable/)

# Events

## Subscribed

- All core NApps (`kytos/*` and `kytos.*`)
    - `kytos/mef_eline.*`
    - `kytos/of_core.*`
    - `kytos/flow_manager.*`
    - `kytos/topology.*`
    - `kytos/of_lldp.*`
    - `kytos/pathfinder.*`
    - `kytos/maintenance.*`

# Filtering

Event consumption and serialization follows the principle of `least privilege`, meaning events must be explicitly accepted to be allowed to be propagated to Kafka. Filtering logic uses `regex` to quickly accept or deny incoming events, based on preset patterns. Currently, the NApp mainly supports wildcard logic, but can be easily extended for matching as well:

## Wildcard

The expected functionality, takes in any regex logic and compares values to them

```
# Example
{"pattern": "kytos[./](.*)", "description": "Allows all core NApps"}
```

## Match

To achieve match functionality, you must start and end your match with `^` and `$` respectively.

```
# Example
{"pattern": "^test/something.created$", "description": "Allow ONLY this pattern"}
```

# Endpoints

## /v1/create

Creates a Filter object to be used in the filtering pipeline. Requires JSON data like the following:

```
{
    "pattern": str,
    "description": str # OPTIONAL (If not provided, will become N/A) 
}
```

If the given pattern already exists or is an invalid regular expression, the endpoint will return a 400 status code and the exception message.

## /v1/list

Lists the summary of all Filter objects in the filtering pipeline. The response looks similar to the following:

```
[
    {
        "pattern": str,
        "mutable": bool,
        "description": str
    },
    {
        "pattern": str,
        ...
    },
    ...
]
```

## /v1/delete

Deletes a Filter object from the filtering pipeline. Requires JSON data like the following:

```
{
    "pattern": str
}
```

If the given pattern does not exist or is immutable, the endpoint will return a 400 status code and the exception message.

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
