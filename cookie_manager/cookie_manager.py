"""
Cookie Manager Terpusat
=======================
Menyimpan, memvalidasi, dan mendistribusikan cookie ke semua worker via Redis.

Alur:
1. `camoufox_login.py` (dijalankan manual/terjadwal) → simpan cookie ke Redis
2. Worker butuh cookie → panggil CookieManager.get_cookies(platform)
3. Kalau cookie expired / tidak ada → trigger alert / auto-refresh

Usage:
    cm = CookieManager()
    cookies = cm.get_cookies("shopee")
    cm.save_cookies("shopee", cookies_list, ttl_hours=12)
    is_valid = cm.is_valid("shopee")
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis

logger = logging.getLogger(__name__)

# TTL default per platform (jam) — disesuaikan dengan masa aktif session masing-masing
PLATFORM_TTL = {
    "shopee": 12,    # Shopee session biasanya ~12 jam
    "lazada": 24,    # Lazada lebih panjang
    "tokopedia": 0,  # Tokopedia tidak butuh login untuk scraping dasar
    "blibli": 0,
    "olx": 0,
}

REDIS_COOKIE_PREFIX = "cookie:"
REDIS_META_PREFIX = "cookie_meta:"


class CookieManager:
    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = 6379,
        redis_db: int = 1,
    ):
        host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis = redis.Redis(
            host=host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
        )

    # ──────────────────────────────────────────────
    # WRITE
    # ──────────────────────────────────────────────

    def save_cookies(
        self,
        platform: str,
        cookies: list,
        ttl_hours: int = None,
        account: str = "default",
    ) -> bool:
        """
        Simpan cookies ke Redis dengan TTL.
        cookies: list of dict (format Playwright/Camoufox context.cookies())
        """
        ttl_hours = ttl_hours or PLATFORM_TTL.get(platform, 12)
        key = self._cookie_key(platform, account)
        meta_key = self._meta_key(platform, account)

        expires_at = (
            datetime.now(tz=timezone.utc) + timedelta(hours=ttl_hours)
        ).isoformat()

        meta = {
            "platform": platform,
            "account": account,
            "saved_at": datetime.now(tz=timezone.utc).isoformat(),
            "expires_at": expires_at,
            "cookie_count": len(cookies),
        }

        ttl_seconds = ttl_hours * 3600

        pipe = self.redis.pipeline()
        pipe.setex(key, ttl_seconds, json.dumps(cookies))
        pipe.setex(meta_key, ttl_seconds, json.dumps(meta))
        pipe.execute()

        logger.info(
            f"[CookieManager] Saved {len(cookies)} cookies for {platform}/{account}, "
            f"expires in {ttl_hours}h"
        )
        return True

    # ──────────────────────────────────────────────
    # READ
    # ──────────────────────────────────────────────

    def get_cookies(
        self, platform: str, account: str = "default"
    ) -> Optional[list]:
        """
        Ambil cookies dari Redis. Return None kalau tidak ada / expired.
        """
        key = self._cookie_key(platform, account)
        raw = self.redis.get(key)
        if raw is None:
            logger.warning(
                f"[CookieManager] No cookies found for {platform}/{account}"
            )
            return None
        return json.loads(raw)

    def get_meta(self, platform: str, account: str = "default") -> Optional[dict]:
        meta_key = self._meta_key(platform, account)
        raw = self.redis.get(meta_key)
        if raw is None:
            return None
        return json.loads(raw)

    def is_valid(self, platform: str, account: str = "default") -> bool:
        """Cek apakah cookie masih ada di Redis (belum expired)."""
        key = self._cookie_key(platform, account)
        return self.redis.exists(key) > 0

    def ttl_seconds(self, platform: str, account: str = "default") -> int:
        """Sisa TTL dalam detik. -1 = tidak ada TTL. -2 = key tidak ada."""
        key = self._cookie_key(platform, account)
        return self.redis.ttl(key)

    def list_platforms(self) -> list:
        """List semua platform yang punya cookie aktif."""
        keys = self.redis.keys(f"{REDIS_COOKIE_PREFIX}*")
        platforms = []
        for k in keys:
            parts = k.replace(REDIS_COOKIE_PREFIX, "").split(":")
            platforms.append({"platform": parts[0], "account": parts[1] if len(parts) > 1 else "default"})
        return platforms

    # ──────────────────────────────────────────────
    # DELETE / INVALIDATE
    # ──────────────────────────────────────────────

    def invalidate(self, platform: str, account: str = "default"):
        """Hapus cookie secara manual (misal setelah detect session expired)."""
        self.redis.delete(self._cookie_key(platform, account))
        self.redis.delete(self._meta_key(platform, account))
        logger.info(f"[CookieManager] Invalidated cookies for {platform}/{account}")

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    def to_httpx_cookies(self, platform: str, account: str = "default") -> dict:
        """
        Convert cookies ke format dict {name: value} untuk dipakai
        di httpx/requests sebagai cookies=...
        """
        cookies = self.get_cookies(platform, account)
        if not cookies:
            return {}
        return {c["name"]: c["value"] for c in cookies}

    def to_playwright_cookies(self, platform: str, account: str = "default") -> list:
        """Return dalam format asli Playwright (list of dict)."""
        return self.get_cookies(platform, account) or []

    def _cookie_key(self, platform: str, account: str) -> str:
        return f"{REDIS_COOKIE_PREFIX}{platform}:{account}"

    def _meta_key(self, platform: str, account: str) -> str:
        return f"{REDIS_META_PREFIX}{platform}:{account}"
