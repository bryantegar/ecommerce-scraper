import sys
import json
import hashlib
import time
import re
import urllib.parse
from urllib.parse import urlparse
from curl_cffi import requests

def generate_lazada_sign(token, timestamp, app_key, data_json):
    raw_string = f"{token}&{timestamp}&{app_key}&{data_json}"
    return hashlib.md5(raw_string.encode('utf-8')).hexdigest()

def get_cookies_data(cookies_file):
    with open(cookies_file, 'r') as f:
        data = json.load(f)
    
    cookies_dict = {c['name']: c['value'] for c in data}
    
    cookies_string = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
    
    token = cookies_dict.get('_m_h5_tk', '').split('_')[0]
    return token, cookies_string

def extract_item_id_lazada(url):
    match = re.search(r'i(\d+)-', url)
    if match:
        return int(match.group(1))
    return None

def get_product_main_info(url):
    proxy_url = "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    proxies = {"http": proxy_url, "https": proxy_url}
    path_parts = urllib.parse.urlparse(url).path.strip('/').split('/')
    if len(path_parts) < 2:
        print("URL tidak valid")
        return None
        
    shop_domain = path_parts[0]
    product_key = path_parts[1]
    print(shop_domain, product_key)
    
    api_url = "https://gql.tokopedia.com/graphql/PDPMainInfo"
    
    query = """
    fragment ProductMedia on pdpDataProductMedia {\n  media {\n    type\n    urlOriginal: URLOriginal\n    urlThumbnail: URLThumbnail\n    urlMaxRes: URLMaxRes\n    videoUrl: videoURLAndroid\n    prefix\n    suffix\n    description\n    variantOptionID\n    __typename\n  }\n  videos {\n    source\n    url\n    __typename\n  }\n  __typename\n}\n\nfragment ProductHighlight on pdpDataProductContent {\n  name\n  price {\n    value\n    currency\n    priceFmt\n    slashPriceFmt\n    discPercentage\n    __typename\n  }\n  campaign {\n    campaignID\n    campaignType\n    campaignTypeName\n    campaignIdentifier\n    background\n    percentageAmount\n    originalPrice\n    discountedPrice\n    originalStock\n    stock\n    stockSoldPercentage\n    threshold\n    startDate\n    endDate\n    endDateUnix\n    appLinks\n    isAppsOnly\n    isActive\n    hideGimmick\n    showStockBar\n    __typename\n  }\n  thematicCampaign {\n    additionalInfo\n    background\n    campaignName\n    icon\n    __typename\n  }\n  stock {\n    useStock\n    value\n    stockWording\n    __typename\n  }\n  variant {\n    isVariant\n    parentID\n    __typename\n  }\n  wholesale {\n    minQty\n    price {\n      value\n      currency\n      __typename\n    }\n    __typename\n  }\n  isCashback {\n    percentage\n    __typename\n  }\n  isTradeIn\n  isOS\n  isPowerMerchant\n  isWishlist\n  isCOD\n  preorder {\n    duration\n    timeUnit\n    isActive\n    preorderInDays\n    __typename\n  }\n  __typename\n}\n\nfragment ProductInfo on pdpDataProductInfo {\n  row\n  content {\n    title\n    subtitle\n    applink\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDetail on pdpDataProductDetail {\n  title\n  productDetailDescription {\n    title\n    content\n    __typename\n  }\n  content {\n    title\n    subtitle\n    applink\n    showAtFront\n    isAnnotation\n    __typename\n  }\n  __typename\n}\n\nfragment ProductSocial on pdpDataSocialProof {\n  row\n  content {\n    icon\n    title\n    subtitle\n    applink\n    type\n    rating\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDataInfo on pdpDataInfo {\n  icon\n  title\n  isApplink\n  applink\n  content {\n    icon\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment ProductCustomInfo on pdpDataCustomInfo {\n  icon\n  title\n  isApplink\n  applink\n  separator\n  description\n  __typename\n}\n\nfragment ProductVariant on pdpDataProductVariant {\n  errorCode\n  parentID\n  defaultChild\n  sizeChart\n  totalStockFmt\n  variants {\n    productVariantID\n    variantID\n    name\n    identifier\n    option {\n      picture {\n        urlOriginal: url\n        urlThumbnail: url100\n        __typename\n      }\n      productVariantOptionID\n      variantUnitValueID\n      value\n      hex\n      stock\n      __typename\n    }\n    __typename\n  }\n  children {\n    productID\n    price\n    priceFmt\n    slashPriceFmt\n    discPercentage\n    optionID\n    optionName\n    productName\n    productURL\n    picture {\n      urlOriginal: url\n      urlThumbnail: url100\n      __typename\n    }\n    stock {\n      stock\n      isBuyable\n      stockWordingHTML\n      minimumOrder\n      maximumOrder\n      __typename\n    }\n    isCOD\n    isWishlist\n    campaignInfo {\n      campaignID\n      campaignType\n      campaignTypeName\n      campaignIdentifier\n      background\n      discountPercentage\n      originalPrice\n      discountPrice\n      stock\n      stockSoldPercentage\n      startDate\n      endDate\n      endDateUnix\n      appLinks\n      isAppsOnly\n      isActive\n      hideGimmick\n      isCheckImei\n      minOrder\n      showStockBar\n      __typename\n    }\n    thematicCampaign {\n      additionalInfo\n      background\n      campaignName\n      icon\n      __typename\n    }\n    ttsPID\n    ttsSKUID\n    __typename\n  }\n  __typename\n}\n\nfragment ProductCategoryCarousel on pdpDataCategoryCarousel {\n  linkText\n  titleCarousel\n  applink\n  list {\n    categoryID\n    icon\n    title\n    isApplink\n    applink\n    __typename\n  }\n  __typename\n}\n\nfragment ProductDetailMediaComponent on pdpDataProductDetailMediaComponent {\n  title\n  description\n  contentMedia {\n    url\n    ratio\n    type\n    __typename\n  }\n  show\n  ctaText\n  __typename\n}\n\nfragment PdpDataComponentShipmentV4 on pdpDataComponentShipmentV4 {\n  data {\n    productID\n    warehouse_info {\n      warehouse_id\n      is_fulfillment\n      district_id\n      postal_code\n      geolocation\n      city_name\n      ttsWarehouseID\n      __typename\n    }\n    useBOVoucher\n    isCOD\n    metadata\n    __typename\n  }\n  __typename\n}\n\nquery PDPMainInfo($productKey: String, $shopDomain: String, $layoutID: String, $extraPayload: String, $queryParam: String, $source: String, $userLocation: pdpUserLocation) {\n  pdpMainInfo(shopDomain: $shopDomain, productKey: $productKey, layoutID: $layoutID, extraPayload: $extraPayload, queryParam: $queryParam, source: $source, userLocation: $userLocation) {\n    requestID\n    extraPayload\n    data {\n      layoutName\n      basicInfo {\n        alias\n        createdAt\n        isQA\n        id: productID\n        shopID\n        shopName\n        minOrder\n        maxOrder\n        weight\n        weightUnit\n        condition\n        status\n        url\n        needPrescription\n        catalogID\n        isLeasing\n        isBlacklisted\n        isTokoNow\n        defaultMediaURL\n        menu {\n          id\n          name\n          url\n          __typename\n        }\n        blacklistMessage {\n          identifier\n          imageURL\n          title\n          description\n          button\n          buttonArea\n          buttonName\n          url\n          supportingImage {\n            url\n            width\n            height\n            __typename\n          }\n          __typename\n        }\n        category {\n          id\n          name\n          title\n          breadcrumbURL\n          isAdult\n          isKyc\n          minAge\n          detail {\n            id\n            name\n            breadcrumbURL\n            isAdult\n            __typename\n          }\n          ttsID\n          ttsDetail {\n            id\n            name\n            breadcrumbURL\n            isAdult\n            __typename\n          }\n          __typename\n        }\n        txStats {\n          transactionSuccess\n          transactionReject\n          countSold\n          paymentVerified\n          itemSoldFmt\n          __typename\n        }\n        stats {\n          countView\n          countReview\n          countTalk\n          rating\n          __typename\n        }\n        productID\n        ttsPID\n        ttsSKUID\n        ttsShopID\n        isAggregatedWithTTS\n        __typename\n      }\n      __typename\n    }\n    components {\n      name\n      type\n      kind\n      position\n      data {\n        ...ProductMedia\n        ...ProductHighlight\n        ...ProductInfo\n        ...ProductDetail\n        ...ProductSocial\n        ...ProductDataInfo\n        ...ProductCustomInfo\n        ...ProductVariant\n        ...ProductCategoryCarousel\n        ...ProductDetailMediaComponent\n        ...PdpDataComponentShipmentV4\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n
    """
    
    payload = [{
        "operationName": "PDPMainInfo",
        "variables": {
            "productKey": product_key,
            "shopDomain": shop_domain,
            "source": "P1"
        },
        "query": query
    }]
    
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "referer": "https://www.tokopedia.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-device": "desktop",
        "x-source": "tokopedia-lite",
        "x-tkpd-akamai": "pdpMainInfo",
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, impersonate="chrome110", proxies=proxies)
        
        if response.status_code == 200:
            res_json = response.json()
            
            main_info = res_json[0].get('data', {}).get('pdpMainInfo', {}).get('data', {})
            if not main_info:
                print("Data not found")
                return None
                
            
            p_id = main_info.get('basicInfo', {}).get('id')
            output = {
                "raw": main_info,
                "metadata": {
                    "product_id": p_id,
                    "platform": "tokopedia",
                    "url": url
                }
            }
            filename = f"tokopedia_product_main_info_{p_id}.json"
            with open(filename, 'w') as f:
                json.dump(output, f, indent=4)
            print(f"Saved: {filename}")
            return p_id
            
        else:
            print(f"HTTP Error: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None
        
        
def scrape_lazada_comments(product_url):
    proxy_url = "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    proxies = {"http": proxy_url, "https": proxy_url}
    item_id = extract_item_id_lazada(product_url)
    if not item_id:
        print("❌ Gagal mendapatkan Item ID dari URL. Pastikan format link benar.")
        return
    token, cookies = get_cookies_data('lazada_cookies.json')
    
    max_pages = 2
    for page in range(1, max_pages + 1):
        TOKEN_FROM_COOKIE = token
        COOKIE_FULL = cookies
        TIMESTAMP = str(int(time.time() * 1000))
        APP_KEY = 24677475

        DATA_Ulasan = {
            "itemId": item_id, 
            "pageSize": 5,
            "pageNo": page,
            "ratingFilter": 0,
            "sort": 0,
            "tagId": 0
        }
        data_string = json.dumps(DATA_Ulasan, separators=(',', ':'))

        hasil_sign = generate_lazada_sign(TOKEN_FROM_COOKIE, TIMESTAMP, APP_KEY, data_string)

        api_url = (
            f"https://acs-m.lazada.co.id/h5/mtop.lazada.review.item.getpcreviewlist/1.0/?"
            f"jsv=2.6.1&appKey={APP_KEY}&t={TIMESTAMP}&sign={hasil_sign}&"
            f"api=mtop.lazada.review.item.getPcReviewList&v=1.0&type=originaljson&"
            f"isSec=1&AntiCreep=true&timeout=10000&dataType=json&sessionOption=AutoLoginOnly&"
            f"x-i18n-language=id&x-i18n-regionID=ID"
        )

        payload = {"data": data_string}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.lazada.co.id/",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": COOKIE_FULL
        }

        print(f"🚀 Memproses Item ID: {item_id}")
        print(f"🔑 Sign Generated: {hasil_sign}")
        print(f"Page: {page}")
        all_review  = []

        try:
            response = requests.post(api_url, data=payload, headers=headers, impersonate="chrome110", proxies=proxies)
            
            if response.status_code == 200:
                data = response.json()
                with open("review_data.json", 'w') as f:
                    json.dump(data, f, indent=4)
                    
                review_data = data.get('data', {})              
                if not review_data:
                    print("Review data not found")
                    break
                
                output = {
                    "raw": review_data,
                    "metadata": {
                        "product_id": str(item_id),
                        "platform": "lazada",
                        "url": product_url
                    }
                }
                
                filename = f"lazada_comment_productid_{item_id}_page_{page}.json"
                with open(filename, 'w') as f:
                    json.dump(output, f, indent=4)
                print(f"Saved: {filename}")
                
                time.sleep(2)
                
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")
            return None

