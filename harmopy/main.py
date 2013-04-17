#!/usr/bin/env python2
import argparse
import ConfigParser
import logging
import time

try:
    from . import rsync
    from . import status
except ValueError:
    import rsync
    import status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Log debug messages', default=False)

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    rsyncs = rsync.RsyncManager([])
    server = status.Status(rsyncs)
    server.start()

    while True:
        # check runtime
        rsyncs.tick()
        time.sleep(42)

if __name__ == '__main__':
    main()
