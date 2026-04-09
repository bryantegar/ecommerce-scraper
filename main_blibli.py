import argparse
import sentry_sdk
from settings import SENTRY
from sentry_sdk import set_tags

from workers.worker_blibli import WorkerBlibli


if __name__ == '__main__':
    choices = [
        'worker_blibli_keyword',
        'worker_blibli_comments',
        'worker_blibli_store'
    ]
    parser = argparse.ArgumentParser(description='Worker Blibli',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-m', '--mode', metavar='', type=str,
                        help='Worker Mode',
                        choices=choices)
    parser.add_argument('--max-page', metavar='', type=int,
                        help='Max page to be crawled',
                        default=20)
    parser.add_argument('-c', '--config', metavar='', type=str,
                        help='Config File', default='default')
    parser.add_argument('--allowed-usage', metavar='', type=str,
                        help='Cookie Allowed Usage', default='for_auto')
    parser.add_argument('--cookie',
                        help='Use Cookie', action='store_true')
    parser.add_argument('--do-not-use-proxy',
                        help='Do not use proxy', action='store_false', default=True)
    parser.set_defaults(cookie=False)
    args = parser.parse_args()
    mode = args.mode
    allowed_usage = args.allowed_usage
    config = args.config

    sentry_sdk.init(
        dsn=SENTRY[config]['dsn'],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        environment=SENTRY[config]['env']
    )
    set_tags({'process.social_media': 'blibli',
              'process.name': mode})
    if mode == 'worker_blibli_keyword':
        worker_blibli = WorkerBlibli(
            config=config,
            allowed_usage=args.allowed_usage,
            use_proxy=args.do_not_use_proxy)
        worker_blibli.worker_keyword()
    
    elif mode == 'worker_blibli_comments':
        worker_blibli = WorkerBlibli(
            config=config,
            allowed_usage=args.allowed_usage,
            use_proxy=args.do_not_use_proxy)
        worker_blibli.worker_comments()
        
    elif mode == 'worker_blibli_store':
        worker_blibli = WorkerBlibli(
            config=config,
            allowed_usage=args.allowed_usage,
            use_proxy=args.do_not_use_proxy)
        worker_blibli.worker_store()