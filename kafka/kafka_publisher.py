"""
Kafka Publisher
===============
Publish hasil scrape ke Kafka topic.

Topic naming:
    ecommerce.shopee.keyword
    ecommerce.tokopedia.keyword
    ecommerce.lazada.keyword
    ecommerce.blibli.keyword
    ecommerce.shopee.store
    dst...

Cara pakai:
    publisher = KafkaPublisher()
    publisher.publish(platform="shopee", job_type="keyword", items=items, keyword="Dancow")
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9093")
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() == "true"


class KafkaPublisher:
    def __init__(self):
        self._producer = None
        self._available = False

        if not KAFKA_ENABLED:
            logger.info("Kafka disabled via KAFKA_ENABLED=false")
            return

        self._connect()

    def _connect(self):
        try:
            from kafka import KafkaProducer
            self._producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                # Retry config
                retries=3,
                retry_backoff_ms=500,
                request_timeout_ms=10000,
            )
            self._available = True
            logger.info(f"✅ Kafka terhubung ke {KAFKA_BROKER}")
        except ImportError:
            logger.warning("kafka-python tidak terinstall. Jalankan: pip install kafka-python")
            self._available = False
        except Exception as e:
            logger.warning(f"⚠️  Kafka tidak tersedia ({KAFKA_BROKER}): {e}")
            logger.warning("   Worker tetap jalan, hasil hanya disimpan ke PostgreSQL + JSON.")
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def publish(
        self,
        platform: str,
        job_type: str,
        items: list,
        keyword: str = None,
        store_url: str = None,
        job_id: str = None,
        page_number: int = 1,
    ) -> int:
        """
        Publish items ke Kafka topic.
        Return jumlah message yang berhasil di-publish.
        """
        if not self._available:
            return 0

        topic = f"ecommerce.{platform}.{job_type}"
        published = 0

        for item in items:
            message = {
                "platform": platform,
                "job_type": job_type,
                "keyword": keyword,
                "store_url": store_url,
                "job_id": job_id,
                "page": page_number,
                "scraped_at": datetime.now(tz=timezone.utc).isoformat(),
                "data": item,
            }
            try:
                future = self._producer.send(
                    topic=topic,
                    key=job_id,
                    value=message,
                )
                future.get(timeout=5)  # Block sampai konfirmasi
                published += 1
            except Exception as e:
                logger.error(f"  Gagal publish ke Kafka topic {topic}: {e}")

        if published > 0:
            logger.info(f"  📨 {published}/{len(items)} messages published ke Kafka topic '{topic}'")

        return published

    def close(self):
        if self._producer:
            self._producer.flush()
            self._producer.close()


# Singleton instance
_publisher: Optional[KafkaPublisher] = None


def get_publisher() -> KafkaPublisher:
    global _publisher
    if _publisher is None:
        _publisher = KafkaPublisher()
    return _publisher
