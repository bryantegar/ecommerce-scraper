"""Worker Lazada — Keyword + Store"""
import logging, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import init_db, log_job_start, log_job_finish, save_lazada_items
from services.service_lazada import ServiceLazada
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)
MAX_PAGES = int(os.getenv("LAZADA_MAX_PAGES", 3))


class WorkerLazada(BaseWorker):
    def __init__(self):
        super().__init__()
        init_db()
        self.service = ServiceLazada()
        logger.info(f"WorkerLazada siap. MAX_PAGES={MAX_PAGES}")

    @property
    def platform(self): return "lazada"

    @property
    def tube_name(self): return "ecommerce_crawler_lazada_keyword"

    def process_job(self, job_data: dict) -> bool:
        keyword   = job_data.get("content")
        job_id    = job_data.get("job_id", "unknown")
        job_type  = job_data.get("job_type", "keyword")
        store_url = job_data.get("store_url")
        max_page  = job_data.get("max_count", MAX_PAGES)

        if not keyword and not store_url:
            logger.error("Job tidak punya 'content' atau 'store_url'. Skip.")
            return False

        cookies = self.get_cookies()
        if not cookies:
            raise RuntimeError("Cookie Lazada tidak tersedia")

        log_job_start(job_id, self.platform, keyword=keyword, store_url=store_url, job_type=job_type)
        total_saved = 0
        final_status = "success"
        error_msg = None

        try:
            for page_num in range(1, max_page + 1):
                logger.info(f"  📄 Lazada page {page_num}/{max_page}...")

                if job_type == "store" and store_url:
                    resp = self.service.scrape_lazada_store(store_url, page=page_num)
                else:
                    resp = self.service.scrape_lazada_keyword(keyword, cookies=cookies, page=page_num)

                if resp is None or resp.status_code != 200:
                    logger.warning(f"  ⚠️  Status {resp.status_code if resp else 'None'}")
                    break

                resp_json = resp.json()
                items = resp_json.get("mods", {}).get("listItems", [])

                if not items:
                    logger.info(f"  ℹ️  Tidak ada items di page {page_num}. Stop.")
                    break

                logger.info(f"  ✅ {len(items)} items ditemukan di page {page_num}")
                name = keyword or store_url

                saved = save_lazada_items(
                    job_id=job_id,
                    keyword=name if job_type == "keyword" else None,
                    resp_json=resp_json,
                    page_number=page_num,
                    store_url=store_url,
                )

                from output.output_json import save_json_output
                save_json_output(
                    platform=self.platform,
                    job_type=job_type,
                    name=name,
                    items=items,
                    page_number=page_num,
                    job_id=job_id,
                )

                total_saved += saved

        except Exception as e:
            final_status = "failed"
            error_msg = str(e)
            raise
        finally:
            log_job_finish(job_id, final_status, total_saved, error_msg)

        logger.info(f"✅ Lazada '{keyword}': {total_saved} items, status={final_status}")
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
    WorkerLazada().run()
