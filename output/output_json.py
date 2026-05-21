"""
Output JSON Helper
==================
Simpan hasil scrape ke folder output/{platform}/ sebagai JSON
untuk cek manual dan backup.

Format file: output/shopee/shopee_keyword_Dancow_page1_20260518_181200.json
"""

import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

OUTPUT_BASE = os.getenv("OUTPUT_DIR", "output")


def save_json_output(
    platform: str,
    job_type: str,       # "keyword" atau "store"
    name: str,           # keyword atau store name
    items: list,
    page_number: int = 1,
    job_id: str = None,
) -> str:
    """
    Simpan items ke JSON file.
    Return path file yang disimpan.
    """
    folder = os.path.join(OUTPUT_BASE, platform)
    os.makedirs(folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = name.replace(" ", "_").replace("/", "-")[:50]
    filename = f"{platform}_{job_type}_{safe_name}_page{page_number}_{timestamp}.json"
    filepath = os.path.join(folder, filename)

    payload = {
        "platform": platform,
        "job_type": job_type,
        "name": name,
        "page": page_number,
        "job_id": job_id,
        "scraped_at": datetime.now().isoformat(),
        "total_items": len(items),
        "items": items,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(f"  📄 JSON saved: {filepath} ({len(items)} items)")
    return filepath