def scrape_tokopedia_comments(product_url):
    proxy_url = "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    proxies = {"http": proxy_url, "https": proxy_url}
    product_id = get_product_main_info(product_url)
    api_url = "https://gql.tokopedia.com/graphql/productReviewList"
    
    max_pages = 2
    for page in range(1, max_pages + 1):
        query = """
        query productReviewList($productID: String!, $page: Int!, $limit: Int!, $sortBy: String, $filterBy: String) {
        productrevGetProductReviewList(productID: $productID, page: $page, limit: $limit, sortBy: $sortBy, filterBy: $filterBy) {
        productID
            list {
            id: feedbackID
            message
            productRating
            reviewCreateTime
            user {
                fullName
            }
            likeDislike {
                totalLike
            }
            }
            hasNext
            totalReviews
        }
        }
        """
        payload = [{
        "operationName": "productReviewList",
        "variables": {
            "productID": str(product_id),
            "page": page,
            "limit": 10,
            "sortBy": "informative_score desc",
            "filterBy": ""
        },
        "query": query
        }]
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "x-device": "desktop",
        }

        try:
            print(f"💬 [Tokopedia] Memproses ID: {product_id} | Page: {page}")
            r = requests.post("https://gql.tokopedia.com/graphql", json=payload, headers=headers, impersonate="chrome110", proxies=proxies)
            
            if r.status_code == 200:
                res_json = r.json()
                raw_data = res_json[0].get('data', {}).get('productrevGetProductReviewList', {})

                final_output = {
                    "raw": raw_data, 
                    "metadata": {
                        "product_id": str(product_id),
                        "platform": "tokopedia",
                        "url": api_url
                    }
                }
                
                filename = f"tokopedia_comment_{product_id}_page_{page}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(final_output, f, indent=4, ensure_ascii=False)
                print(f"✅ Saved Tokopedia Comment: {filename}")
                time.sleep(2)
            else:
                print(f"❌ Error Tokopedia {r.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
def scrape_blibli_comments(product_url):
    proxy_url = "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
    proxies = {"http": proxy_url, "https": proxy_url}
    path = urlparse(product_url).path 
    last_part = path.split('/')[-1] 

    product_id = last_part.replace("is--", "").rsplit("-", 1)[0]
    print(f"{product_id}")

    max_page = 2

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.6",
        "content-type": "application/json",
        "if-modified-since": "Fri, 20 Feb 2026 04:02:45 GMT",
        "priority": "u=1, i",
        "referer": f"{product_url}",
        "sec-ch-ua": '"Not:A-Brand";v="99", "Brave";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    }

    for page in range(1, max_page + 1):
        print(f"💬 [Blibli] Memproses ID: {product_id} | Page: {page}")
        api_url = f"https://www.blibli.com/backend/product-review/public-reviews?itemPerPage=5&page={page}&hasMedia=true&productSku={product_id}"
        
        try:
            r = requests.get(api_url, headers=headers, impersonate="chrome110", proxies=proxies)
        
            if r.status_code == 200:
                data = r.json()
                items = data.get('data',[])
                final_output = {
                                "raw": items,
                                "metadata": {
                                    "product_id": str(product_id),
                                    "platform": "blibli",
                                    "url": api_url
                            }
                        }
                filename = f"blibli_comment_{product_id}_page_{page}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(final_output, f, indent=4, ensure_ascii=False)
                print(f"✅ Saved Blibli Comment: {filename}")
                time.sleep(2)
            else:
                print(f"Error {r.status_code}")
                
        except Exception as e:
            print(f"Error {e}")
        
        

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Penggunaan: python get_comment_list.py [lazada/tokopedia] '[link]'")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    product_url = sys.argv[2]
    
    if platform == "lazada":
        scrape_lazada_comments(product_url)
    elif platform == "olx":
        print(f"OLX doesn't have comment")
    elif platform in ["tokopedia", "tokped"]:
        scrape_tokopedia_comments(product_url)
    elif platform == "blibli":
        scrape_blibli_comments(product_url)
    else:
        print(f"Platform {platform} belum bisa di scrape")