"""
push_jobs.py — Manual Job Pusher
=================================
Support semua platform dan semua job type.

Usage:
    # Keyword - semua platform
    python push_jobs.py

    # Keyword - platform tertentu + keyword spesifik
    python push_jobs.py --platform tokopedia shopee --keywords "Dancow" "Nutrilon"

    # Store - push URL toko
    python push_jobs.py --platform shopee --job-type store --store-urls "https://shopee.co.id/dancow.id"

    # Review - push URL produk
    python push_jobs.py --platform tokopedia --job-type review --product-urls "https://tokopedia.com/..."

    # Force push (skip cookie check)
    python push_jobs.py --platform lazada --force
"""

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime

import greenstalk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cookie_manager.cookie_manager import CookieManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BEANS_HOST = os.getenv("BEANS_HOST", "localhost")
BEANS_PORT = int(os.getenv("BEANS_PORT", 11300))

# ── Tube mapping (platform + job_type → tube name) ────────────────────────────

TUBE_MAP = {
    "tokopedia": {
        "keyword": "ecommerce_crawler_tokopedia_keyword",
        "store":   "ecommerce_crawler_tokopedia_store",
        "review":  "ecommerce_crawler_tokopedia_review",
    },
    "shopee": {
        "keyword": "ecommerce_crawler_shopee_keyword",
        "store":   "ecommerce_crawler_shopee_store",
        "review":  "ecommerce_crawler_shopee_review",
    },
    "lazada": {
        "keyword": "ecommerce_crawler_lazada_keyword",
        "store":   "ecommerce_crawler_lazada_store",
        "review":  "ecommerce_crawler_lazada_review",
    },
    "blibli": {
        "keyword": "ecommerce_crawler_blibli_keyword",
        "store":   "ecommerce_crawler_blibli_store",
        "review":  "ecommerce_crawler_blibli_review",
    },
}

PLATFORMS_NEED_COOKIE = {"shopee", "lazada"}

# Default keywords kalau tidak di-specify
DEFAULT_KEYWORDS = [
    "Friesland Campina", "SGM", "Vidoran", "Dancow",
    "Shanghiang Perkasa", "Bebelac", "Lactogrow", "Healthy Way",
    "Abbot", "Mead Johnson", "Weyth Nutrition", "Nutrilon",
]


# ── Cookie check ──────────────────────────────────────────────────────────────

def _check_cookie(platform: str, force: bool) -> bool:
    """Return True jika bisa lanjut push."""
    if force or platform not in PLATFORMS_NEED_COOKIE:
        return True
    cm = CookieManager()
    if not cm.is_valid(platform):
        logger.warning(
            f"⏭️  Skip {platform}: cookie tidak valid. "
            f"Jalankan: python cookie_manager/login_handler.py --platform {platform}"
        )
        return False
    ttl_min = cm.ttl_seconds(platform) // 60
    logger.info(f"  🍪 Cookie {platform} valid (TTL: {ttl_min} menit)")
    return True


# ── Beanstalkd push helper ────────────────────────────────────────────────────

def _push_jobs(platform: str, job_type: str, payloads: list, force: bool = False) -> int:
    if not _check_cookie(platform, force):
        return 0

    tube = TUBE_MAP[platform][job_type]

    try:
        client = greenstalk.Client((BEANS_HOST, BEANS_PORT), use=tube)
    except Exception as e:
        logger.error(f"❌ Gagal koneksi Beanstalkd: {e}")
        return 0

    pushed = 0
    for payload in payloads:
        try:
            client.put(json.dumps(payload))
            pushed += 1
            logger.info(f"  [{pushed}] PUSHED → {payload.get('content', payload.get('product_url', '?'))}")
        except Exception as e:
            logger.error(f"  Gagal push payload: {e}")

    client.close()
    return pushed


# ── Job builders ──────────────────────────────────────────────────────────────

