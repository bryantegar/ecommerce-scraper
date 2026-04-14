import hashlib
import json
from time import time
from urllib import parse
import urllib.parse
from urllib.parse import urlparse
import random

from requests import Response
from requests.utils import cookiejar_from_dict


from libs.logger import printinfo
from curl_cffi import requests


class ServiceTokopedia:
    def __init__(self):
        ...

    def scrape_tokopedia_keyword(self, keyword, proxy=None, page=1):
        url = "https://gql.tokopedia.com/graphql/SearchProductV5Query"
        # url = f"https://www.tokopedia.com/search?st=&q={keyword}"

        payload = [{
            "operationName": "SearchProductV5Query",
            "variables": {
                "params": f"device=desktop&enter_method=normal_search&l_name=sre&ob=23&page={page}&q={keyword}&related=true&rows=60&safe_search=false&sc=&scheme=https&shipping=&show_adult=false&source=search&st=product&start=0&topads_bucket=true&unique_id=7e500e7f1e364ce215992821ccbbd74a&user_addressId=&user_cityId=176&user_districtId=2274&user_id=&user_lat=&user_long=&user_postCode=&user_warehouseId=&variants=&warehouses="
            },
            "query": "query SearchProductV5Query($params: String!) { searchProductV5(params: $params) { header { totalData responseCode keywordProcess keywordIntention componentID isQuerySafe additionalParams backendFilters meta { dynamicFields __typename } __typename } data { totalDataText banner { position text applink url imageURL componentID trackingOption __typename } redirection { url __typename } related { relatedKeyword position trackingOption otherRelated { keyword url applink componentID products { oldID: id id: id_str_auto_ name url applink mediaURL { image __typename } shop { oldID: id id: id_str_auto_ name city tier __typename } badge { oldID: id id: id_str_auto_ title url __typename } price { text number __typename } freeShipping { url __typename } labelGroups { position title type url styles { key value __typename } __typename } rating wishlist ads { id productClickURL productViewURL productWishlistURL tag __typename } meta { oldWarehouseID: warehouseID warehouseID: warehouseID_str_auto_ componentID __typename } __typename } __typename } __typename } suggestion { currentKeyword suggestion query text componentID trackingOption __typename } ticker { oldID: id id: id_str_auto_ text query applink componentID trackingOption __typename } violation { headerText descriptionText imageURL ctaURL ctaApplink buttonText buttonType __typename } products { oldID: id id: id_str_auto_ ttsProductID name url applink mediaURL { image image300 videoCustom __typename } shop { oldID: id id: id_str_auto_ ttsSellerID name url city tier __typename } stock { ttsSKUID __typename } badge { oldID: id id: id_str_auto_ title url __typename } price { text number range original discountPercentage __typename } freeShipping { url __typename } labelGroups { position title type url styles { key value __typename } __typename } labelGroupsVariant { title type typeVariant hexColor __typename } category { oldID: id id: id_str_auto_ name breadcrumb gaKey __typename } rating wishlist ads { id productClickURL productViewURL productWishlistURL tag __typename } meta { oldParentID: parentID parentID: parentID_str_auto_ oldWarehouseID: warehouseID warehouseID: warehouseID_str_auto_ isImageBlurred isPortrait __typename } __typename } __typename } __typename } }"
        }]

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "x-device": "desktop"
        }

        resp: Response = requests.post(
            url, json=payload, impersonate="chrome110", headers=headers, proxies=proxy)

        return resp

    def get_product_main_info(self, url, proxy=None):
        path_parts = urllib.parse.urlparse(url).path.strip('/').split('/')
        if len(path_parts) < 2:
            print("URL tidak valid")
            return None

        shop_domain = path_parts[0]
        product_key = path_parts[1]
        # print(shop_domain, product_key)

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
            response = requests.post(
                api_url, json=payload, headers=headers, impersonate="chrome110", proxies=proxy)

            if response.status_code == 200:
                res_json = response.json()

                main_info = res_json[0].get('data', {}).get(
                    'pdpMainInfo', {}).get('data', {})
                if not main_info:
                    print("Data not found")
                    return None

                p_id = main_info.get('basicInfo', {}).get('id')
                # output = {
                #     "raw": main_info,
                #     "metadata": {
                #         "product_id": p_id,
                #         "platform": "tokopedia",
                #         "url": url
                #     }
                # }

                # filename = f"tokopedia_product_main_info_{p_id}.json"
                # with open(filename, 'w') as f:
                #     json.dump(output, f, indent=4)
                # print(f"Saved: {filename}")
                return p_id

            else:
                print(f"HTTP Error: {response.status_code}")
                return None

        except Exception as e:
            raise

    def scrape_tokopedia_comments(self, product_url, page=1, proxy=None):
        product_id = self.get_product_main_info(product_url)
        api_url = "https://gql.tokopedia.com/graphql/productReviewList"
        payload = [{
            "operationName": "productReviewList",
            "variables": {
                "productID": str(product_id),
                "page": page,
                "limit": 10,
                "sortBy": "informative_score desc",
                "filterBy": "",
                "sortBy": "create_time desc"
            },
            'query': "query productReviewList($productID: String!, $page: Int!, $limit: Int!, $sortBy: String, $filterBy: String) {\n  productrevGetProductReviewList(productID: $productID, page: $page, limit: $limit, sortBy: $sortBy, filterBy: $filterBy) {\n    productID\n    list {\n      id: feedbackID\n      variantName\n      message\n      productRating\n      reviewCreateTime\n      reviewCreateTimestamp\n      isReportable\n      isAnonymous\n      imageAttachments {\n        attachmentID\n        imageThumbnailUrl\n        imageUrl\n        __typename\n      }\n      videoAttachments {\n        attachmentID\n        videoUrl\n        __typename\n      }\n      reviewResponse {\n        message\n        createTime\n        __typename\n      }\n      user {\n        userID\n        fullName\n        image\n        url\n        __typename\n      }\n      likeDislike {\n        totalLike\n        likeStatus\n        __typename\n      }\n      stats {\n        key\n        formatted\n        count\n        __typename\n      }\n      badRatingReasonFmt\n      __typename\n    }\n    shop {\n      shopID\n      name\n      url\n      image\n      __typename\n    }\n    hasNext\n    totalReviews\n    __typename\n  }\n}\n"
        }]
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "x-device": "desktop",
        }

        response = requests.post(
            api_url, json=payload, headers=headers, impersonate="chrome110", proxies=proxy)
        return response

    def get_shop_id(self, shop_url):
        try:
            path = urlparse(shop_url).path.strip('/')
            shop_name = path.split('/')[-1]

            url = "https://gql.tokopedia.com/graphql/ShopInfoCore"

            payload = [{
                "operationName": "ShopInfoCore",
                "variables": {
                    "id": 0,
                    "domain": shop_name
                },
                "query": "query ShopInfoCore($id: Int!, $domain: String) {\n  shopInfoByID(input: {shopIDs: [$id], fields: [\"core\"], domain: $domain, source: \"shoppage\"}) {\n    result {\n      shopCore {\n        shopID\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
            }]

            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'x-source': 'tokopedia-lite'
            }

            # Tambahkan http_version=requests.HttpVersion.V1_1 jika HTTP/2 bermasalah
            response = requests.post(
                url, headers=headers, json=payload, impersonate="chrome110")

            if response.status_code == 200:
                res_json = response.json()
                data_list = res_json[0].get('data', {})
                shop_info = data_list.get('shopInfoByID', {})
                results = shop_info.get('result', [])
                if results:
                    shop_id = results[0].get('shopCore', {}).get('shopID')
                    return shop_name, str(shop_id)

            print(
                f"Shop {shop_name} tidak ditemukan atau status {response.status_code}")
            return None, None

        except Exception as e:
            raise

    def scrape_tokopedia_store(self, shop_url, page, proxy=None):
        shop_data = self.get_shop_id(shop_url)

        print(shop_data[0])
        if shop_data[0] is None:
            print("Stop, Failed to obtained shop_metadata")
            return
        shop_name, shop_id = shop_data
        api_url = "https://gql.tokopedia.com/graphql/ShopProducts"
        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'x-version': 'a6610c6',
            'Referer': 'https://www.tokopedia.com/',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Brave";v="145", "Chromium";v="145"',
            'x-price-center': 'true',
            'sec-ch-ua-mobile': '?0',
            'bd-device-id': '2412165513116213415',
            'x-source': 'tokopedia-lite',
            'x-device': 'default_v3',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'accept': '*/*',
            'content-type': 'application/json',
            'x-tkpd-lite-service': 'zeus',
        }
        print(f"[Tokopedia] Scraping {shop_name} | Page {page}")
        payload = json.dumps([
            {
                "operationName": "ShopProducts",
                "variables": {
                    "source": "shop",
                    "sid": shop_id,
                    "page": page,
                    "perPage": 80,
                    "etalaseId": "etalase",
                    "sort": 1,
                    "user_districtId": "2274",
                    "user_cityId": "176",
                    "user_lat": "0",
                    "user_long": "0",
                    "usecase": "ace_get_shop_product_v2"
                },
                "query": "query ShopProducts($sid: String!, $source: String, $page: Int, $perPage: Int, $keyword: String, $etalaseId: String, $sort: Int, $user_districtId: String, $user_cityId: String, $user_lat: String, $user_long: String, $usecase: String) {\n  GetShopProduct(shopID: $sid, source: $source, filter: {page: $page, perPage: $perPage, fkeyword: $keyword, fmenu: $etalaseId, sort: $sort, user_districtId: $user_districtId, user_cityId: $user_cityId, user_lat: $user_lat, user_long: $user_long, usecase: $usecase}) {\n    status\n    errors\n    links {\n      prev\n      next\n      __typename\n    }\n    data {\n      name\n      product_url\n      product_id\n      price {\n        text_idr\n        __typename\n      }\n      primary_image {\n        original\n        thumbnail\n        resize300\n        __typename\n      }\n      flags {\n        isSold\n        isPreorder\n        isWholesale\n        isWishlist\n        __typename\n      }\n      campaign {\n        discounted_percentage\n        original_price_fmt\n        start_date\n        end_date\n        __typename\n      }\n      label {\n        color_hex\n        content\n        __typename\n      }\n      label_groups {\n        position\n        title\n        type\n        url\n        styles {\n          key\n          value\n          __typename\n        }\n        __typename\n      }\n      badge {\n        title\n        image_url\n        __typename\n      }\n      stats {\n        reviewCount\n        rating\n        averageRating\n        __typename\n      }\n      category {\n        id\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
            }
        ])
        resp = requests.request(
            "POST", api_url, headers=headers, data=payload, proxies=proxy)
        return resp
