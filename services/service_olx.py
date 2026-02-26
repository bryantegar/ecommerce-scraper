from curl_cffi import requests
from urllib import parse

from requests import Response


class ServiceOLX:
    def __init__(self):
        ...

    def scrape_olx(self, keyword, page=0, proxy=None):
        url = 'https://www.olx.co.id/api/relevance/v4/search'

        params = {
            "facet_limit": "100",
            "location": "1000001",  # indonesia
            "location_facet_limit": "40",
            "platform": "web-desktop",
            "query": keyword,
            "relaxedFilters": "true"
        }
        if page > 0:
            params['page'] = page

        resp: Response = requests.get(
            url, params=params, impersonate="chrome110", proxies=proxy)
        return resp
