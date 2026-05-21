"""
workers/base_worker.py
=======================
Base class untuk semua worker ecommerce scraper.

Support job types:
    - keyword  : scrape produk berdasarkan keyword pencarian
    - store    : scrape semua produk dari toko tertentu
    - review   : scrape review/rating dari product URL

Flow:
    Beanstalkd → Worker.process_job() → save_and_publish() → PostgreSQL + JSON + Kafka

PENTING: Import dari `publishers.kafka_publisher` bukan `kafka.kafka_publisher`
         karena folder `kafka/` bentrok dengan package kafka-python di site-packages.
"""

import json
import logging
import os
import signal
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime

import greenstalk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cookie_manager.cookie_manager import CookieManager
from db.database import log_job_finish, log_job_start
from output.output_json import save_json_output
from publishers.kafka_publisher import get_publisher  # ← FIX: bukan kafka.kafka_publisher

logger = logging.getLogger(__name__)

BEANS_HOST = os.getenv("BEANS_HOST", "localhost")
BEANS_PORT = int(os.getenv("BEANS_PORT", 11300))

PLATFORMS_NEED_COOKIE = {"shopee", "lazada"}

MAX_RETRIES      = 3
RETRY_DELAY_BASE = 5  # seconds, exponential backoff


class BaseWorker(ABC):
    def __init__(self):
        self.running = True
        self.cm      = CookieManager()
        self.kafka   = get_publisher()
        self._setup_signal_handlers()

    # ── Abstract properties ───────────────────────────────────────────────────

    @property
    @abstractmethod
    def platform(self) -> str: ...

    @property
    @abstractmethod
    def tube_name(self) -> str: ...

    @abstractmethod
    def process_job(self, job_data: dict) -> bool: ...

    # ── Cookie helpers ────────────────────────────────────────────────────────

    def get_cookies(self, account: str = "default") -> list:
        """Return list of cookies untuk Playwright."""
        return self.cm.to_playwright_cookies(self.platform, account)

    def get_cookies_dict(self, account: str = "default") -> dict:
        """Return dict cookies untuk httpx/requests."""
        return self.cm.to_httpx_cookies(self.platform, account)

    # ── Save & Publish ────────────────────────────────────────────────────────

    def save_and_publish(
        self,
        items: list,
        save_fn,
        job_id: str,
        name: str,
        job_type: str,
        page_number: int  = 1,
        store_url: str    = None,
        store_name: str   = None,
        product_url: str  = None,
    ) -> int:
        """
        Pipeline: PostgreSQL → JSON file → Kafka.
        Return jumlah item yang tersimpan ke DB.

        Args:
            items        : list hasil scrape (dict per item)
            save_fn      : fungsi db/database.py untuk simpan ke PostgreSQL
            job_id       : UUID job
            name         : keyword, store name, atau product URL (untuk display)
            job_type     : "keyword" | "store" | "review"
            page_number  : halaman yang sedang di-scrape
            store_url    : URL toko (untuk job_type=store)
            store_name   : nama toko (untuk Kafka metadata)
            product_url  : URL produk (untuk job_type=review)
        """
        if not items:
            return 0

        # 1. Simpan ke PostgreSQL
        saved = save_fn(
            job_id=job_id,
            keyword=name if job_type == "keyword" else None,
            items=items,
            page_number=page_number,
            store_url=store_url,
            product_url=product_url,
        )

        # 2. Simpan ke JSON output
        save_json_output(
            platform=self.platform,
            job_type=job_type,
            name=name,
            items=items,
            page_number=page_number,
            job_id=job_id,
        )

        # 3. Publish ke Kafka (skip kalau tidak tersedia)
        if self.kafka.is_available():
            self.kafka.publish(
                platform=self.platform,
                job_type=job_type,
                items=items,
                keyword=name if job_type == "keyword" else None,
                store_url=store_url,
                store_name=store_name,
                product_url=product_url,
                job_id=job_id,
                page_number=page_number,
            )

        return saved

    # ── Cookie validation ─────────────────────────────────────────────────────

    def _check_cookie_requirement(self) -> bool:
        if self.platform not in PLATFORMS_NEED_COOKIE:
            return True
        if not self.cm.is_valid(self.platform):
            logger.error(
                f"❌ Cookie {self.platform} tidak tersedia!\n"
                f"   Jalankan: python cookie_manager/login_handler.py --platform {self.platform}"
            )
            return False
        ttl_min = self.cm.ttl_seconds(self.platform) // 60
        logger.info(f"🍪 Cookie {self.platform} valid (TTL: {ttl_min} menit)")
        if ttl_min < 30:
            logger.warning(f"⚠️  Cookie {self.platform} akan expired dalam {ttl_min} menit!")
        return True

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        logger.info(f"🟢 Worker {self.platform} dimulai. Tube: {self.tube_name}")
        if not self._check_cookie_requirement():
            return

        failed_tube = f"{self.tube_name}_failed"

        while self.running:
            # Reconnect loop
            try:
                client = greenstalk.Client((BEANS_HOST, BEANS_PORT), watch=self.tube_name)
            except Exception as e:
                logger.error(f"Gagal koneksi beanstalkd: {e}. Retry 10 detik...")
                time.sleep(10)
                continue

            logger.info(f"✅ Terhubung ke beanstalkd. Menunggu job dari '{self.tube_name}'...")

            while self.running:
                # Reserve job
                try:
                    job = client.reserve(timeout=5)
                except greenstalk.TimedOutError:
                    continue
                except Exception as e:
                    logger.error(f"Error reserve job: {e}")
                    break

                # Parse JSON
                try:
                    job_data = json.loads(job.body)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}. Delete job.")
                    client.delete(job)
                    continue

                job_id  = job_data.get("job_id", job.id)
                content = job_data.get("content", "?")
                jtype   = job_data.get("job_type", "keyword")
                logger.info(f"📥 Job [{job_id}] type={jtype} content='{content}'")

                # Re-check cookie sebelum proses
                if self.platform in PLATFORMS_NEED_COOKIE and not self.cm.is_valid(self.platform):
                    logger.warning(f"⚠️  Cookie {self.platform} expired! Worker berhenti.")
                    client.bury(job)
                    client.close()
                    return

                # Process dengan retry + exponential backoff
                success    = False
                last_error = None
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        success = self.process_job(job_data)
                        if success:
                            break
                        raise RuntimeError("process_job() returned False")
                    except Exception as e:
                        last_error = e
                        if attempt < MAX_RETRIES:
                            delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))
                            logger.warning(f"  Attempt {attempt}/{MAX_RETRIES} gagal: {e}. Retry {delay}s...")
                            time.sleep(delay)
                        else:
                            logger.error(f"  ❌ Semua {MAX_RETRIES} attempt gagal: {last_error}")

                # Delete atau dead-letter
                if success:
                    client.delete(job)
                    logger.info(f"  ✅ Job [{job_id}] selesai.")
                else:
                    try:
                        fc = greenstalk.Client((BEANS_HOST, BEANS_PORT), use=failed_tube)
                        dead = {
                            **job_data,
                            "failed_at": datetime.utcnow().isoformat(),
                            "error": str(last_error),
                        }
                        fc.put(json.dumps(dead))
                        fc.close()
                        logger.warning(f"  📥 Job [{job_id}] → dead-letter: {failed_tube}")
                    except Exception as e:
                        logger.error(f"Gagal push ke failed tube: {e}")
                    client.delete(job)

            try:
                client.close()
            except Exception:
                pass

        logger.info(f"🔴 Worker {self.platform} dihentikan.")

    # ── Signal handlers ───────────────────────────────────────────────────────

    def _setup_signal_handlers(self):
        def handle_shutdown(signum, frame):
            logger.info(f"Shutdown signal. Menghentikan worker {self.platform}...")
            self.running = False
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
