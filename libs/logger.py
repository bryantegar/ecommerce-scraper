from datetime import datetime
import sys


def printinfo(*args):
    print('[{}][INFO] - {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ' - '.join(args)))


def printerror(*args):
    print('[{}][ERROR] - {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ' - '.join(args)),
          file=sys.stderr)
