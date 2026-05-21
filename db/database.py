"""
Database Manager — PostgreSQL
==============================
Support: Shopee, Tokopedia, Lazada, Blibli
"""

import json
import logging
import os
from typing import Optional

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", 5433)),
    "dbname":   os.getenv("POSTGRES_DB", "ecommerce_scraper"),
    "user":     os.getenv("POSTGRES_USER", "scraper"),
    "password": os.getenv("POSTGRES_PASSWORD", "scraper123"),
}

_pool: Optional[ThreadedConnectionPool] = None


def get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(minconn=1, maxconn=10, **DB_CONFIG)
        logger.info("PostgreSQL connection pool dibuat.")
    return _pool


def get_conn():
    return get_pool().getconn()


def release_conn(conn):
    get_pool().putconn(conn)


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS scrape_results (
    id              BIGSERIAL PRIMARY KEY,
    platform        VARCHAR(50)     NOT NULL,
    keyword         VARCHAR(500),
    store_url       VARCHAR(1000),
    job_id          VARCHAR(100),
    job_type        VARCHAR(20)     DEFAULT 'keyword',  -- keyword / store

    product_id      VARCHAR(200),
    product_name    TEXT,
    product_url     TEXT,
    price           BIGINT,
    price_min       BIGINT,
    price_max       BIGINT,
    currency        VARCHAR(10)     DEFAULT 'IDR',

    rating          NUMERIC(3,2),
    rating_count    INTEGER,
    sold_count      INTEGER,
    stock           INTEGER,

    shop_id         VARCHAR(200),
    shop_name       VARCHAR(500),
    shop_location   VARCHAR(200),

    image_url       TEXT,
    raw_data        JSONB,
    scraped_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    page_number     INTEGER         DEFAULT 1,

    CONSTRAINT uq_product_per_job UNIQUE (job_id, product_id)
);

