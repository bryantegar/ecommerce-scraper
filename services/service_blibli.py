import json
import time
import urllib.parse
import os
import random
from curl_cffi import requests
from urllib.parse import urlparse
import sys


class ServiceBlibli:
    def __init__(self):
        ...
    
    def scrape_blibli_keyword(self, keyword, proxy=None, page=1):
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://www.blibli.com/cari/{encoded_keyword}"
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
        resp = requests.get(base_api_url, params=query_params, impersonate="chrome110", headers=headers, proxies=proxy)
        return resp
    
    def extract_product_id(self, product_url):
        path = urlparse(product_url).path 
        last_part = path.split('/')[-1] 
        product_id = last_part.replace("is--", "").rsplit("-", 1)[0]
        return product_id
        
    def scrape_blibli_comments(self, product_url, proxy=None, page=1):

        product_id = self.extract_product_id(product_url)
        print(f"{product_id}")
        

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.6",
            "content-type": "application/json",
            # "if-modified-since": "Fri, 20 Feb 2026 04:02:45 GMT",
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
        print(f"[Blibli] Scraping Comments from product ID: {product_id} | Page: {page}")
        api_url = f"https://www.blibli.com/backend/product-review/public-reviews?itemPerPage=5&page={page}&hasMedia=true&productSku={product_id}"
        resp = requests.get(api_url, headers=headers, impersonate="chrome110", proxies=proxy)
            
        return resp
    
    def extract_store_name(self, url_store):
        path = urlparse(url_store).path    
        path_split = path.split('/')
        store = path_split[1]
        store_name = path_split[-1]
        return store_name
    
    
    def scrape_blibli_store(self, url_store, proxy=None, page=1):
        page = int(page)
        # path = urlparse(url_store).path    
        # path_split = path.split('/')
        # store = path_split[1]
        store_name = self.extract_store_name(url_store)   
        start_index = (page - 1) * 40
        itemPerPage = 40
        print(path_split)
        
        if 'brand' in path_split:
            print("brand found")
            query_params = {
                "promoTab": "false",
                "excludeProductList": "false",
                "page": page,
                "start": start_index,
                "itemPerPage": itemPerPage,
                "intent": "false",
                "multiCategory": "true",
                "showFacet": "false",
                "brandSearch": "true"
            }
            base_api_url = f"https://www.blibli.com/backend/search/brand/{store_name}"

            # print(url_store)
            # print(path_store)
            # print(path_name_store)
        elif 'merchant' in path_store:
            print('merchant found')
            query_params = {
                "promoTab": "false",
                "excludeProductList": "false",
                "page": page,          
                "start": start_index,  
                "multiCategory": "true",
                "defaultPickupPoint": "true",
                "facetOnly": "false",
                "pickupPointCode": "PP-3162573", 
                "intent": "false",
                "itemPerPage": 40    
            }
            base_api_url = f"https://www.blibli.com/backend/search/merchant/{store_name}"
            # print(url_store)
            # print(path_store)
            # print(path_name_store)
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "referer": url_store,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        
        print(query_params)
        print(f"[Blibli] Scraping Product from Store: {store_name} | Page: {page}")
        resp = requests.get(base_api_url, params=query_params, impersonate="chrome110", headers=headers, proxies=self.proxies)
                    
        return resp