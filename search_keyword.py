import sys
import requests
import json
import time
import urllib.parse
import curl_cffi
from curl_cffi import requests
from camoufox.sync_api import Camoufox


def get_cookies_data(cookies_file):
    with open(cookies_file, 'r') as f:
        data = json.load(f)

    cookies_dict = {c['name']: c['value'] for c in data}

    cookies_string = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])

    # token = cookies_dict.get('_m_h5_tk', '').split('_')[0]
    return cookies_string


def scrape_olx(keyword, max_pages=3):
    proxy_url = "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    proxies = {"http": proxy_url, "https": proxy_url}
    encoded_keyword = urllib.parse.quote(keyword)
    max_pages = 2
    clean_keyword_url = keyword.lower().replace(" ", "-")

    for page in range(1, max_pages + 1):
        print(
            f"[OLX] Scraping keyword ({encoded_keyword}) from OLX, Page {page}")
        api_url = f"https://www.olx.co.id/api/relevance/v4/search?facet_limit=100&location=4000030&location_facet_limit=40&page={page}&platform=web-desktop&query={keyword}&relaxedFilters=true"
        url = f"https://www.olx.co.id/items/q-{clean_keyword_url}"

        try:
            r = requests.get(api_url, impersonate="chrome110", proxies=proxies)

            if r.status_code == 200:
                print(f"[OLX] Success directing to: {api_url}")
                data = r.json()
                items = data.get("data", [])
                if not items:
                    print("Data Not Found")
                    break

                output = {
                    "raw": items,
                    "metadata": {
                        "keyword": keyword,
                        "platform": "olx",
                        "url": url
                    }
                }

                filename = f"olx_{keyword.replace(' ', '_')}_page_{page}.json"
                with open(filename, 'w') as f:
                    json.dump(output, f, indent=4)
                print(f"[OLX] File Saved: {filename}")

                time.sleep(5)
            else:
                print(f"Status Code {r.status_code}")
                break
        except Exception as e:
            print("Error ", e)
            break
    # print(f"[Olx] Success taking keywoard ({keyword}) from Olx")