CREATE TABLE IF NOT EXISTS scrape_jobs (
    id              BIGSERIAL PRIMARY KEY,
    job_id          VARCHAR(100)    UNIQUE NOT NULL,
    platform        VARCHAR(50)     NOT NULL,
    keyword         VARCHAR(500),
    store_url       VARCHAR(1000),
    job_type        VARCHAR(20)     DEFAULT 'keyword',
    status          VARCHAR(20)     NOT NULL DEFAULT 'running',
    items_saved     INTEGER         DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_scrape_results_platform   ON scrape_results(platform);
CREATE INDEX IF NOT EXISTS idx_scrape_results_keyword    ON scrape_results(keyword);
CREATE INDEX IF NOT EXISTS idx_scrape_results_scraped_at ON scrape_results(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_scrape_results_job_type   ON scrape_results(job_type);
"""


def init_db():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLES_SQL)
        conn.commit()
        logger.info("✅ Database schema siap.")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Gagal init database: {e}")
        raise
    finally:
        release_conn(conn)


def log_job_start(job_id, platform, keyword=None, store_url=None, job_type="keyword"):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scrape_jobs (job_id, platform, keyword, store_url, job_type, status)
                VALUES (%s, %s, %s, %s, %s, 'running')
                ON CONFLICT (job_id) DO UPDATE SET status='running', started_at=NOW()
            """, (job_id, platform, keyword, store_url, job_type))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.warning(f"log_job_start error: {e}")
    finally:
        release_conn(conn)


def log_job_finish(job_id, status, items_saved=0, error=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scrape_jobs
                SET status=%s, items_saved=%s, error_message=%s, finished_at=NOW()
                WHERE job_id=%s
            """, (status, items_saved, error, job_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.warning(f"log_job_finish error: {e}")
    finally:
        release_conn(conn)


def _save_items(rows: list):
    """Generic insert rows ke scrape_results."""
    if not rows:
        return 0
    conn = get_conn()
    saved = 0
    try:
        with conn.cursor() as cur:
            for row in rows:
                try:
                    cur.execute("""
                        INSERT INTO scrape_results (
                            platform, keyword, store_url, job_id, job_type,
                            product_id, product_name, product_url,
                            price, price_min, price_max,
                            rating, rating_count, sold_count, stock,
                            shop_id, shop_name, shop_location,
                            image_url, raw_data, page_number
                        ) VALUES (
                            %(platform)s, %(keyword)s, %(store_url)s, %(job_id)s, %(job_type)s,
                            %(product_id)s, %(product_name)s, %(product_url)s,
                            %(price)s, %(price_min)s, %(price_max)s,
                            %(rating)s, %(rating_count)s, %(sold_count)s, %(stock)s,
                            %(shop_id)s, %(shop_name)s, %(shop_location)s,
                            %(image_url)s, %(raw_data)s, %(page_number)s
                        )
                        ON CONFLICT (job_id, product_id) DO UPDATE SET
                            product_name = EXCLUDED.product_name,
                            price        = EXCLUDED.price,
                            sold_count   = EXCLUDED.sold_count,
                            raw_data     = EXCLUDED.raw_data,
                            scraped_at   = NOW()
                    """, {**row, "raw_data": psycopg2.extras.Json(row.get("raw_data", {}))})
                    saved += 1
                except Exception as e:
                    logger.warning(f"  Skip item {row.get('product_id','?')}: {e}")
        conn.commit()
        logger.info(f"  💾 {saved}/{len(rows)} items tersimpan ke PostgreSQL.")
    except Exception as e:
        conn.rollback()
        logger.error(f"_save_items error: {e}")
        raise
    finally:
        release_conn(conn)
    return saved


# ─────────────────────────────────────────────
# SHOPEE
# ─────────────────────────────────────────────

def save_shopee_items(job_id, keyword, items, page_number=1, store_url=None) -> int:
    rows = []
    job_type = "store" if store_url else "keyword"
    for item in items:
        ib = item.get("item_basic") or item
        price     = ib.get("price")
        product_id = str(ib.get("itemid", ""))
        shop_id    = str(ib.get("shopid", ""))
        image      = ib.get("image", "")
        if image:
            image = f"https://cf.shopee.co.id/file/{image}"
        rating_cnt = ib.get("item_rating", {}).get("rating_count", [0])
        if isinstance(rating_cnt, list):
            rating_cnt = rating_cnt[0] if rating_cnt else 0
        rows.append({
            "platform": "shopee", "keyword": keyword, "store_url": store_url,
            "job_id": job_id, "job_type": job_type,
            "product_id": product_id,
            "product_name": ib.get("name", ""),
            "product_url": f"https://shopee.co.id/product/{shop_id}/{product_id}" if product_id else None,
            "price": price, "price_min": ib.get("price_min"), "price_max": ib.get("price_max"),
            "rating": ib.get("item_rating", {}).get("rating_star"),
            "rating_count": rating_cnt,
            "sold_count": ib.get("historical_sold") or ib.get("sold", 0),
            "stock": ib.get("stock", 0),
            "shop_id": shop_id, "shop_name": ib.get("shop_name", ""),
            "shop_location": ib.get("shop_location", ""),
            "image_url": image, "raw_data": ib, "page_number": page_number,
        })
    return _save_items(rows)


# ─────────────────────────────────────────────
# TOKOPEDIA
# ─────────────────────────────────────────────

def save_tokopedia_items(job_id, keyword, resp_json, page_number=1, store_url=None) -> int:
    rows = []
    job_type = "store" if store_url else "keyword"
    try:
        if store_url:
            # Store scraping response format
            products = resp_json[0]["data"]["GetShopProduct"]["data"]
        else:
            # Keyword scraping response format
            products = resp_json[0]["data"]["searchProductV5"]["data"]["products"]
    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Tidak bisa parse Tokopedia response: {e}")
        return 0

    for p in products:
        price_raw = p.get("price", {})
        price_num = price_raw.get("number") if isinstance(price_raw, dict) else None
        shop = p.get("shop", {})
        rows.append({
            "platform": "tokopedia", "keyword": keyword, "store_url": store_url,
            "job_id": job_id, "job_type": job_type,
            "product_id": str(p.get("id") or p.get("product_id", "")),
            "product_name": p.get("name", ""),
            "product_url": p.get("url") or p.get("product_url", ""),
            "price": int(price_num) if price_num else None,
            "price_min": None, "price_max": None,
            "rating": p.get("rating"),
            "rating_count": None,
            "sold_count": None,
            "stock": None,
            "shop_id": str(shop.get("id", "")),
            "shop_name": shop.get("name", ""),
            "shop_location": shop.get("city", ""),
            "image_url": p.get("mediaURL", {}).get("image") if isinstance(p.get("mediaURL"), dict) else None,
            "raw_data": p, "page_number": page_number,
        })
    return _save_items(rows)


# ─────────────────────────────────────────────
# LAZADA
# ─────────────────────────────────────────────

def save_lazada_items(job_id, keyword, resp_json, page_number=1, store_url=None) -> int:
    rows = []
    job_type = "store" if store_url else "keyword"
    try:
        items = resp_json.get("mods", {}).get("listItems", [])
    except AttributeError:
        logger.warning("Tidak bisa parse Lazada response")
        return 0

    for p in items:
        price_str = p.get("price", "0").replace(".", "").replace(",", "")
        try:
            price = int(float(price_str))
        except Exception:
            price = None
        rows.append({
            "platform": "lazada", "keyword": keyword, "store_url": store_url,
            "job_id": job_id, "job_type": job_type,
            "product_id": str(p.get("itemId", p.get("productId", ""))),
            "product_name": p.get("name", ""),
            "product_url": p.get("productUrl", ""),
            "price": price, "price_min": None, "price_max": None,
            "rating": p.get("ratingScore"),
            "rating_count": p.get("review"),
            "sold_count": None, "stock": None,
            "shop_id": str(p.get("sellerId", "")),
            "shop_name": p.get("sellerName", ""),
            "shop_location": None,
            "image_url": p.get("image", ""),
            "raw_data": p, "page_number": page_number,
        })
    return _save_items(rows)


# ─────────────────────────────────────────────
# BLIBLI
# ─────────────────────────────────────────────

def save_blibli_items(job_id, keyword, resp_json, page_number=1, store_url=None) -> int:
    rows = []
    job_type = "store" if store_url else "keyword"
    try:
        products = resp_json.get("data", {}).get("products", [])
    except AttributeError:
        logger.warning("Tidak bisa parse Blibli response")
        return 0

    for p in products:
        price_raw = p.get("price", {})
        price = price_raw.get("minPrice") if isinstance(price_raw, dict) else None
        merchant = p.get("merchant", {})
        rows.append({
            "platform": "blibli", "keyword": keyword, "store_url": store_url,
            "job_id": job_id, "job_type": job_type,
            "product_id": str(p.get("itemSku", p.get("id", ""))),
            "product_name": p.get("name", ""),
            "product_url": f"https://www.blibli.com{p.get('url', '')}",
            "price": int(price) if price else None,
            "price_min": price_raw.get("minPrice") if isinstance(price_raw, dict) else None,
            "price_max": price_raw.get("maxPrice") if isinstance(price_raw, dict) else None,
            "rating": p.get("review", {}).get("rating") if isinstance(p.get("review"), dict) else None,
            "rating_count": p.get("review", {}).get("count") if isinstance(p.get("review"), dict) else None,
            "sold_count": None, "stock": None,
            "shop_id": str(merchant.get("id", "")),
            "shop_name": merchant.get("name", ""),
            "shop_location": merchant.get("city", ""),
            "image_url": p.get("images", [None])[0] if p.get("images") else None,
            "raw_data": p, "page_number": page_number,
        })
    return _save_items(rows)
