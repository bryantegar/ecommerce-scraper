"""
Test Lazada scraping pakai Camoufox + cookie injection
Intercept response dari API Lazada seperti cara Shopee
"""
import json
from cookie_manager.cookie_manager import CookieManager
from camoufox.sync_api import Camoufox
from urllib.parse import quote

keyword = "Dancow"
page_num = 1

cm = CookieManager()
cookies = cm.to_playwright_cookies('lazada')
print(f"Cookies loaded: {len(cookies)} cookies")

encoded_keyword = quote(keyword)

with Camoufox(
    os=["windows", "macos", "linux"],
    headless=False,  # headful dulu biar kita bisa lihat
) as browser:
    context = browser.new_context()
    context.add_cookies(cookies)
    page = context.new_page()

    state = {"items": None, "status": None, "raw": None}

    def handle_response(response):
        try:
            if response.request.resource_type in ["fetch", "xhr", "document"]:
                url = response.url
                # Target API Lazada keyword search
                if "catalog" in url and "ajax=true" in url:
                    print(f"\n✅ Found API URL: {url}")
                    try:
                        data = response.json()
                        state["raw"] = data
                        state["status"] = response.status
                        # Cari dimana items berada
                        mods = data.get("mods", {})
                        list_items = mods.get("listItems", [])
                        print(f"Items found: {len(list_items)}")
                        if list_items:
                            state["items"] = list_items
                            print(f"Sample item keys: {list(list_items[0].keys())}")
                    except Exception as e:
                        print(f"Not JSON: {e}")
                        print(f"Response text preview: {response.text()[:200]}")
        except Exception as e:
            print(f"Handler error: {e}")

    page.on("response", handle_response)

    url = f"https://www.lazada.co.id/catalog/?ajax=true&isFirstRequest=true&page={page_num}&q={encoded_keyword}"
    print(f"Opening: {url}")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    print(f"\n--- RESULT ---")
    print(f"Status: {state['status']}")
    print(f"Items: {len(state['items']) if state['items'] else 0}")

    if state["raw"]:
        with open("lazada_response_debug.json", "w", encoding="utf-8") as f:
            json.dump(state["raw"], f, ensure_ascii=False, indent=2)
        print("Raw response saved to lazada_response_debug.json")
