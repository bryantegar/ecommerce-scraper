import sys
import requests
import json
import time
import urllib.parse
import curl_cffi

def get_cookies_data(cookies_file):
    with open(cookies_file, 'r') as f:
        data = json.load(f)
    
    cookies_dict = {c['name']: c['value'] for c in data}
    
    cookies_string = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
    
    # token = cookies_dict.get('_m_h5_tk', '').split('_')[0]
    return cookies_string
    

def scrape_lazada(keyword):
    proxy_url = "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    proxies = {"http": proxy_url, "https": proxy_url}
    encoded_keyword = urllib.parse.quote(keyword)
    cookies = get_cookies_data('lazada_cookies.json')
    
    max_pages = 2
    
    for page in range(1, max_pages + 1):
        print(f"[Lazada] Scraping keyword ({encoded_keyword}) from Lazada, Page {page}")
        api_url = f"https://www.lazada.co.id/catalog/?ajax=true&isFirstRequest=true&page={page}&q={encoded_keyword}"
        headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Referer": "https://www.lazada.co.id/",
                "Accept": "application/json, text/plain, */*",
                "Cookie": "__wpkreporterwid_=505b7114-f6dd-4698-3de2-17975374a302; miidlaz=miidgl3vcs1j90s7lepr44k; t_fv=1762039933572; t_uid=zZK4vjlaQojkbsmlB4FiUOdoVtyHCIJW; lwrid=AgGaQcOrAVp%2ByGA3cSsLX39uI5Qx; lzd_cid=f6e5d77d-06a4-4e85-b04d-87f843e91374; lzd_click_id=clkgg5vbk1j9qnl02145te; userLanguageML=id; hng=ID|id-ID|IDR|360; hng.sig=to18pG508Hzz7EPB_okhuQu8kDUP3TDmLlnu4IbIOY8; EGG_SESS=S_Gs1wHo9OvRHCMp98md7B_AOzS4gJXS3a879XlsGAFHMr2NdtjrJ88SyxS-w0eQ25K9eqOggzpmf5wV8XQ86HlOuT7Dd9qFBAf6CoW6Sd79mnhcsHxbLHNvjo5wC_HxMsym2Uv0IgbbC3ei_acYb3S-qj0Qw5S_GlDXY7spi9A=; t_sid=yQwt2xqTDggTiBdtzp8oXKMFEGkh0Tt8; utm_channel=NA; lzd_sid=1c0af417030600baf4b7566b59f75d4a; _tb_token_=7ddaee5de1e8b; clkgg5vbk1j9qnl02145te_click_time=1771810287037; _m_h5_tk=436205e8bbc9c4844db2cadbb2172c06_1771817855051; _m_h5_tk_enc=95ac75040133d39b086879ce00222dcd; lwrtk=AAIEaZwebkxw/pkgDr9gCHJX/Hhf/85cFjpwPmHzbs5FsVukdKlkFlw=; isg=BCkpBH5VZMNab1jqo7P9mnC8ONWD9h0omOwIu8sepZBPkkmkE0Yt-BcBUC6kCrVg; csc-auto-init=1; __itrace_wid=77f6df93-7f39-4af5-a9e3-cbb122738a57; epssw=11*mmL-1mCJPTrwfObg3uAkDO8KcAVpiXAP7RRChhghXfxwKPy5rFcnJPx7YhiYhYabyPVTXRhvbjQpKC6OarAPmuTEp5HK7RmmarAXOpDgDEIQh4AsEOAQQRAZfvj99jfspwymJS6bhIEzOmdbMyu5gy5GommiVXeiJ4A-gYV7nSrXexB71K67ueYi3qUmJdaL9LkArDBx9aFAseRmHB_EBqu-_f5IhtnCpq1viPJEmmHuuO8muuMCtOP71lFuuK7bWBmmqmBERAcSB_ETEmNmyRdmuu0plcymuuyemmBmuu7YNxn0V9-uu_aaBja5HHLxaYI3LL1K9_f8mCF0; tfstk=gIvjdGNs5r4berixWrozRpZJ9k61C0kUGls9xhe4XtBYWPKdzOo0_jj1CaTGu1dqSUZDFewa3qcDXR6NB2uELv-SmOXt8RduWRacfiFtQsIAetjN0Mghdv-DmuEk3RGKLAgZxUsOWFCAyzIdy5IOMFCJ2GQ8HGeAXzn5jaBOXGeYeYIOxieAXFK-VGbRWOCvWTn5jaQOBOhMuzsoGa-jfKKTj8q52nQ7BRpxi17C05y_CLsfGdKAPoZXFisfR1iYkN9vzhp2n_casOxyOFO9yYwX5ndpWZJ-JR_wtKxJUsEQdOC1lQpANle90T_27CTjlSbvgU1h2_EsKg8FynvvNc4JDe7fHgCrpDtR6QJctKu8h9dH0tR9yYwXJgSzLw6-P5i6SRs580i7s5XhcHQ6F88JSsIl49oSVWPGMgj550i7s5fAqg2KV0NQi"
                }     
        try:
            # print(api_url)
            r = curl_cffi.get(api_url, impersonate="chrome110", headers=headers)
            # # response = requests.get(api_url)
            # print(r.text)
            # print(r.content)
            print(r.status_code)
            if r.status_code == 200:
                print(f"[Lazada] Success directing to: {api_url}")
                print(r.content)
                data = r.json()
                items = data.get('mods', {})
                
                if not items:
                    print("Data not found")
                    break
                
                output = {
                    "raw": items,
                    "metadata": {
                        "keyword": keyword,
                        "platform": "lazada",
                        "url": api_url
                    }
                }
                
                filename = f"lazada_{keyword.replace(' ', '_')}_page_{page}.json"
                with open(filename, 'w') as f:
                    json.dump(output, f, indent=4)
                print(f"[Lazada] FIle Saved: {filename}")
                
                time.sleep(5)
            else:
                print(f"Error status {r.status_code}")
                break
        except Exception as e:
            print(f"Error {e}")
            break
    # print(f"[Lazada] Success taking keywoard ({keyword}) from Lazada")

