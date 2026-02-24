import socket
from libs.beans import Pusher
from redis import Redis
from libs.exc import NoAvailableResourceException
from settings import REDIS, BEANS, PATH
from sentry_sdk import capture_exception
from .logger import printerror, printinfo
import requests
import base64
import json
import sys

HOSTNAME = socket.gethostname()


def cookie_from_sleep(social_media, usage, config='default'):
    conn_redis = Redis(host=REDIS[config]['host'],
                       port=REDIS[config]['port'], decode_responses=True,
                       password=REDIS[config]['password'])
    resp_redis = conn_redis.lpop(
        f'{social_media}_{usage}_cookie_stock')
    conn_redis.close()
    return resp_redis


def fresh_cookie_from_resource(allowed_usage, social_media, config='default', count=1):
    url = "https://crawlercluster.dashboard.nolimit.id/crawler-resource/fetch"
    params = {'allowed_usage': allowed_usage,
              'social_media': social_media,
              'client_id': f'periodic-crawler-{HOSTNAME}',
              'with_valid_cookies': 'true',
              'count': count
              }
    resp = requests.get(url, params=params)
    return resp


def fresh_cookie_from_redis(social_media, allowed_usage, config='default'):
    conn_redis = Redis(host=REDIS[config]['host'],
                       port=REDIS[config]['port'], decode_responses=True,
                       password=REDIS[config]['password'])
    resp_redis = conn_redis.lpop(
        f'{social_media}_{allowed_usage}_fresh_cookie')
    conn_redis.close()
    return resp_redis


def process_cookies(resp_content, from_file=False):
    cookies = resp_content[0]['sessionInfo']['cookie']
    for cookie in cookies:
        value: str = cookie['value']
        if value.startswith('base64'):
            cookie['value'] = base64.b64decode(value[7:]).decode()
    resource_id = resp_content[0]['originalId']
    user_credential = resp_content[0]['crawlingAccessForm']['userCredential']

    return cookies, resource_id, user_credential, resp_content, from_file


def processed_cookie_from_sleep(social_media, config='default'):
    conn_redis = Redis(host=REDIS[config]['host'],
                       port=REDIS[config]['port'], decode_responses=True,
                       password=REDIS[config]['password'])
    resp_redis = conn_redis.lpop(
        f'{social_media}_cookie_stock')
    conn_redis.close()
    content = json.loads(resp_redis)
    printinfo('Sleeping cookies available')
    return process_cookies(content, False)


def get_cookies(filename, allowed_usage, social_media, config='default', save=True, retries=5, get_from_resource=False):
    run = True
    count = 0
    from_file = False
    while run:
        try:
            printinfo(f'Attempt {count+1}')

            printinfo('Requesting fresh cookies')
            resp = fresh_cookie_from_redis(social_media, allowed_usage)
            if resp:
                content = json.loads(resp)
            elif get_from_resource:
                resp = fresh_cookie_from_resource(allowed_usage, social_media)
                try:
                    content = resp.json()
                except json.JSONDecodeError:
                    content = []
            else:
                content = []
            if len(content) > 0:
                printinfo('Fresh cookies received')
                break

            printinfo('Waking up sleeping cookies')
            resp_redis = cookie_from_sleep(social_media, allowed_usage, config)
            if resp_redis:
                printinfo('Sleeping cookies available')
                content = json.loads(resp_redis)
                break
            else:
                printinfo('No sleeping cookies available')
            count += 1
            if count >= retries:
                raise NoAvailableResourceException(
                    social_media, allowed_usage)
        except NoAvailableResourceException as e:
            run = False
            # capture_exception()
            printinfo('No fresh cookies available')
            printinfo('Reading cookies from file')
            with open(f"{PATH['default']['cookiepath'].rstrip('/')}/{filename}.json", 'r') as f:
                try:
                    content = json.loads(f.read())
                    from_file = True
                except json.JSONDecodeError as e:
                    run = False
                    sys.exit()
        except Exception as e:
            run = False
            capture_exception()
            sys.exit()

    if not content:
        raise NoAvailableResourceException(
            social_media, allowed_usage)

    return process_cookies(content, from_file)


def release_cookies_with_error(resource_id, message='Token is invalid'):
    url = "https://crawlercluster.dashboard.nolimit.id/crawler-resource/error"
    body = {
        "resourceId": resource_id,
        "error": str(message),
        "validity": "invalid"
    }
    headers = {'Content-Type': 'application/json'}
    return requests.post(url, headers=headers, data=json.dumps(body))


def release_cookies(resource_id):
    url = "https://crawlercluster.dashboard.nolimit.id/crawler-resource/release"
    body = {
        "resourceId": resource_id,
    }
    headers = {'Content-Type': 'application/json'}
    requests.post(url, headers=headers, data=json.dumps(body))


def renew_cookies(credential, config='default'):
    conn_redis = Redis(host=REDIS[config]['host'],
                       port=REDIS[config]['port'], decode_responses=True,
                       password=REDIS[config]['password'])
    message = '{}|{}'.format(credential['username'], credential['password'])
    if not conn_redis.sismember('renew_cookie_instagram', message):
        pusher = Pusher('nolimit_renew_cookie_instagram', BEANS[config]
                        ['host'], BEANS[config]['port'])
        pusher.setJob(message)
        conn_redis.sadd('renew_cookie_instagram', message)
        pusher.close()


def empty_cookie_file(filename):
    with open(f"{PATH['default']['cookiepath'].rstrip('/')}/{filename}.json", 'w') as f:
        f.write("[]")
    printerror('Cookie file emptied')
