"""
Scheduler — Orkestrasi Job Push ke Beanstalkd
=============================================
Pengganti scheduler.py lama yang pakai while True + time.sleep.

Fitur baru:
- Pakai APScheduler (cron-based, tidak drift seperti sleep)
- Cek queue beanstalkd sebelum push (hindari duplikasi)
- Cek cookie validity sebelum push job ke platform yang butuh login
- Alert log kalau cookie hampir expired (< 1 jam)
- Graceful shutdown

Cara jalankan:
    python scheduler.py

Atau via docker-compose (sudah dikonfigurasi di docker-compose.yml)
"""

import json
import logging
import os
import signal
import sys
import uuid
from datetime import datetime

import greenstalk
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Tambahkan root ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cookie_manager.cookie_manager import CookieManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("scheduler")

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────

BEANS_HOST = os.getenv("BEANS_HOST", "localhost")
BEANS_PORT = int(os.getenv("BEANS_PORT", 11300))

# Platform yang butuh cookie valid sebelum job di-push
PLATFORMS_NEED_COOKIE = {"shopee", "lazada"}

# Tube name → platform name
PLATFORMS = {
    "ecommerce_crawler_tokopedia_keyword": "tokopedia",
    "ecommerce_crawler_shopee_keyword": "shopee",
    "ecommerce_crawler_lazada_keyword": "lazada",
    "ecommerce_crawler_blibli_keyword": "blibli",
    "ecommerce_crawler_olx_keyword": "olx",   # ← FIX: OLX ditambahkan
}

KEYWORDS = [
    "Friesland Campina",
    "SGM",
    "Vidoran",
    "Dancow",
    "Shanghiang Perkasa",
    "Bebelac",
    "Lactogrow",
    "Healthy Way",
    "Abbot",
    "Mead Johnson",
    "Weyth Nutrition",
    "Nutrilon",
]

# Batas max job pending di queue sebelum tidak push lagi
MAX_QUEUE_JOBS = 500

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_queue_stats(tube: str) -> dict:
    """Ambil statistik tube dari beanstalkd."""
    try:
        client = greenstalk.Client((BEANS_HOST, BEANS_PORT))
        stats = client.stats_tube(tube)
        client.close()
        return stats
    except greenstalk.NotFoundError:
        # Tube belum ada (belum pernah ada job)
        return {"current-jobs-ready": 0, "current-jobs-reserved": 0}
    except Exception as e:
        logger.error(f"Gagal ambil stats tube {tube}: {e}")
        return {"current-jobs-ready": 0}


def push_jobs_to_tube(tube: str, platform: str, keywords: list):
    """Push list keyword sebagai jobs ke tube beanstalkd."""
    try:
        client = greenstalk.Client((BEANS_HOST, BEANS_PORT), use=tube)
        pushed = 0
        for keyword in keywords:
            payload = {
                "job_id": str(uuid.uuid4()),
                "platform": platform,
                "content": keyword,
                "count": 0,
                "max_count": 1,
                "pushed_at": datetime.utcnow().isoformat(),
            }
            client.put(json.dumps(payload))
            pushed += 1
        client.close()
        logger.info(f"  ✅ {tube}: {pushed} jobs pushed")
        return pushed
    except Exception as e:
        logger.error(f"  ❌ Gagal push ke {tube}: {e}")
        return 0


def check_cookie_warnings(cm: CookieManager):
    """Log warning kalau ada cookie yang hampir expired."""
    for platform in PLATFORMS_NEED_COOKIE:
        ttl = cm.ttl_seconds(platform)
        if ttl < 0:
            logger.warning(
                f"⚠️  Cookie {platform} TIDAK ADA atau sudah expired! "
                f"Jalankan: python cookie_manager/login_handler.py --platform {platform}"
            )
        elif ttl < 3600:
            logger.warning(
                f"⚠️  Cookie {platform} akan expired dalam {ttl//60} menit! "
                f"Segera refresh cookie."
            )


# ─────────────────────────────────────────────
# MAIN JOB FUNCTION
# ─────────────────────────────────────────────

def run_push_jobs():
    logger.info(f"{'='*60}")
    logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Memulai push jobs...")

    cm = CookieManager()

    # Cek cookie warnings dulu
    check_cookie_warnings(cm)

    total_pushed = 0
    skipped_platforms = []

    for tube, platform in PLATFORMS.items():
        logger.info(f"\n📦 Memproses tube: {tube} (platform: {platform})")

        # Cek apakah platform butuh cookie
        if platform in PLATFORMS_NEED_COOKIE:
            if not cm.is_valid(platform):
                logger.warning(
                    f"  ⏭️  Skip {platform}: cookie tidak valid. "
                    f"Login dulu via: python cookie_manager/login_handler.py --platform {platform}"
                )
                skipped_platforms.append(platform)
                continue
            else:
                ttl_min = cm.ttl_seconds(platform) // 60
                logger.info(f"  🍪 Cookie {platform} valid (TTL: {ttl_min} menit)")

        # Cek apakah queue sudah terlalu penuh
        stats = get_queue_stats(tube)
        current_ready = stats.get("current-jobs-ready", 0)
        current_reserved = stats.get("current-jobs-reserved", 0)

        logger.info(f"  📊 Queue stats: {current_ready} ready, {current_reserved} processing")

        if current_ready >= MAX_QUEUE_JOBS:
            logger.warning(
                f"  ⏭️  Skip {tube}: queue sudah penuh ({current_ready} jobs pending)"
            )
            continue

        # Push jobs
        pushed = push_jobs_to_tube(tube, platform, KEYWORDS)
        total_pushed += pushed

    logger.info(f"\n✅ Selesai! Total {total_pushed} jobs pushed.")
    if skipped_platforms:
        logger.warning(f"⚠️  Platform di-skip karena tidak ada cookie: {skipped_platforms}")
    logger.info(f"{'='*60}\n")


# ─────────────────────────────────────────────
# SCHEDULER SETUP
# ─────────────────────────────────────────────

def main():
    scheduler = BlockingScheduler(timezone="Asia/Jakarta")

    # Jadwal default: setiap jam
    # Bisa diubah sesuai kebutuhan, contoh:
    # - Setiap 30 menit: interval_minutes=30 (pakai IntervalTrigger)
    # - Setiap jam 6 pagi dan 6 sore: cron hour='6,18'
    cron_hour = os.getenv("SCHEDULER_CRON_HOUR", "*")    # Default: setiap jam
    cron_minute = os.getenv("SCHEDULER_CRON_MINUTE", "0")

    scheduler.add_job(
        run_push_jobs,
        trigger=CronTrigger(hour=cron_hour, minute=cron_minute),
        id="push_jobs",
        name="Push Ecommerce Scraper Jobs",
        misfire_grace_time=300,  # 5 menit tolerance kalau telat jalan
    )

    # Juga jalankan sekali saat startup
    scheduler.add_job(
        run_push_jobs,
        id="push_jobs_startup",
        name="Push Jobs (startup)",
    )

    # Graceful shutdown
    def shutdown(signum, frame):
        logger.info("Menerima sinyal shutdown, menghentikan scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    logger.info(
        f"⏰ Scheduler dimulai. "
        f"Cron: jam={cron_hour} menit={cron_minute} (WIB)"
    )
    scheduler.start()


if __name__ == "__main__":
    main()
