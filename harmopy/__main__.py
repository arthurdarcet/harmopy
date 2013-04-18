#!/usr/bin/env python
import argparse
import configparser
import logging
import os
import sys
import time

if __name__ == '__main__' and __package__ == '':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import harmopy
    __package__ = 'harmopy'

from . import logs
from . import rsync
from . import status


def main(config='harmopy.conf'):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Log debug messages',
        default=False
    )
    parser.add_argument(
        '-c', '--config',
        help='Config file',
        default=config,
    )

    args = parser.parse_args()

    config = configparser.ConfigParser()
    with open(args.config, 'r') as f:
        config.readfp(f)

    rsyncs = rsync.RsyncManager(
        [dict(config[section]) for section in config.sections() if section not in ('general', 'status')],
        int(config['general']['history_length'])
    )
    server = status.StatusThread(args.debug, config, rsyncs)
    logs.config('DEBUG' if args.debug else 'INFO')
    try:
        server.start()
        while True:
            rsyncs.tick()
            time.sleep(int(config['general']['check_sleep']))
    except KeyboardInterrupt:
        server.stop()

if __name__ == '__main__':
    main()
