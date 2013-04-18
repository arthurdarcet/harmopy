#!/usr/bin/env python
import argparse
import configparser
import logging
import time

try:
    from . import rsync
    from . import status
except SystemError:
    import rsync
    import status


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
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    config = configparser.ConfigParser()
    with open(args.config, 'r') as f:
        config.readfp(f)

    rsyncs = rsync.RsyncManager(
        [config[section] for section in config.sections() if section != 'general'],
        config['general']['history_length']
    )
    server = status.StatusThread(args.debug, config, rsyncs)
    server.start()

    while True:
        rsyncs.tick()
        time.sleep(int(config['general']['check_sleep']))

if __name__ == '__main__':
    main()
