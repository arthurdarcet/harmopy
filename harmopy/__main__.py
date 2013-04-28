#!/usr/bin/env python
import argparse
import logging
import os
import sys
import threading
import time

if __name__ == '__main__' and __package__ == '':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import harmopy
    __package__ = 'harmopy'

from . import config
from . import logs
from . import rsync
from . import status


class Main(threading.Thread):
    def __init__(self, configfile=None):
        super().__init__()
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-d', '--debug',
            action='store_true',
            help='Log DEBUG messages',
            default=False
        )
        parser.add_argument(
            '-i', '--info',
            action='store_true',
            help='Log INFO messages',
            default=False
        )
        config_arg = parser.add_argument(
            '-c', '--config',
            help='Config file',
            type=argparse.FileType('r'),
            required=True,
        )
        if configfile is not None and os.path.exists(configfile):
            config_arg.default = open(configfile, 'r')

        self.args = parser.parse_args()

        self.config = config.Config(self.args.config)
        self.rsyncs = rsync.RsyncManager(self.config)
        self.server = status.StatusThread(self.config, self.rsyncs)

    def run(self):
        try:
            logs.config(False, False)
            self.server.start()
            logs.config(self.args.debug, self.args.info)
            while True:
                self.rsyncs.tick()
                time.sleep(self.config['general']['check_sleep'])
        except KeyboardInterrupt:
            self.server.stop()

def main(config='harmopy.conf'):
    Main(config).run()

if __name__ == '__main__':
    main()