def scrape_tokped(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    proxies = {
        "http": "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570",
        "https": "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    }
    max_pages = 2

    for page in range(1, max_pages + 1):
        print(
            f"[Tokopedia] Scraping keyword ({encoded_keyword}) from Tokopedia, Page {page}")
        api_url = "https://gql.tokopedia.com/graphql/SearchProductV5Query"
        url = f"https://www.tokopedia.com/search?st=&q={keyword}"

        payload = [{
            "operationName": "SearchProductV5Query",
            "variables": {
                # "params": f"device=desktop&enter_method=normal_search&l_name=sre&navsource=&ob=23&page={page}&q={keyword}&rows=60&source=search"
                "params": f"device=desktop&enter_method=normal_search&l_name=sre&ob=23&page={page}&q={keyword}&related=true&rows=60&safe_search=false&sc=&scheme=https&shipping=&show_adult=false&source=search&st=product&start=0&topads_bucket=true&unique_id=7e500e7f1e364ce215992821ccbbd74a&user_addressId=&user_cityId=176&user_districtId=2274&user_id=&user_lat=&user_long=&user_postCode=&user_warehouseId=&variants=&warehouses="
            },
            "query": "query SearchProductV5Query($params: String!) { searchProductV5(params: $params) { header { totalData responseCode keywordProcess keywordIntention componentID isQuerySafe additionalParams backendFilters meta { dynamicFields __typename } __typename } data { totalDataText banner { position text applink url imageURL componentID trackingOption __typename } redirection { url __typename } related { relatedKeyword position trackingOption otherRelated { keyword url applink componentID products { oldID: id id: id_str_auto_ name url applink mediaURL { image __typename } shop { oldID: id id: id_str_auto_ name city tier __typename } badge { oldID: id id: id_str_auto_ title url __typename } price { text number __typename } freeShipping { url __typename } labelGroups { position title type url styles { key value __typename } __typename } rating wishlist ads { id productClickURL productViewURL productWishlistURL tag __typename } meta { oldWarehouseID: warehouseID warehouseID: warehouseID_str_auto_ componentID __typename } __typename } __typename } __typename } suggestion { currentKeyword suggestion query text componentID trackingOption __typename } ticker { oldID: id id: id_str_auto_ text query applink componentID trackingOption __typename } violation { headerText descriptionText imageURL ctaURL ctaApplink buttonText buttonType __typename } products { oldID: id id: id_str_auto_ ttsProductID name url applink mediaURL { image image300 videoCustom __typename } shop { oldID: id id: id_str_auto_ ttsSellerID name url city tier __typename } stock { ttsSKUID __typename } badge { oldID: id id: id_str_auto_ title url __typename } price { text number range original discountPercentage __typename } freeShipping { url __typename } labelGroups { position title type url styles { key value __typename } __typename } labelGroupsVariant { title type typeVariant hexColor __typename } category { oldID: id id: id_str_auto_ name breadcrumb gaKey __typename } rating wishlist ads { id productClickURL productViewURL productWishlistURL tag __typename } meta { oldParentID: parentID parentID: parentID_str_auto_ oldWarehouseID: warehouseID warehouseID: warehouseID_str_auto_ isImageBlurred isPortrait __typename } __typename } __typename } __typename } }"
        }]

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "x-device": "desktop"
        }

        try:
            # print(api_url)
            r = curl_cffi.post(
                api_url, json=payload, impersonate="chrome110", headers=headers, proxies=proxies)
            # # response = requests.get(api_url)
            # print(r.text)
            # print(r.content)

            if r.status_code == 200:
                print(f"[Tokopedia] Success directing to: {api_url}")
                data = r.json()
                root_data = data[0].get('data', {})
                search_v5 = root_data.get('searchProductV5', {})
                items = search_v5.get('data', {})

                if not items:
                    print("Data not found")
                    break

                output = {
                    "raw": items,
                    "metadata": {
                        "keyword": keyword,
                        "platform": "tokopedia",
                        "url": url
                    }
                }

                filename = f"tokopedia_{keyword.replace(' ', '_')}_page_{page}.json"
                with open(filename, 'w') as f:
                    json.dump(output, f, indent=4)
                print(f"[Tokopedia] File Saved: {filename}")

                time.sleep(2)
            else:
                print(f"Error status {r.status_code}")
                break
        except Exception as e:
            print(f"Error {e}")
            break
    # print(f"[Tokopedia] Success taking keywoard ({keyword}) from Tokopedia")


def scrape_blibli(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.blibli.com/cari/{encoded_keyword}"
    proxies = {
        "http": "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570",
        "https": "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    }

    max_pages = 2
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.6",
        "content-type": "application/json",
        "if-modified-since": "Fri, 20 Feb 2026 04:02:45 GMT",
        "priority": "u=1, i",
        "referer": f"https://www.blibli.com/cari/{encoded_keyword}",
        "sec-ch-ua": '"Not:A-Brand";v="99", "Brave";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    for page in range(1, max_pages + 2):
        base_api_url = "https://www.blibli.com/backend/search/products"
        query_params = {
            "searchTerm": keyword,
            "page": page,
            "start": (page - 1) * 40,
            "merchantSearch": "true",
            "multiCategory": "true",
            "channelId": "mobile-web",
            "itemPerPage": 40
        }
        print(
            f"[Blibli] Scraping keyword ({encoded_keyword}) from Blibli, Page {page}")

        try:
            r = curl_cffi.get(base_api_url, params=query_params,
                              impersonate="chrome110", headers=headers, proxies=proxies)

            if r.status_code == 200:
                print(f"Success Redirecting to{base_api_url}")
                data = r.json()
                items = data.get('data', {})
                if not items:
                    print("Data not found")
                    break

                output = {
                    "raw": items,
                    "metadata": {
                        "keyword": keyword,
                        "platform": "blibli",
                        "url": url
                    }
                }

                print(output)
                filename = f"blibli_{keyword.replace(' ', '_')}_page_{page}.json"
                with open(filename, 'w') as f:
                    json.dump(output, f, indent=4)
                print(f"[Blibli] File Saved: {filename}")
                time.sleep(2)

            else:
                print(f"Error {r.status_code}")

        except Exception as e:
            print(f"Error {e}")
            break

def scrape_shopee(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    max_pages = 2
    with Camoufox(
        os=["windows", "macos", "linux"],
        persistent_context=True,
        user_data_dir='./shopee_session',
        headless=True
        ) as context:
            browser_page = context.new_page()
            page = context.new_page()
            def handle_response(response):
                try:
                    if response.request.resource_type in ['fetch', 'xhr']:
                        url = response.url
                        target_api = "api/v4/search/search_items"
                        if target_api in url:
                            data = response.json()
                            items = data.get("items",[])
                            if not items:
                                print("Data Not Found")
                            output = {
                                "raw": items,
                                "metadata": {
                                    "keyword": keyword,
                                    "platform": "shopee",
                                    "url": f'https://shopee.co.id/search?keyword={encoded_keyword}&page={current_page}'
                                }
                            }
                                
                            filename = f"shopee_{keyword.replace(' ', '_')}_page_{current_page}.json"
                            with open(filename, 'w') as f:
                                json.dump(output, f, indent=4)
                            print(f"[Shopee] File Saved: {filename}")
                    else:
                        pass
                    
                except Exception as e:
                    print(f"[Shopee] Error {e}")
                    
            browser_page.on('response', handle_response)

            
            for current_page in range(0, max_pages):
                print(f"[Shopee] Open Page {current_page}")
                try:
                    print(f"[Shopee] Scraping page {current_page}")
                    url = f"https://shopee.co.id/search?keyword={encoded_keyword}&page={current_page}"
                    browser_page.goto(url)
                    browser_page.wait_for_timeout(10000)
                except Exception as e:
                    print(f"Cannot access pages")
                    pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Penggunaan: python search_keyword.py [lazada/olx] '[keyword]'")
        sys.exit(1)

    platform = sys.argv[1].lower()
    target_keyword = sys.argv[2]

    if platform == "lazada":
        print('See service_lazada.py for more proper implementation')
    elif platform == "olx":
        print('See service_olx.py for more proper implementation')
    elif platform in ["tokopedia", "tokped"]:
        scrape_tokped(target_keyword)
    elif platform == "blibli":
        scrape_blibli(target_keyword)
    elif platform == 'shopee':
        scrape_shopee(target_keyword)
    else:
        print(f"Platform {platform} belum bisa di scrape")
