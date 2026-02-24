from settings import PROXIES
from itertools import cycle
from urllib.parse import urlparse


def get_proxy_cycle(key='default'):
    proxies = []
    for proxy in PROXIES[key]:
        parsed = urlparse(proxy['auth_url'])
        proxies.append({'https': proxy['auth_url'],
                        'redis-key': f"{parsed.hostname}:{parsed.port}:{parsed.username}"})
    return cycle(proxies)
