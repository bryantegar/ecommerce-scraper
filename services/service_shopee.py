import hashlib
import json
from time import time
from urllib import parse

from requests import Response
from requests.utils import cookiejar_from_dict


from libs.logger import printinfo
from curl_cffi import requests


class ServiceShopee:
    def __init__(self):
        ...
        
    def scrape_shopee_store(self, store_url, page_num, cookies, proxies=None):
        product_url_list = []
        url_parse = urlparse(store_url)
        store_name = url_parse.path.split('/')[-1]
        print(store_name)
        # encoded_keyword = urllib.parse.quote(keyword)
        with Camoufox(
            os=["windows", "macos", "linux"],
            # persistent_context=True,
            # user_data_dir='./shopee_session',
            headless=True,
            humanize = 2.0
        ) as browser:
            # with open('shopee_cookies.json', 'r') as f:
            #     cookies_data = json.load(f)
            # cookies_data = get_cookies('shopee')
            context = browser.new_context()
            context.add_cookies(cookies_redis)
            page = context.new_page()
            
            state = {"items": None, 'is_capctha': False, 'status': None}
            product_link = []
            def handle_response(response):
                try:
                    if response.request.resource_type in ['fetch', 'xhr']:
                        url = response.url
                        # print(url)
                        target_api = "api/v4/shop/rcmd_items"
                        login_pattern = 'api/v2/authentication/get_active_login_page'
                        captcha_patern = 'api/v4/anti_fraud/captcha'
                        if login_pattern in url or captcha_patern in url:
                            print('==================')
                            print('Captcha detected')
                            print('==================')
                            state['is_captcha'] = True
                            state['status'] = 403
                        elif target_api in url:
                            print(url)
                            data = response.json()
                            # print(data)
                            raw = data.get("data", {})
                            centralize_item_card = raw.get('centralize_item_card',{})
                            items = centralize_item_card.get('item_cards',[])
                            # print(items)
                            if items:
                                state['items'] = items
                                state['status'] = 200     
                    else:
                        pass

                except Exception as e:
                    print(f"[Service Shopee] Error {e}")

            page.on('response', handle_response)
            
            page_num = page_num - 1

            print(f"[Shopee] Open Page {page_num}")
            try:
                print(f"[Shopee] Scraping page {page_num}")
                url = f"https://shopee.co.id/{store_name}?page={page_num}&sortBy=pop&tab=0"
                # url = f"https://shopee.co.id/search?keyword={encoded_keyword}&page={p}"
                page.goto(url, wait_until="domcontentloaded")
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 1.5)")
                # if page.locator('#NEW_CAPTCHA').is_visible():
                #     state['is_capctha'] = True
                page.wait_for_timeout(10000)
                # cookies_data = page.context.cookies()
                # with open("shopee_cookies.json", "w", encoding="utf-8") as f:
                #     json.dump(cookies_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Cannot access pages")
                pass
        return state

    def scrape_shopee_keyword(self, keyword, cookies, page_num, proxies=None):
        encoded_keyword = urllib.parse.quote(keyword)
        with Camoufox(
            os=["windows", "macos", "linux"],
            # persistent_context=True,
            # user_data_dir='./shopee_session',
            headless=True
        ) as browser:
            # with open('shopee_cookies.json', 'r') as f:
            #     cookies_data = json.load(f)
            # cookies_data = fresh_cookies_from_redis('shopee')
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()
            
            state = {"items": None, 'is_captcha': False, 'status':None}            
            def handle_response(response):
                try:
                    if response.request.resource_type in ['fetch', 'xhr']:
                        url = response.url
                        target_api = "api/v4/search/search_items"
                        login_pattern = 'api/v2/authentication/get_active_login_page'
                        captcha_patern = 'api/v4/anti_fraud/captcha'
                        if login_pattern in url or captcha_patern in url:
                            print('==================')
                            print('Captcha detected')
                            print('==================')
                            state['is_captcha'] = True
                            state['status'] = 403
                        elif target_api in url:
                            data = response.json()
                            print(data)
                            items = data.get("items", [])
                            if items:
                                state['items'] = items
                                state['status'] = 200
                            
                    else:
                        pass

                except Exception as e:
                    print(f"[Shopee] Error {e}")

            page.on('response', handle_response)
            print(f"[Shopee] Open Page {page_num}")
            try:
                    print(f"[Shopee] Scraping page {p}")
                    url = f"https://shopee.co.id/search?keyword={encoded_keyword}&page={page_num}"
                    page.goto(url)
                    page.mouse.wheel(0, 1000)
                    page.wait_for_timeout(2000)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 1.5)")
                    # if page.locator('#NEW_CAPTCHA').is_visible():
                    #     state['is_capctha'] = True
                    page.wait_for_timeout(6000)
                    # cookies_data = page.context.cookies()
                    # with open("shopee_cookies.json", "w", encoding="utf-8") as f:
                    #     json.dump(cookies_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                    print(f"Cannot access pages")
                    pass
            return state['items']

    def scrape_shopee_comments(self, product_url, p, cookies, proxies=None):
        with Camoufox(
            os=["windows","linux"],
            headless=True,
            humanize = 2.0
        ) as browser:
            # with open('shopee_cookies.json', 'r') as f:
            #     cookies_data = json.load(f)
            # cookies_data = get_cookies('shopee')
            context = browser.new_context()
            page = context.new_page()
            context.add_cookies(cookies)
            state = {'current_page': p, 'has_review': True, 'items': None, 'is_captcha': False, 'product_id':None}
            offset = (p * 6) - 6
            def handle_response(response):
                    if response.request.resource_type in ['fetch', 'xhr']:
                        url = response.url
                        # print(url)
                        target_api = f"api/v2/item/get_ratings?filter=0&flag=1&limit=6&offset={offset}"
                        login_pattern = 'api/v2/authentication/get_active_login_page'
                        captcha_patern = 'api/v4/anti_fraud/captcha'
                        if login_pattern in url or captcha_patern in url:
                            print('==================')
                            print('Captcha detected')
                            print('==================')
                            state['is_captcha'] = True
                            state['status'] = 403
                        elif target_api in url:
                            print(url)
                            data = response.json()
                            review_data = data.get('data', {})
                            # print(data)
                            product_id = data['data']['ratings'][0]['itemid']
                            state['product_id'] = product_id
                            if not review_data:
                                print("Review Not Found")
                                state['has_review'] = False
                            print(product_id)
                            state['items'] = data
                            state['status'] = 200
                            

            page.on('response', handle_response)
                    
            time_out = random.randint(3000, 6000)
            print("Navigating...")
            page.goto(product_url, wait_until="domcontentloaded")
            # with open("shopee_cookies.json", "w", encoding="utf-8") as f:
            #     json.dump(cookies_data, f, indent=2, ensure_ascii=False)            
            
            for _ in range(2):
                print(f"Pressing arrow down")
                page.keyboard.press("PageDown")
                print(f"Waiting For {time_out}")
                page.wait_for_timeout(time_out)
            
            if not state['has_review']:
                return state
            
            # for _ in range(2):
                # print(f"Pressing arrow down")
                # page.keyboard.press("PageDown")
            #     print(f"Waiting For {time_out}")
            #     page.wait_for_timeout(time_out)
                
            target_page = p
            if target_page == 1:
                for _ in range(2):
                    print(f"Pressing arrow down")
                    page.keyboard.press("PageDown")
                    # print(f"Waiting For {time_out}")
                    # page.wait_for_timeout(time_out)
                    return state
            elif target_page > 5:
                page.locator(f"button.shopee-button-no-outline:has-text('{5}')").dispatch_event("click")
                next_button = page.locator("button.shopee-icon-button--right")
                for current_click in range(5, target_page):
                    print(f"Clicking from {current_click} to {target_page}")
                    next_button.dispatch_event("click")
                    page.wait_for_timeout(time_out)
            else:
                page.locator(f"button.shopee-button-no-outline:has-text('{p}')").dispatch_event("click")
                page.wait_for_timeout(time_out)
            
            return state
    
    def extract_store_name(self, store_url):
        path = urlparse(store_url).path.strip('/')
        store_name = path.split('/')[-1]
        return store_name
    