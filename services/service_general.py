from typing import Dict, Union
from requests import Response
from settings import PATH
from datetime import datetime

import uuid
import json


def store_raw(resp: Union[Response, Dict, list], prefix=None, **kwargs):
    fname = '{}.json'.format(uuid.uuid4().hex)
    if prefix:
        fname = prefix + '-' + fname
    with open('{}{}'.format(PATH['default']['rawpath'], fname), 'w') as f:
        if isinstance(resp, Dict):
            data = {'raw': resp}
            url = None
        elif isinstance(resp, list):
            data = {'raw': resp}
            url = None
        else:
            data = {'raw': resp.json()}
            url = resp.url
        data['metadata'] = {'crawltime': int(datetime.now().timestamp())}
        data['metadata']['url'] = url
        for key, value in kwargs.items():
            data['metadata'][key] = value
        f.write(json.dumps(data, default=str))
    return fname