def scrape_olx(keyword, max_pages=3):
    proxy_url = "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    proxies = {"http": proxy_url, "https": proxy_url}
    encoded_keyword = urllib.parse.quote(keyword)
    max_pages = 2
    
    for page in range(1, max_pages + 1):
        print(f"[OLX] Scraping keyword ({encoded_keyword}) from OLX, Page {page}")
        api_url = f"https://www.olx.co.id/api/relevance/v4/search?facet_limit=100&location=4000030&location_facet_limit=40&page={page}&platform=web-desktop&query={keyword}&relaxedFilters=true"
        
        try:
            r = requests.get(api_url, impersonate="chrome110", proxies=proxies)
            
            if r.status_code == 200:
                print(f"[OLX] Success directing to: {api_url}")
                print(r.body)
                data = r.json()
                items = data.get("data",[])
                if not items:
                    print("Data Not Found")
                    break
                
                output = {
                    "raw": items,
                    "metadata": {
                        "keyword": keyword,
                        "platform": "olx",
                        "url": api_url
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
            print("Error ",e)
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
        print(f"[Tokopedia] Scraping keyword ({encoded_keyword}) from Tokopedia, Page {page}")
        api_url = "https://gql.tokopedia.com/graphql/SearchProductV5Query"
        url = f"https://www.tokopedia.com/search?st=&q={keyword}"
        
        payload = [{
            "operationName": "SearchProductV5Query",
            "variables": {
                # "params": f"device=desktop&enter_method=normal_search&l_name=sre&navsource=&ob=23&page={page}&q={keyword}&rows=60&source=search"
                "params": f"device=desktop&enter_method=normal_search&l_name=sre&ob=23&page={page}&q={keyword}&related=true&rows=60&safe_search=false&sc=&scheme=https&shipping=&show_adult=false&source=search&st=product&start=0&topads_bucket=true&unique_id=7e500e7f1e364ce215992821ccbbd74a&user_addressId=&user_cityId=176&user_districtId=2274&user_id=&user_lat=&user_long=&user_postCode=&user_warehouseId=&variants=&warehouses="
            },
            "query" : "query SearchProductV5Query($params: String!) { searchProductV5(params: $params) { header { totalData responseCode keywordProcess keywordIntention componentID isQuerySafe additionalParams backendFilters meta { dynamicFields __typename } __typename } data { totalDataText banner { position text applink url imageURL componentID trackingOption __typename } redirection { url __typename } related { relatedKeyword position trackingOption otherRelated { keyword url applink componentID products { oldID: id id: id_str_auto_ name url applink mediaURL { image __typename } shop { oldID: id id: id_str_auto_ name city tier __typename } badge { oldID: id id: id_str_auto_ title url __typename } price { text number __typename } freeShipping { url __typename } labelGroups { position title type url styles { key value __typename } __typename } rating wishlist ads { id productClickURL productViewURL productWishlistURL tag __typename } meta { oldWarehouseID: warehouseID warehouseID: warehouseID_str_auto_ componentID __typename } __typename } __typename } __typename } suggestion { currentKeyword suggestion query text componentID trackingOption __typename } ticker { oldID: id id: id_str_auto_ text query applink componentID trackingOption __typename } violation { headerText descriptionText imageURL ctaURL ctaApplink buttonText buttonType __typename } products { oldID: id id: id_str_auto_ ttsProductID name url applink mediaURL { image image300 videoCustom __typename } shop { oldID: id id: id_str_auto_ ttsSellerID name url city tier __typename } stock { ttsSKUID __typename } badge { oldID: id id: id_str_auto_ title url __typename } price { text number range original discountPercentage __typename } freeShipping { url __typename } labelGroups { position title type url styles { key value __typename } __typename } labelGroupsVariant { title type typeVariant hexColor __typename } category { oldID: id id: id_str_auto_ name breadcrumb gaKey __typename } rating wishlist ads { id productClickURL productViewURL productWishlistURL tag __typename } meta { oldParentID: parentID parentID: parentID_str_auto_ oldWarehouseID: warehouseID warehouseID: warehouseID_str_auto_ isImageBlurred isPortrait __typename } __typename } __typename } __typename } }"
        }]
        
        headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "x-device": "desktop"
        }
        
        try:
            # print(api_url)
            r = curl_cffi.post(api_url, json=payload, impersonate="chrome110", headers=headers, proxies=proxies)
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
        print(f"[Blibli] Scraping keyword ({encoded_keyword}) from Blibli, Page {page}")
        
        try:
            r = curl_cffi.get(base_api_url, params=query_params, impersonate="chrome110", headers=headers, proxies=proxies)
            
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
                        "platform": "tokopedia",
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
    


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Penggunaan: python search_keyword.py [lazada/olx] '[keyword]'")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    target_keyword = sys.argv[2]
    
    if platform == "lazada":
        scrape_lazada(target_keyword)
    elif platform == "olx":
        scrape_olx(target_keyword)
    elif platform in ["tokopedia", "tokped"]:
        scrape_tokped(target_keyword)
    elif platform == "blibli":
        scrape_blibli(target_keyword)
    else:
        print(f"Platform {platform} belum bisa di scrape")
        