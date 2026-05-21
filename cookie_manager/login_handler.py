"""
Login Handler — Multi-Platform Cookie Harvester
================================================
Buka browser Camoufox untuk login manual, lalu simpan cookie ke Redis
via CookieManager.

Cara pakai:
    # Login Shopee (headful, manual)
    python cookie_manager/login_handler.py --platform shopee

    # Login Lazada
    python cookie_manager/login_handler.py --platform lazada

    # Login semua platform sekaligus (satu per satu)
    python cookie_manager/login_handler.py --platform all
"""

import argparse
import json
import logging
import os
import sys

# Tambahkan root project ke path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cookie_manager import CookieManager
from camoufox.sync_api import Camoufox

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

PLATFORM_URLS = {
    "shopee": "https://shopee.co.id/buyer/login",
    "lazada": "https://member.lazada.co.id/user/login",
    "tokopedia": None,   # tidak butuh login
    "blibli": None,
    "olx": None,
}

PLATFORM_TTL = {
    "shopee": 12,
    "lazada": 24,
}


def login_platform(platform: str, account: str = "default"):
    login_url = PLATFORM_URLS.get(platform)
    if login_url is None:
        logger.info(f"Platform {platform} tidak membutuhkan login. Skip.")
        return

    logger.info(f"Membuka browser untuk login {platform.upper()}...")
    logger.info("Silakan login secara manual di browser yang terbuka.")
    logger.info("Tutup browser setelah selesai login — cookie akan otomatis disimpan.")

    with Camoufox(
        os=["windows", "macos", "linux"],
        headless=False,
    ) as browser:
        page = browser.new_page()
        page.goto(login_url)

        # Tunggu user tutup browser / tab
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass

        # Ambil cookies setelah login
        cookies_list = page.context.cookies()

    if not cookies_list:
        logger.error(f"Tidak ada cookie yang berhasil diambil untuk {platform}!")
        return

    # Simpan ke Redis via CookieManager
    cm = CookieManager()
    ttl = PLATFORM_TTL.get(platform, 12)
    cm.save_cookies(platform, cookies_list, ttl_hours=ttl, account=account)

    # Simpan juga sebagai backup file JSON (untuk debugging)
    backup_path = f"shopee_session/{platform}_cookies_{account}.json"
    os.makedirs("shopee_session", exist_ok=True)
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(cookies_list, f, indent=2, ensure_ascii=False)

    logger.info(
        f"✅ Cookie {platform}/{account} berhasil disimpan! "
        f"({len(cookies_list)} cookies, TTL {ttl} jam)"
    )
    logger.info(f"   Backup tersimpan di: {backup_path}")


def check_cookie_status():
    """Print status semua cookie yang ada di Redis."""
    cm = CookieManager()
    platforms = cm.list_platforms()

    if not platforms:
        print("Tidak ada cookie aktif di Redis.")
        return

    print(f"\n{'Platform':<15} {'Account':<15} {'TTL (menit)':<15} {'Status'}")
    print("-" * 60)
    for p in platforms:
        ttl = cm.ttl_seconds(p["platform"], p["account"])
        meta = cm.get_meta(p["platform"], p["account"])
        ttl_min = ttl // 60 if ttl > 0 else "N/A"
        status = "✅ Valid" if ttl > 0 else "❌ Expired"
        expires = meta.get("expires_at", "?") if meta else "?"
        print(f"{p['platform']:<15} {p['account']:<15} {str(ttl_min):<15} {status} (expires: {expires})")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Login handler untuk mengumpulkan cookie ecommerce"
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="shopee",
        choices=["shopee", "lazada", "all", "status"],
        help="Platform yang akan di-login. Gunakan 'status' untuk cek semua cookie.",
    )
    parser.add_argument(
        "--account",
        type=str,
        default="default",
        help="Nama akun (untuk multi-akun per platform)",
    )
    args = parser.parse_args()

    if args.platform == "status":
        check_cookie_status()
    elif args.platform == "all":
        for platform in ["shopee", "lazada"]:
            print(f"\n{'='*50}")
            login_platform(platform, args.account)
    else:
        login_platform(args.platform, args.account)
