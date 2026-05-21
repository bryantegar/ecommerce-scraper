"""
Service Shopee — Scraping Logic
================================
Perbaikan dari versi asli:
1. Fix import: urllib.parse.quote sekarang benar
2. Fix variable bentrok: parameter `page` (int) vs Playwright page object
   → parameter scraping page sekarang disebut `page_num`
3. Cleanup komentar kode lama yang tidak terpakai
"""

import random
from urllib.parse import quote, urlparse

from camoufox.sync_api import Camoufox

from libs.logger import printinfo


class ServiceShopee:
    def __init__(self):
        ...

    def scrape_shopee_keyword(
        self,
        keyword: str,
        cookies: list,           # list of dict format Playwright (dari CookieManager)
        page_num: int = 1,       # FIX: dulu namanya 'page', bentrok dengan Playwright page object
        proxy=None,
    ) -> dict:
        """
        Scrape hasil search Shopee untuk satu keyword di satu halaman.

        Return:
            {
                "items": [...],      # list produk dari API Shopee
                "is_captcha": bool,
                "status": int        # 200 / 403 / None
            }
        """
        # FIX: dulu `urllib.parse.quote` tapi `urllib` tidak diimport
        encoded_keyword = quote(keyword)

        with Camoufox(
            os=["windows", "macos", "linux"],
            headless=True,
        ) as browser:
            context = browser.new_context()
            context.add_cookies(cookies)

            # FIX: variable Playwright page object sekarang bernama `pw_page`
            # bukan `page` (supaya tidak bentrok dengan parameter `page_num`)
            pw_page = context.new_page()

            state = {"items": None, "is_captcha": False, "status": None}

            def handle_response(response):
                try:
                    if response.request.resource_type in ["fetch", "xhr"]:
                        url = response.url
                        target_api    = "api/v4/search/search_items"
                        login_pattern = "api/v2/authentication/get_active_login_page"
                        captcha_pattern = "api/v4/anti_fraud/captcha"

                        if login_pattern in url or captcha_pattern in url:
                            print("==================")
                            print("Captcha / Login detected")
                            print("==================")
                            state["is_captcha"] = True
                            state["status"] = 403
                        elif target_api in url:
                            data = response.json()
                            items = data.get("items", [])
                            if items:
                                state["items"] = items
                                state["status"] = 200
                except Exception as e:
                    print(f"[Shopee] handle_response error: {e}")

            pw_page.on("response", handle_response)

            print(f"[Shopee] Scraping keyword='{keyword}' page={page_num}")
            try:
                url = f"https://shopee.co.id/search?keyword={encoded_keyword}&page={page_num}"
                pw_page.goto(url, wait_until="domcontentloaded")
                pw_page.mouse.wheel(0, 1000)
                pw_page.wait_for_timeout(2000)
                pw_page.evaluate("window.scrollTo(0, document.body.scrollHeight / 1.5)")
                pw_page.wait_for_timeout(6000)
            except Exception as e:
                print(f"[Shopee] Cannot access page: {e}")

        return state

    def scrape_shopee_store(self, store_url: str, page_num: int, cookies: list) -> dict:
        """Scrape produk dari toko Shopee."""
        url_parse = urlparse(store_url)
        store_name = url_parse.path.split("/")[-1]
        print(f"[Shopee Store] store_name={store_name}")

        with Camoufox(
            os=["windows", "macos", "linux"],
            headless=True,
            humanize=2.0,
        ) as browser:
            context = browser.new_context()
            context.add_cookies(cookies)
            pw_page = context.new_page()

            state = {"items": None, "is_captcha": False, "status": None}

            def handle_response(response):
                try:
                    if response.request.resource_type in ["fetch", "xhr"]:
                        url = response.url
                        target_api      = "api/v4/shop/rcmd_items"
                        login_pattern   = "api/v2/authentication/get_active_login_page"
                        captcha_pattern = "api/v4/anti_fraud/captcha"

                        if login_pattern in url or captcha_pattern in url:
                            state["is_captcha"] = True
                            state["status"] = 403
                        elif target_api in url:
                            data = response.json()
                            raw = data.get("data", {})
                            items = raw.get("centralize_item_card", {}).get("item_cards", [])
                            if items:
                                state["items"] = items
                                state["status"] = 200
                except Exception as e:
                    print(f"[Shopee Store] Error: {e}")

            pw_page.on("response", handle_response)

            actual_page = page_num - 1  # Shopee 0-indexed
            print(f"[Shopee Store] Opening page {actual_page}")
            try:
                url = f"https://shopee.co.id/{store_name}?page={actual_page}&sortBy=pop&tab=0"
                pw_page.goto(url, wait_until="domcontentloaded")
                pw_page.mouse.wheel(0, 1000)
                pw_page.wait_for_timeout(2000)
                pw_page.evaluate("window.scrollTo(0, document.body.scrollHeight / 1.5)")
                pw_page.wait_for_timeout(10000)
            except Exception as e:
                print(f"[Shopee Store] Cannot access page: {e}")

        return state
