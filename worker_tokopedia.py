"""
workers/worker_tokopedia.py
============================
Support job_type:
    - keyword : scrape produk berdasarkan keyword
    - store   : scrape semua produk dari toko
    - review  : scrape review produk

Env vars:
    TOKOPEDIA_MAX_PAGES=3
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db, log_job_start, log_job_finish, save_tokopedia_items
from services.service_tokopedia import ServiceTokopedia
from workers.base_worker import BaseWorker

logger     = logging.getLogger(__name__)
MAX_PAGES  = int(os.getenv("TOKOPEDIA_MAX_PAGES", 3))

TUBE_KEYWORD = "ecommerce_crawler_tokopedia_keyword"
TUBE_STORE   = "ecommerce_crawler_tokopedia_store"
TUBE_REVIEW  = "ecommerce_crawler_tokopedia_review"


class WorkerTokopedia(BaseWorker):
    def __init__(self, tube: str = TUBE_KEYWORD):
        super().__init__()
        init_db()
        self.service    = ServiceTokopedia()
        self._tube_name = tube
        logger.info(f"WorkerTokopedia siap. Tube={tube} MAX_PAGES={MAX_PAGES}")

    @property
    def platform(self) -> str:
        return "tokopedia"

    @property
    def tube_name(self) -> str:
        return self._tube_name

    # ── Main job handler ──────────────────────────────────────────────────────

    def process_job(self, job_data: dict) -> bool:
        job_type    = job_data.get("job_type", "keyword")
        job_id      = job_data.get("job_id", "unknown")
        keyword     = job_data.get("content") if job_type == "keyword" else None
        store_url   = job_data.get("store_url") or (job_data.get("content") if job_type == "store" else None)
        product_url = job_data.get("product_url") or (job_data.get("content") if job_type == "review" else None)
        max_page    = job_data.get("max_count", MAX_PAGES)

        if job_type == "keyword" and not keyword:
            logger.error("Keyword job tapi tidak ada 'content'. Skip.")
            return False
        if job_type == "store" and not store_url:
            logger.error("Store job tapi tidak ada 'store_url'/'content'. Skip.")
            return False
        if job_type == "review" and not product_url:
            logger.error("Review job tapi tidak ada 'product_url'/'content'. Skip.")
            return False

        name = keyword or store_url or product_url

        log_job_start(job_id, self.platform, keyword=keyword, store_url=store_url, job_type=job_type)
        total_saved  = 0
        final_status = "success"
        error_msg    = None

        try:
            if job_type == "review":
                total_saved = self._process_review(job_id, product_url, max_page)
            else:
                total_saved = self._process_pages(job_id, job_type, keyword, store_url, name, max_page)

        except Exception as e:
            final_status = "failed"
            error_msg    = str(e)
            logger.error(f"❌ Tokopedia job [{job_id}] error: {e}")
            raise
        finally:
            log_job_finish(job_id, final_status, total_saved, error_msg)

        logger.info(f"✅ Tokopedia '{name}': {total_saved} items saved, status={final_status}")
        return True

    # ── Keyword & Store ───────────────────────────────────────────────────────

    def _process_pages(
        self,
        job_id: str,
        job_type: str,
        keyword: str,
        store_url: str,
        name: str,
        max_page: int,
    ) -> int:
        total = 0
        for page_num in range(1, max_page + 1):
            logger.info(f"  📄 Tokopedia {job_type} page {page_num}/{max_page}...")

            if job_type == "store":
                resp = self.service.scrape_tokopedia_store(store_url, page=page_num)
            else:
                resp = self.service.scrape_tokopedia_keyword(keyword, page=page_num)

            if resp is None or resp.status_code != 200:
                code = resp.status_code if resp else "None"
                logger.warning(f"  ⚠️  HTTP {code} di page {page_num}. Stop.")
                break

            resp_json = resp.json()

            try:
                if job_type == "store":
                    products = resp_json[0]["data"]["GetShopProduct"]["data"]
                else:
                    products = resp_json[0]["data"]["searchProductV5"]["data"]["products"]
            except (KeyError, IndexError, TypeError):
                logger.warning(f"  ⚠️  Tidak bisa parse response page {page_num}. Stop.")
                break

            if not products:
                logger.info(f"  ℹ️  Tidak ada products di page {page_num}. Stop.")
                break

            logger.info(f"  ✅ {len(products)} items ditemukan")

            saved = self.save_and_publish(
                items=products,
                save_fn=lambda **kw: save_tokopedia_items(resp_json=resp_json, **kw),
                job_id=job_id,
                name=name,
                job_type=job_type,
                page_number=page_num,
                store_url=store_url,
            )
            total += saved

        return total

    # ── Review ────────────────────────────────────────────────────────────────

    def _process_review(self, job_id: str, product_url: str, max_page: int) -> int:
        total = 0
        for page_num in range(1, max_page + 1):
            logger.info(f"  💬 Tokopedia review page {page_num}/{max_page}...")

            resp = self.service.scrape_tokopedia_review(product_url, page=page_num)
            if resp is None or resp.status_code != 200:
                code = resp.status_code if resp else "None"
                logger.warning(f"  ⚠️  HTTP {code} di review page {page_num}. Stop.")
                break

            resp_json = resp.json()

            try:
                reviews = resp_json[0]["data"]["productrevGetProductReviewList"]["list"]
            except (KeyError, IndexError, TypeError):
                logger.warning(f"  ⚠️  Tidak bisa parse review response page {page_num}. Stop.")
                break

            if not reviews:
                logger.info(f"  ℹ️  Tidak ada review di page {page_num}. Stop.")
                break

            logger.info(f"  ✅ {len(reviews)} reviews ditemukan")

            saved = self.save_and_publish(
                items=reviews,
                save_fn=lambda **kw: save_tokopedia_items(resp_json=resp_json, **kw),
                job_id=job_id,
                name=product_url,
                job_type="review",
                page_number=page_num,
                product_url=product_url,
            )
            total += saved

        return total


# ── Entrypoint ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-type", choices=["keyword", "store", "review"], default="keyword")
    args = parser.parse_args()

    tube_map = {
        "keyword": TUBE_KEYWORD,
        "store":   TUBE_STORE,
        "review":  TUBE_REVIEW,
    }
    WorkerTokopedia(tube=tube_map[args.job_type]).run()
