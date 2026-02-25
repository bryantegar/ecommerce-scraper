import hashlib
import json
from time import time
from urllib import parse

from requests import Response
from requests.utils import cookiejar_from_dict


from libs.logger import printinfo
from curl_cffi import requests


class ServiceLazada:
    def __init__(self):
        ...

    def generate_lazada_sign(self, token, timestamp, app_key, data_json):
        raw_string = f"{token}&{timestamp}&{app_key}&{data_json}"
        return hashlib.md5(raw_string.encode('utf-8')).hexdigest()

    def process_cookies(self, cookies):
        cookiejar_dict = {}
        cookie_headers = []
        for c in cookies:
            cookiejar_dict[c['name']] = c['value']
            cookie_headers.append(f"{c['name']}={c['value']}")

        cookiejar = cookiejar_from_dict(cookiejar_dict)
        cookie_header = "; ".join(cookie_headers)
        token = cookiejar_dict.get('_m_h5_tk', '').split('_')[0]

        return cookiejar, cookie_header, token

    def scrape_lazada(self, keyword, cookies, page=1, proxy=None):
        encoded_keyword = parse.quote(keyword)
        cookiejar, cookie_header, token = self.process_cookies(cookies)

        printinfo(
            f"{encoded_keyword} - Page: {page}")
        api_url = f"https://www.lazada.co.id/catalog/?ajax=true&isFirstRequest=true&page={page}&q={encoded_keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.lazada.co.id/",
            "Accept": "application/json, text/plain, */*",
            "Cookie": cookie_header
        }
        resp: Response = requests.get(
            api_url, impersonate="chrome110", headers=headers, proxies=proxy)

        return resp

    def scrape_lazada_comments(self, item_id, cookies, page=1, proxy=None):
        cookiejar, cookie_header, token = self.process_cookies(cookies)
        # COOKIE_FULL = cookies
        _timestamp = str(int(time() * 1000))
        APP_KEY = 24677475

        data = {
            "itemId": item_id,
            "pageSize": 5,
            "pageNo": page,
            "ratingFilter": 0,
            "sort": 0,
            "tagId": 0
        }
        data_string = json.dumps(data, separators=(',', ':'))
        _sign = self.generate_lazada_sign(
            token, _timestamp, APP_KEY, data_string)
        url = (
            f"https://acs-m.lazada.co.id/h5/mtop.lazada.review.item.getpcreviewlist/1.0/?"
            f"jsv=2.6.1&appKey={APP_KEY}&t={_timestamp}&sign={_sign}&"
            f"api=mtop.lazada.review.item.getPcReviewList&v=1.0&type=originaljson&"
            f"isSec=1&AntiCreep=true&timeout=10000&dataType=json&sessionOption=AutoLoginOnly&"
            f"x-i18n-language=id&x-i18n-regionID=ID"
        )
        payload = {"data": data_string}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.lazada.co.id/",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": cookie_header
        }
        response: Response = requests.post(
            url, data=payload, headers=headers, impersonate="chrome110", proxies=proxy)
        return response
