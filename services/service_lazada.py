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

    def scrape_lazada_keyword(self, keyword, cookies, page=1, proxy=None):
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
    
    def scrape_lazada_store(self, shop_url, page=1, proxy=None):
        # product_url_list = []
        # with open('lazada_cookies.json', 'r') as f:
        #     cookies_data = json.load(f)
        path = urlparse(shop_url).path
        shop_name = path.split('/')[-1]
        proxy_url = "http://bandung:456xyz@proxycrawler.dashboard.nolimit.id:2570"
        proxies = {"http": proxy_url, "https": proxy_url}
        # cookies = self.get_cookies_data('lazada_cookies.json')
        
        print(f"[Lazada] Scraping product from store ({shop_name}), Page {page}")
        api_url = f"https://www.lazada.co.id/{shop_name}/?ajax=true&from=wangpu&isFirstRequest=true&langFlag=id&page={page}&pageTypeId=2&q=All-Products"
        payload = {}
        headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=1, i',
        'referer': 'https://www.lazada.co.id/',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'x-csrf-token': 'f317f51e157ee',
        'Cookie': '__wpkreporterwid_=02631038-e686-4dcf-1e45-963bf0e95d2e; lzd_cid=6c61c345-5d0e-448c-80be-855661eb8483; lwrid=AgGdQxkMlgpNCTBxquNeX39uI7qt; userLanguageML=id; _bl_uid=dzm71n7wey5d9eq99os86XpsUnab; t_fv=1774947209943; t_uid=G5psM9RjveC5ObhNHfUagzwLIjqaP0YB; xlly_s=1; cna=jHlSIlFNdGgCAbb9+u+KOuWV; _gcl_au=1.1.1920824345.1774947210; _ga=GA1.3.1324004323.1774947211; _fbp=fb.2.1774947211615.25591898649954003; lzd_sid=16586375d7a9168994d622115bb938cc; _tb_token_=f317f51e157ee; undefined_click_time=1775111905692; lwrtk=AAIEac5/YSObKRLwTAEpWTNwDJbItPTzfcY1YT5EJk2mUEEGie/9Krw=; t_sid=OLshLSrBTcWcd5EZHSKzGcvsJbygwAmD; utm_channel=NA; _m_h5_tk=ca955e520455adb7febcec7e1a4ed612_1775119831152; _m_h5_tk_enc=94a531cb353e80b1b22c5ac2ba05aa68; hng=ID|id-ID|IDR|360; hng.sig=to18pG508Hzz7EPB_okhuQu8kDUP3TDmLlnu4IbIOY8; EGG_SESS=S_Gs1wHo9OvRHCMp98md7CXpHQ05eSuwQd-wSkDjjIh6uQCRoYb0bdyVgjdluDfMvMmW2ak8PM7Lu5PPbo_JfWhhHAkw6ECTjk3Y8zeikas08HGkJQPBXoyenLVdisR4wF4ZzDc0FjmcGuKqIvFu12x6gNGPJYbgwZCJb3jn9CI=; _gid=GA1.3.1848751026.1775113268; _gat_UA-29801013-1=1; AMCVS_126E248D54200F960A4C98C6%40AdobeOrg=1; AMCV_126E248D54200F960A4C98C6%40AdobeOrg=-1124106680%7CMCIDTS%7C20546%7CMCMID%7C28013983688099196300847155555133644639%7CMCAAMLH-1775718068%7C3%7CMCAAMB-1775718068%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1775120468s%7CNONE%7CvVersion%7C5.2.0; _uetsid=b9b982d02e6111f18fea0fa73ee7eaf5; _uetvid=17fe69502cdf11f184e759fbc941ac50; _ga_44FMGEPY40=GS2.3.s1775113268$o2$g1$t1775113312$j16$l0$h0; isg=BJWVwRxbUBqXknTjDGEjyJRApJFPkkmkONkTcBc6I4wcbrRg3-K6dYItOGpYtmFc; epssw=12*n8vyL0BGGI60-0LzV-_lEUT0Gtrzml3SqQ_Ymw_a95LzljohMFczlGGIMFvhML53rjcnplIGGbS3miDjNcjSQT7wjYsLD3jOt0OMWieMj_UVfC8pc-s9P73pFNBajwm7AgVmmyMjBZE6XqOWgVkDq046jGJGMPetRGIGuRnh-zz9uO0YXRFKjwItUhIfgRDO7eUqCjPw461ie0zLesCMIGGGGrbHsL14IMeisk8gwl5n3GrGGMEvGGGIjmlNAJIOabziSNvtSsiRaTptJ6s1D3xw7GrOtIbN_zmqaLTj-13vt3jpHM07jEfRSVF6rzE8XMrOJw92MQYrqlzR-6jrhw..; tfstk=gYwmX-OOGSlbWVLPKFkfw87-qtCJkxMsJPptWA3Na4uWkEpYbGDgmP2Ocl7bS74Y8qJYBxEarP4hfSUOGV4oh8FvBqQjIlzKIwQdp9EbqYMNJwhJqZx-LcnwuFhw4TktjOsEcvqbcAt7rzwEbo6MEXytbAzZU4oj0ARqgKSoacotQKlw3QurPckZQju2ULoEAnowgfSu44iZQVzZQgDrPckZ7PkZ_iCqlRyzUwPHGEVtNcwomj0UqT9wImpKg2rqrd-rombZ8ouk7F0eX1QzqoQDduHbHymLkTJ0-oPU7WzPEKc7gu2iORTV4AlZPfe47ERqxx0mT-lyvLEr_72oH-76OuEouXD8w__x6x40O2GVNaagqqUanb8cyVFL2-lu8apu5fV4o0kF4SAyTzPHC0STUCOsg0ioJ6Hcsr6oMTSNqgAFfjoSc2IlqCOsg0ioJgjkTOGqVmgd.; _m_h5_tk=2c33210b5ff997e95317c977a013415e_1774798785044; _m_h5_tk_enc=5e913bb7b8e453b4f5be8f0d65ffe775; x5secdata=xg5709c1ea87fc5033naeab76b6ef1eff53e4f68aa9969a762b01775113420a1984346082a-2092571265abaxc3dajrecaptcha33b17c35bca214dd6a4b30f5f2434efd6c9__bx__www.lazada.co.id:443/bebelac; x5sectag=195562'
        } 
        resp = requests.get(api_url, impersonate="chrome110", headers=headers, proxies=proxy)
        return resp
