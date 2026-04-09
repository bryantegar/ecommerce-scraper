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
from services.service_general import store_raw
from services.service_lazada import ServiceLazada
from settings import BEANS
from workers.base_worker import BaseWorker

HOSTNAME = socket.gethostname()


class WorkerLazada(BaseWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def extract_item_id(url) -> Optional[str]:
        match: re.Match = re.search(r'i(\d+)-', url)
        if match:
            return match.group(1)
        return None

    def handle_exception(self, e: Exception, job=None):
        printinfo(f"Error processing job: {str(e)}")
        if job:
            capture_exception(e)
            self.worker.buryJob(job)

    def worker_scrape_comments(self):
        printinfo("----------------------------------")
        printinfo("Starting Worker Lazada Comments")
        tubename = f'{BEANS[self.config]["prefix"]}_crawler_lazada_comments'
        worker = Worker(
            tubename,
            BEANS[self.config]['host'],
            BEANS[self.config]['port'])
        pusher_self = Pusher(
            tubename,
            host=BEANS[self.config]['host'],
            port=BEANS[self.config]['port'])
        self.worker = worker
        self.set_conn_redis()
        self.set_resources('lazada', 'lazada')
        killer = GracefulKiller()
        if self.use_proxy:
            proxy_cycle = get_proxy_cycle()
            printinfo('Proxy Loaded')
        else:
            proxy_cycle = cycle([None])

        service = ServiceLazada()

        while not killer.kill_now:
            self.current_proxy = next(proxy_cycle)
            job = worker.getJob()
            if not job:
                sleep(10)
            else:
                try:
                    crawl_next = True
                    message = json.loads(job.body)
                    item_id = message['product_id'] if 'item_id' in message else self.extract_item_id(
                        message['product_url'])
                    count = message['count'] if 'count' in message else 0
                    max_count = message['max_count'] if 'max_count' in message else 0
                    if item_id:
                        resp = service.scrape_lazada_comments(
                            item_id, self.cookies, page=count+1, proxy=self.current_proxy)

                        if resp.status_code == 200:
                            fname = store_raw(resp, prefix='lzd-cm', hostname=HOSTNAME,
                                              product_id=item_id, page=count+1,
                                              cookie=self.complete_cookie, social_media='lazada')
                            printinfo('Saved to: '+fname)
                        else:
                            raise HTTPStatusException(
                                resp.status_code,
                                f"Item ID: {item_id}", resp=resp
                            )

                    if count >= max_count:
                        crawl_next = False

                    worker.deleteJob(job)

                    if not crawl_next:
                        self.conn_redis.srem(tubename, item_id)
                    else:
                        message['count'] = count + 1
                        pusher_self.setJob(tubename, json.dumps(message))

                except Exception as e:
                    self.handle_exception(e, job)
                    killer.kill_now = self.kill_now
        self.worker_exit()

    def worker_scrape_keyword(self):
        printinfo("----------------------------------")
        printinfo("Starting Worker Lazada Keyword")
        tubename = f'{BEANS[self.config]["prefix"]}_crawler_lazada_keyword'
        worker = Worker(
            tubename,
            BEANS[self.config]['host'],
            BEANS[self.config]['port'])
        pusher_self = Pusher(
            tubename,
            host=BEANS[self.config]['host'],
            port=BEANS[self.config]['port'])
        self.worker = worker
        self.set_conn_redis()
        self.set_resources('lazada', 'lazada')
        killer = GracefulKiller()
        if self.use_proxy:
            proxy_cycle = get_proxy_cycle()
            printinfo('Proxy Loaded')
        else:
            proxy_cycle = cycle([None])

        service = ServiceLazada()

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

                    resp = service.scrape_lazada(
                        keyword, self.cookies, page=count+1, proxy=self.current_proxy)

                    if resp.status_code == 200:
                        fname = store_raw(resp, prefix='lzd-kw', hostname=HOSTNAME,
                                          keyword=keyword, page=count+1,
                                          cookie=self.complete_cookie, social_media='lazada')
                        printinfo('Saved to: '+fname)
                    else:
                        raise HTTPStatusException(
                            resp.status_code,
                            f"Keyword: {keyword} - page: {count}", resp=resp
                        )
                    if count >= max_count:
                        crawl_next = False

                    worker.deleteJob(job)

                    if not crawl_next:
                        self.conn_redis.srem(tubename, keyword)
                    else:
                        message['count'] = count + 1
                        pusher_self.setJob(tubename, json.dumps(message))
                except Exception as e:
                    self.handle_exception(e, job)
                    killer.kill_now = self.kill_now
        self.worker_exit()
    
    def worker_scrape_store(self):
        printinfo("----------------------------------")
        printinfo("Starting Worker Lazada Store")
        tubename = f'{BEANS[self.config]["prefix"]}_crawler_lazada_store'
        worker = Worker(
            tubename,
            BEANS[self.config]['host'],
            BEANS[self.config]['port'])
        pusher_self = Pusher(
            tubename,
            host=BEANS[self.config]['host'],
            port=BEANS[self.config]['port'])
        self.worker = worker
        self.set_conn_redis()
        self.set_resources('lazada', 'lazada')
        killer = GracefulKiller()
        if self.use_proxy:
            proxy_cycle = get_proxy_cycle()
            printinfo('Proxy Loaded')
        else:
            proxy_cycle = cycle([None])

        service = ServiceLazada()

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
                    store_name = service.extract_shop_name(store_url)
                    count = message['count'] if 'count' in message else 0
                    max_count = message['max_count'] if 'max_count' in message else 0
                    
                    resp = service.scrape_lazada_store(message['url'], page=count+1, proxy=self.current_proxy)
                    if resp.status_code == 200:
                        fname = store_raw(resp, prefix='lzd-store', hostname=HOSTNAME,
                                          store_name=store_name, page=count+1, social_media='lazada')
                        printinfo('Saved to: '+fname)
                    else:
                        raise HTTPStatusException(
                            resp.status_code,
                            f"Store: {shop_name}", resp=resp
                        )

                    if count >= max_count:
                        crawl_next = False

                    worker.deleteJob(job)

                    if not crawl_next:
                        self.conn_redis.srem(tubename, item_id)
                    else:
                        message['count'] = count + 1
                        pusher_self.setJob(tubename, json.dumps(message))

                except Exception as e:
                    self.handle_exception(e, job)
                    killer.kill_now = self.kill_now
        self.worker_exit()
