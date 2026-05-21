"""
Publisher — Kafka Publisher untuk Ecommerce Scraper
====================================================
Wrapper dari kafka_helpers.py kantor.

Format topic (konfirmasi ke kantor):
    ecommerce.shopee.keyword
    ecommerce.tokopedia.keyword
    ecommerce.lazada.keyword
    ecommerce.blibli.keyword
    ecommerce.shopee.store
    dst...

Cara pakai di worker:
    from publisher import publish_items
    publish_items(platform="shopee", job_type="keyword", items=items, keyword="Dancow")
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Topic prefix — sesuaikan dengan yang kantor pakai
TOPIC_PREFIX = os.getenv("KAFKA_TOPIC_PREFIX", "ecommerce")


def build_topic(platform: str, job_type: str) -> str:
    """
    Build nama topic Kafka.
    Contoh: ecommerce.shopee.keyword
    """
    return f"{TOPIC_PREFIX}.{platform}.{job_type}"


def publish_items(
    platform: str,
    job_type: str,
    items: list,
    keyword: str = None,
    store_url: str = None,
    job_id: str = None,
    page_number: int = 1,
) -> int:
    """
    Publish hasil scrape ke Kafka topic.
    Return jumlah item yang berhasil di-publish.
    """
    try:
        from libs.kafka_helpers import publish_kafka
    except ImportError:
        logger.warning("kafka_helpers tidak ditemukan. Skip publish ke Kafka.")
        return 0

    topic = build_topic(platform, job_type)
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
            data_str = json.dumps(message, ensure_ascii=False)
            publish_kafka(topic, data_str)
            published += 1
        except Exception as e:
            logger.error(f"  Gagal publish item ke Kafka topic '{topic}': {e}")

    if published > 0:
        logger.info(f"  📨 {published}/{len(items)} messages published ke Kafka topic '{topic}'")

    return published
