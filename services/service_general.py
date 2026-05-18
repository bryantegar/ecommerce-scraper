from typing import Dict, Union
from requests import Response
from settings import PATH
from datetime import datetime

import uuid
import json
import os


def store_raw(resp: Union[Response, Dict, list],
              prefix=None,
              social_media='misc',
              category='misc',
              **kwargs):

    fname = '{}.json'.format(uuid.uuid4().hex)

    if prefix:
        fname = prefix + '-' + fname

    folder = os.path.join(
        PATH['default']['rawpath'],
        social_media,
        category
    )

    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, fname)

    with open(filepath, 'w', encoding='utf-8') as f:

        if isinstance(resp, Dict):
            data = {'raw': resp}
            url = None

        elif isinstance(resp, list):
            data = {'raw': resp}
            url = None

        else:
            try:
                data = {'raw': resp.json()}
            except Exception:
                data = {'raw_text': resp.text}

            url = getattr(resp, 'url', None)

        data['metadata'] = {
            'crawltime': int(datetime.now().timestamp()),
            'url': url
        }

        for key, value in kwargs.items():
            data['metadata'][key] = value

        f.write(json.dumps(
            data,
            default=str,
            ensure_ascii=False,
            indent=4
        ))

    return filepath