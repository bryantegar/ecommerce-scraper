import sys

from redis import Redis

from libs.cookies_manager import get_cookies, release_cookies, release_cookies_with_error
from libs.exc import NoAvailableResourceException
from libs.logger import printerror, printinfo
from settings import REDIS


class BaseWorker:
    def __init__(self, config='default', allowed_usage='for_auto', use_proxy=True):
        self.config = config
        self.allowed_usage = allowed_usage
        self.use_proxy = use_proxy
        self.cookies = None
        self.resource_id = None
        self.user_credential = None
        self.complete_cookie = None
        self.from_file = None
        self.cookie_filename = None
        self.release_cookie = False
        self.cookie_error = False
        self.cookie_error_message = 'Token is invalid'
        self.kill_now = False

    def worker_exit(self):
        if self.resource_id:
            printinfo('Releasing Cookie Resource: ' + self.resource_id)
            if self.cookie_error:
                resp = release_cookies_with_error(
                    self.resource_id, self.cookie_error_message)
                if resp.status_code == 200:
                    printinfo('Resource: ' + self.resource_id +
                               ' released with error: ' + str(self.cookie_error_message))
                else:
                    printinfo('Error releasing resource: ' + self.resource_id
                               )
                    printinfo(f'{resp.status_code} - {resp.text}')
            else:
                release_cookies(self.resource_id)
                printinfo('Resource: ' + self.resource_id + ' released')

    def set_resources(self, social_media, filename):
        printinfo(f'Requesting Cookies - Allowed Usage: {self.allowed_usage}')

        try:
            cookies, resource_id, user_credential, complete_cookie, from_file = get_cookies(
                filename, self.allowed_usage, social_media, retries=1)
        except NoAvailableResourceException as e:
            printerror('No Cookies Available')
            sys.exit(1)

        self.cookies = cookies
        self.resource_id = resource_id
        self.user_credential = user_credential
        self.complete_cookie = complete_cookie
        self.from_file = from_file
        self.cookie_filename = filename
        printinfo('Resource ID: ' + self.resource_id)

    def set_conn_redis(self):
        self.conn_redis = Redis(host=REDIS[self.config]['host'],
                                port=REDIS[self.config]['port'], decode_responses=True,
                                password=REDIS[self.config]['password'])
