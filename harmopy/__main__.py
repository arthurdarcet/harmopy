#!/usr/bin/env python
import argparse
import configparser
import logging
import os
import sys
import threading
import time

if __name__ == '__main__' and __package__ == '':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import harmopy
    __package__ = 'harmopy'

from . import logs
from . import rsync
from . import status


class Main(threading.Thread):
    def __init__(self, config):
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

        self.config = configparser.ConfigParser()
        with open(args.config, 'r') as f:
            self.config.readfp(f)

        self.rsyncs = rsync.RsyncManager(
            [dict(self.config[section]) for section in self.config.sections()
            	if section not in ('general', 'status')],
            int(self.config['general']['history_length'])
        )
        self.server = status.StatusThread(args.debug, self.config, self.rsyncs)
        logs.config('DEBUG' if args.debug else 'INFO')

    def run(self):
        try:
            self.server.start()
            while True:
                self.rsyncs.tick()
                time.sleep(int(self.config['general']['check_sleep']))
        except KeyboardInterrupt:
            self.server.stop()

def main(config='harmopy.conf'):
    Main(config).run()

if __name__ == '__main__':
    main()
