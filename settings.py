"""Module with the Constants used in the kafka_events."""

# Location of the Kafka server
BOOTSTRAP_SERVERS = "localhost:9092"

# Acknowledgements: (str | int) A setting that sets the acknowledgement of messages to Kafka.
# Available options are 0, 1 and "all"
#   0: No acknowledgements. Zero latency but provides no guarantees on delivery.
#   1: Leader acknowledgement. Some latency but provides a guarantee that the message
#      Was sent to the leader.
#   all: Leader & replica acknowledgement: Highest latency but provides the maximum amount
#        of message delivery guarantees. It requires the leader AND all in-sync replicas
#        To acknowledge the delivery of the message.
ACKS = "all"

# Idempotence: (bool) A setting that tells aiokafka to keep track of all messages,
# attaching IDs to them. This removes possible duplicates at the cost increased
# resource consumption
# IMPORTANT: ENABLE_IDEMPOTENCE requires acks == "all"
ENABLE_ITEMPOTENCE = True

# Timeout: (int) The time (in milliseconds) that aiokafka waits when trying to
# sends requests to Kafka
REQUEST_TIMEOUT_MS = 10_000

# Allowed Retries: (int) The amount of retries that we want send_message to be allowed
# to do if it cannot connect, cannot send a message, or a timeout occurs.
ALLOWED_RETRIES = 10

# Number of partitions per topic
DEFAULT_NUM_PARTITIONS = 1

# Ruleset: (list[dict[str: str]]) The regex rules, specifying the pattern an. Currently supports
# all core NApps
RULE_SET = [
    {"pattern": r"kytos[./](.*)", "description": "Allows all core NApps"}
]

# Number of times the partition is replicated across brokers. Should be <= the number of brokers available
REPLICATION_FACTOR = 1

# The name of the topic we will be sending/consuming from
TOPIC_NAME = "event_logs"

# The type of compression we would like to send with
COMPRESSION_TYPE = "gzip"