def push_keyword_jobs(platform: str, keywords: list, force: bool = False) -> int:
    payloads = [
        {
            "job_id":    str(uuid.uuid4()),
            "platform":  platform,
            "content":   keyword,
            "job_type":  "keyword",
            "count":     0,
            "max_count": 3,
            "pushed_at": datetime.utcnow().isoformat(),
        }
        for keyword in keywords
    ]
    return _push_jobs(platform, "keyword", payloads, force)


def push_store_jobs(platform: str, store_urls: list, force: bool = False) -> int:
    payloads = [
        {
            "job_id":    str(uuid.uuid4()),
            "platform":  platform,
            "content":   store_url,
            "store_url": store_url,
            "job_type":  "store",
            "count":     0,
            "max_count": 3,
            "pushed_at": datetime.utcnow().isoformat(),
        }
        for store_url in store_urls
    ]
    return _push_jobs(platform, "store", payloads, force)


def push_review_jobs(platform: str, product_urls: list, force: bool = False) -> int:
    payloads = [
        {
            "job_id":      str(uuid.uuid4()),
            "platform":    platform,
            "content":     product_url,
            "product_url": product_url,
            "job_type":    "review",
            "count":       0,
            "max_count":   5,  # review biasanya lebih banyak page
            "pushed_at":   datetime.utcnow().isoformat(),
        }
        for product_url in product_urls
    ]
    return _push_jobs(platform, "review", payloads, force)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Push jobs ke Beanstalkd queue")
    parser.add_argument(
        "--platform", nargs="+",
        choices=list(TUBE_MAP.keys()) + ["all"],
        default=["all"],
        help="Platform yang mau di-push. Default: all"
    )
    parser.add_argument(
        "--job-type", choices=["keyword", "store", "review"],
        default="keyword",
        help="Tipe job. Default: keyword"
    )
    parser.add_argument(
        "--keywords", nargs="+", default=None,
        help="Override keyword list (untuk job_type=keyword)"
    )
    parser.add_argument(
        "--store-urls", nargs="+", default=None,
        help="URL toko (untuk job_type=store)"
    )
    parser.add_argument(
        "--product-urls", nargs="+", default=None,
        help="URL produk (untuk job_type=review)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=None,
        help="Override max_count (jumlah halaman yang di-scrape)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Skip cookie check (untuk platform yang butuh login)"
    )
    args = parser.parse_args()

    platforms = list(TUBE_MAP.keys()) if "all" in args.platform else args.platform

    print(f"\n🚀 Push Jobs — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Platform   : {platforms}")
    print(f"   Job type   : {args.job_type}")
    print(f"   Beanstalkd : {BEANS_HOST}:{BEANS_PORT}\n")

    # Validasi input per job_type
    if args.job_type == "store" and not args.store_urls:
        print("❌ Gunakan --store-urls untuk job_type=store")
        print("   Contoh: python push_jobs.py --platform shopee --job-type store --store-urls 'https://shopee.co.id/xxx'")
        sys.exit(1)
    if args.job_type == "review" and not args.product_urls:
        print("❌ Gunakan --product-urls untuk job_type=review")
        print("   Contoh: python push_jobs.py --platform tokopedia --job-type review --product-urls 'https://tokopedia.com/xxx'")
        sys.exit(1)

    total = 0
    for platform in platforms:
        print(f"\n📦 {platform.upper()}")

        if args.job_type == "keyword":
            keywords = args.keywords or DEFAULT_KEYWORDS
            pushed   = push_keyword_jobs(platform, keywords, args.force)

        elif args.job_type == "store":
            pushed = push_store_jobs(platform, args.store_urls, args.force)

        elif args.job_type == "review":
            pushed = push_review_jobs(platform, args.product_urls, args.force)

        else:
            pushed = 0

        total += pushed
        if pushed > 0:
            print(f"   ✅ {pushed} jobs pushed ke tube '{TUBE_MAP[platform][args.job_type]}'")

    print(f"\n✅ Total: {total} jobs pushed\n")


if __name__ == "__main__":
    main()
