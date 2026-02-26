import hashlib
import json
from time import time
from urllib import parse

from requests import Response
from requests.utils import cookiejar_from_dict


from libs.logger import printinfo
from curl_cffi import requests


class ServiceTokopedia:
    def __init__(self):
        pass

    def scrape_keyword(self, keyword, proxy=None, page=1):
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
