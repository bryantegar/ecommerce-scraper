from itertools import cycle
import json
import re
import socket
from time import sleep
from typing import Optional

from sentry_sdk import capture_exception

from libs.beans import Pusher, Worker
from libs.exc import HTTPStatusException
from libs.graceful_killer import GracefulKiller
from libs.logger import printinfo
from libs.proxies import get_proxy_cycle
from libs.cookies_manager import get_cookies
from services.service_general import store_raw
from services.service_shopee import ServiceShopee
from settings import BEANS
from workers.base_worker import BaseWorker

HOSTNAME = socket.gethostname()


class WorkerShopee(BaseWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle_exception(self, e: Exception, job=None):
        printinfo(f"Error processing job: {str(e)}")
        if job:
            capture_exception(e)
            self.worker.buryJob(job)

    def worker_keyword(self):
        printinfo("----------------------------------")
        printinfo("Starting Worker Shopee Keyword")
        tubename = f'{BEANS[self.config]["prefix"]}_crawler_shopee_keyword'
        worker = Worker(
            tubename,
            host='localhost', 
            port = 14711)
        pusher_self = Pusher(
            tubename,
            host='localhost', 
            port = 14711)
        self.worker = worker
        self.set_conn_redis()
        self.set_resources('shopee', 'shopee')
        killer = GracefulKiller()
        if self.use_proxy:
            proxy_cycle = get_proxy_cycle()
            printinfo('Proxy Loaded')
        else:
            proxy_cycle = cycle([None])

        service = ServiceShopee()

        while not killer.kill_now:
            self.current_proxy = next(proxy_cycle)
            job = worker.getJob()
            if not job:
                sleep(10)
            else:
                try:
                    crawl_next = True
                    message = json.loads(job.body)
                    keyword = message['content']
                    count = message['count'] if 'count' in message else 0
                    max_count = message['max_count'] if 'max_count' in message else 0
                    resp = service.scrape_shopee_keyword(
                        keyword, cookies=self.cookies, page=count+1, proxy=self.current_proxy)
                    
                    if resp.get('is_captcha'):
                        print('Captcha detected')
                        worker.releaseJob(job)
                                            
                    elif resp['status'] == 200 and resp['items']:
                        fname = store_raw(resp['items'], prefix='shopee-kw', hostname=HOSTNAME,
                                          keyword=keyword, page=count+1, social_media='shopee')
                        printinfo('Saved to: '+fname)
                        worker.deleteJob(job)
                    else:
                        raise HTTPStatusException(
                            resp['status'],
                            f"Keyword: {keyword} - page: {count}",
                            resp=resp)
                    

                    if count >= max_count:
                        crawl_next = False
                    if crawl_next:
                        message['count'] = count + 1
                        pusher_self.setJob(json.dumps(message))
                    else:
                        self.conn_redis.srem(tubename, keyword)
                except Exception as e:
                    self.handle_exception(e, job)
        self.worker_exit()
    
    def worker_comments(self):
        printinfo("----------------------------------")
        printinfo("Starting Worker Shopee Comments")
        tubename = f'{BEANS[self.config]["prefix"]}_crawler_shopee_comments'
        worker = Worker(
            tubename,
            host='localhost', 
            port = 14711)
        pusher_self = Pusher(
            tubename,
            host='localhost', 
            port = 14711)
        self.worker = worker
        self.set_conn_redis()
        self.set_resources('shopee', 'shopee')
        killer = GracefulKiller()
        service = ServiceShopee()
        if self.use_proxy:
            proxy_cycle = get_proxy_cycle()
            printinfo('Proxy Loaded')
        else:
            proxy_cycle = cycle([None])
        
        while not killer.kill_now:
            self.current_proxy = next(proxy_cycle)
            job = worker.getJob()
            if not job:
                sleep(10)
            else:
                try:
                    crawl_next = True
                    message = json.loads(job.body)
                    product_url = message['product_url']
                    count = message['count'] if 'count' in message else 0
                    max_count = message['max_count'] if 'max_count' in message else 0
                    resp = service.scrape_shopee_comments(
                        product_url, page=count+1, cookies=self.cookies, proxy=self.current_proxy)
                    product_id = resp['product_id']

                    if resp.get('is_captcha'):
                        print('Captcha detected')
                        worker.releaseJob(job)                  
                    elif resp['status'] == 200 and resp['items']:
                        fname = store_raw(resp['items'], prefix='shopee-cm', hostname=HOSTNAME,
                                          product_id=product_id, page=count+1, social_media='shopee')
                        printinfo('Saved to: '+fname)
                        worker.deleteJob(job)
                    else:
                        raise HTTPStatusException(
                            resp.status_code,
                            f"Comments: {product_id} - page: {count}",
                            resp=resp)

                    if count >= max_count:
                        crawl_next = False
                    if crawl_next:
                        message['count'] = count + 1
                        pusher_self.setJob(json.dumps(message))
                    else:
                        self.conn_redis.srem(tubename, product_id)
                except Exception as e:
                    self.handle_exception(e, job)
        self.worker_exit()
        
    def worker_store(self):
        printinfo("----------------------------------")
        printinfo("Starting Worker Shopee Store")
        tubename = f'{BEANS[self.config]["prefix"]}_crawler_shopee_store'
        worker = Worker(
            tubename,
            host='localhost', 
            port = 14711)
        pusher_self = Pusher(
            tubename,
            host='localhost', 
            port = 14711)
        self.worker = worker
        self.set_conn_redis()
        self.set_resources('shopee', 'shopee')
        killer = GracefulKiller()
        service = ServiceShopee()
        if self.use_proxy:
            proxy_cycle = get_proxy_cycle()
            printinfo('Proxy Loaded')
        else:
            proxy_cycle = cycle([None])
        
        while not killer.kill_now:
            self.current_proxy = next(proxy_cycle)
            job = worker.getJob()
            if not job:
                sleep(10)
            else:
                try:
                    crawl_next = True
                    message = json.loads(job.body)
                    store_url = message['store_url']
                    store_name = service.extract_store_name(store_url)
                    count = message['count'] if 'count' in message else 0
                    max_count = message['max_count'] if 'max_count' in message else 0
                    resp = service.scrape_shopee_store(
                        store_url, page=count+1, cookies=self.cookies, proxy=self.current_proxy)
                    
                    if resp.get('is_captcha'):
                        print('Captcha detected')
                        worker.releaseJob(job)
                                            
                    elif resp['status'] == 200 and resp['items']:
                        fname = store_raw(resp['items'], prefix='shopee-store', hostname=HOSTNAME,
                                          store_name=store_name, page=count+1, social_media='shopee')
                        printinfo('Saved to: '+fname)
                        worker.deleteJob(job)
                    else:
                        raise HTTPStatusException(
                            resp.status_code,
                            f"Store: {store_name} - page: {count}",
                            resp=resp)

                    if count >= max_count:
                        crawl_next = False
                    if crawl_next:
                        message['count'] = count + 1
                        pusher_self.setJob(json.dumps(message))
                    else:
                        self.conn_redis.srem(tubename, store_name)
                except Exception as e:
                    self.handle_exception(e, job)
        self.worker_exit()
