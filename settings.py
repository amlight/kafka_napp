"""Module with the Constants used in the italovalcy/testnapp."""

# Location of the Kafka server
BOOTSTRAP_SERVERS = "localhost:9092"

# Acknowledgements: (str | int) A setting that sets the acknowledgement of messages to Kafka.
# Available options are 0, 1 and "all"
ACKS = 0

# Number of partitions per topic
DEFAULT_NUM_PARTITIONS = 1

# Ignored events ( set[str] )
IGNORED_EVENTS = {}

# Number of times the partition is replicated across brokers. Should be <= the number of brokers available
REPLICATION_FACTOR = 1

# The name of the topic we will be sending/consuming from
TOPIC_NAME = "event_logs"

# The type of compression we would like to send with
COMPRESSION_TYPE = "gzip"