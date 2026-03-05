from itertools import cycle
import json
import socket
from time import sleep

from sentry_sdk import capture_exception

from libs.beans import Pusher, Worker
from libs.exc import HTTPStatusException
from libs.graceful_killer import GracefulKiller
from libs.logger import printinfo
from libs.proxies import get_proxy_cycle
from services.service_general import store_raw
from services.service_tokopedia import ServiceTokopedia
from settings import BEANS
from workers.base_worker import BaseWorker

HOSTNAME = socket.gethostname()


class WorkerTokopedia(BaseWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle_exception(self, e: Exception, job=None):
        printinfo(f"Error processing job: {str(e)}")
        if job:
            capture_exception(e)
            self.worker.buryJob(job)

    def worker_scrape_keyword(self):
        printinfo("----------------------------------")
        printinfo("Starting Worker Tokopedia Keyword")
        tubename = f'{BEANS[self.config]["prefix"]}_crawler_tokopedia_keyword'
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
        self.set_resources('tokopedia', 'tokopedia')
        killer = GracefulKiller()
        if self.use_proxy:
            proxy_cycle = get_proxy_cycle()
            printinfo('Proxy Loaded')
        else:
            proxy_cycle = cycle([None])

        service = ServiceTokopedia()

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
                    resp = service.scrape_keyword(
                        keyword, page=count+1, proxy=self.current_proxy)
                    if resp.status_code == 200:
                        fname = store_raw(resp, prefix='toped-kw', hostname=HOSTNAME,
                                          keyword=keyword, page=count+1, social_media='tokopedia')
                        printinfo('Saved to: '+fname)

                    else:
                        raise HTTPStatusException(
                            resp.status_code,
                            f"Keyword: {keyword} - page: {count}",
                            resp=resp)
                    worker.deleteJob(job)

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
