from itertools import cycle
import json
import socket
from time import sleep

# from sentry_sdk import capture_exception

from libs.beans import Pusher, Worker
from libs.exc import HTTPStatusException
from libs.graceful_killer import GracefulKiller
from libs.logger import printinfo
from libs.proxies import get_proxy_cycle
from services.service_general import store_raw
from services.service_tokopedia import ServiceTokopedia
# from settings import BEANS
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
        tubename = f'_crawler_tokopedia_keyword'
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
    
    def worker_comments(self):
        printinfo("----------------------------------")
        printinfo("Starting Worker Tokopedia Keyword")
        tubename = f'_crawler_tokopedia_comments'
        worker = Worker(
            tubename,
            host='localhost', 
            port = 14711)
        pusher_self = Pusher(
            tubename,
            host='localhost', 
            port = 14711)
        # w = Worker(tubename='test_link')
        # p = Producer(tubename='test_link')
        self.worker = worker
        self.set_conn_redis()
        self.set_resources('tokopedia', 'tokopedia')
        killer = GracefulKiller()
        service = ServiceTokopedia()
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
                    keyword = message['content']
                    count = message['count'] if 'count' in message else 0
                    max_count = message['max_count'] if 'max_count' in message else 0
                    resp = service.scrape_keyword(
                        keyword, page=count+1, proxy=self.current_proxy)
                    if resp.status_code == 200:
                        # fname = store_raw(resp, prefix='tokped-comments', hostname=HOSTNAME,
                        #                   keyword=keyword, page=count+1, social_media='tokopedia')
                        # printinfo('Saved to: '+fname)
                        print(resp.json())
                    else:
                        raise HTTPStatusException(
                            resp.status_code,
                            f"Comments: {keyword} - page: {count}",
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
        
        
        
        
        
        
        
        
        print("[*] Tokopedia Worker is active...")
        print("[*] Press Ctrl+C to stop.")
        while not killer.kill_now:
            job = w.getJob(timeout=5)
            
            if not job:
                continue
            
            try:
                message = json.loads(job.job_data)
                url_product = message['url_product']
                current_page = message.get('page', 1)
                max_page = message.get('max_page', 2)
                
                print(f" [+] Processing: {url_product} | Page: {current_page}")
                
                resp = service.scrape_tokopedia_comments(url_product, page=current_page)   
                
                if resp.status_code == 200:
                    store_raw(
                        raw=resp.json(), 
                        platform='tokopedia', 
                        type_data='comments', 
                        url_product=url_product, 
                        page=current_page
                    )
                    
                    w.deleteJob(job)
                    if current_page < max_page:
                        message['page'] = current_page + 1
                        p.setJob(json.dumps(message))
                        print(f" [->] Push to job {current_page + 1}")
                    else:
                        print(f" Done {url_product} already reach {max_page} max page.")
                elif resp.status_code == 403:
                    w.releaseJob(job)   
            except Exception as e:
                print(f" [X] Error: {e}")
                w.buryJob(job)
            
        print(f"\n[!] Stop {killer._signal}")
        
    def worker_store(self):
        w = Worker(tubename='tokopedia_store_link')
        p = Producer(tubename='tokopedia_store_link')
        p_comment = Producer(tubename='tokopedia_shop_link')
        killer = GracefulKiller()
        service = ServiceTokopedia()
        print("[*] Tokopedia Worker is active...")
        print("[*] Press Ctrl+C to stop.")
        product_url_list=[]
        while not killer.kill_now:
            job = w.getJob(timeout=5)
            
            if not job:
                continue
            
            try:
                message = json.loads(job.job_data)
                url_store = message['url_store']
                current_page = message.get('page', 1)
                max_page = message.get('max_page', 2)
                
                print(f" [+] Processing: {url_store} | Page: {current_page}")
                
                resp = service.get_shop_product(url_store, page=current_page)   
                
                res_json = resp.json()
                if resp.status_code == 200:
                    first_node = res_json[0].get('data', {})
                    shop_product_node = first_node.get('GetShopProduct') 
                    items = shop_product_node.get('data', [])
                    for item in items:
                        url = item.get('product_url') 
                        product_url_list.append(url)
                        comment_job = {
                                "url_product": url,
                                "page": 1,
                                "max_page": 10 
                        }
                        p_comment.setJob(json.dumps(comment_job))
                    print(f"Obtained {len(product_url_list)} Links")
                    print(product_url_list)
                    store_raw(
                        raw=resp.json(), 
                        platform='tokopedia', 
                        type_data='store', 
                        url_store=url_store, 
                        page=current_page
                    )
                    
                    w.deleteJob(job)
                    if current_page < max_page:
                        message['page'] = current_page + 1
                        p.setJob(json.dumps(message))
                        print(f" [->] Push to job {current_page + 1}")
                    else:
                        print(f" Done {url_store} already reach {max_page} max page.")
                elif resp.status_code == 403:
                    w.releaseJob(job)         
            except Exception as e:
                print(f" [X] Error: {e}")
                w.buryJob(job)
            
        print(f"\n[!] Stop {killer._signal}")
