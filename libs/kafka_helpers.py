from kafka import KafkaProducer
from kafka.errors import KafkaError
from settings import KAFKA
from .logger import printinfo


def publish_kafka(topic, data: str):
    producer = None
    producer = KafkaProducer(
        bootstrap_servers=KAFKA['default']['bootstrap_servers'], max_request_size=10*1024*1024)
    future = producer.send(topic, data.encode())
    try:
        record_metadata = future.get(timeout=10)
        printinfo('Topic: {};Partition: {};Offset: {}'.format(
            record_metadata.topic, record_metadata.partition, record_metadata.offset
        ))
        return True
    except KafkaError as e:
        # Decide what to do if produce request failed...
        raise
    except Exception as e:
        raise
    finally:
        if producer:
            producer.close()
