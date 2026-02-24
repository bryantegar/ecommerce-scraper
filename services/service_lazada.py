from urllib import parse

from requests import Response
from requests.utils import cookiejar_from_dict


from libs.exc import HTTPStatusException
from libs.logger import printinfo
from search_keyword import get_cookies_data
from curl_cffi import requests


class ServiceLazada:
    def __init__(self):
        ...

    def get_cookiejar(self, cookies):
        cookiejar_dict = {}
        for c in cookies:
            cookiejar_dict[c['name']] = c['value']
        cookiejar = cookiejar_from_dict(cookiejar_dict)
        return cookiejar

    def get_cookie_headers(self, cookies):
        cookie_headers = []
        for c in cookies:
            cookie_headers.append(f"{c['name']}={c['value']}")
        return "; ".join(cookie_headers)

    def scrape_lazada(self, keyword, cookies, page=1, proxy=None):
        encoded_keyword = parse.quote(keyword)

        printinfo(
            f"{encoded_keyword} - Page: {page}")
        api_url = f"https://www.lazada.co.id/catalog/?ajax=true&isFirstRequest=true&page={page}&q={encoded_keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://www.lazada.co.id/",
            "Accept": "application/json, text/plain, */*",
            "Cookie": self.get_cookie_headers(cookies)
        }
        resp: Response = requests.get(
            api_url, impersonate="chrome110", headers=headers, proxies=proxy)

        return resp

        # if resp.status_code == 200:
        #     return resp.json()
        # else:
        #     raise HTTPStatusException(
        #         resp.status_code, f"Failed to scrape Lazada with keyword: {keyword} and page: {page}", resp=resp)
