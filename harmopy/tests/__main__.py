import itertools
import unittest
import logging
import os
import sys
import tempfile

if __name__ == '__main__' and __package__ == '':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import harmopy
    __package__ = 'harmopy'

from . import __main__ as main
from . import config

class Tests(unittest.TestCase):
    def setUp(self):
        logging.root.disabled = True
        self.main = main.Main('harmopy/tests/tests.conf')

    def test_get_config(self):
        pass


    def test_config_main_sections(self):
        expected = {
            'general': {
                'history_length': 200,
                'check_sleep': 10,
            },
            'status': {
                'host': '127.0.0.1',
                'port': 50000,
                'allow_conf_edit': True,
            },
        }
        self.assertEqual(dict((section, dict(v.items())) for section, v in self.main.config.main_sections), expected)

    def test_config_files(self):
        expected = {
            'directory 1': {
                'source': 'rsync://rsync.de.gentoo.org/gentoo-portage',
                'dest': '/tmp/harmopy-tests',
                'rsync_args': '-aP',
                'max_runtime': None,
                'user': None,
            },
            'dir2': {
                'source': 'blah',
                'dest': '/tmp/harmopy-tests',
                'rsync_args': '-aP',
                'max_runtime': None,
                'user': None,
            },
        }
        res = dict(self.main.config.files)
        for k,v in expected.items():
            for kk,vv in v.items():
                self.assertEqual(res[k][kk], vv)
        self.assertTrue(res['dir2']['should_run'](0,1,2))

    def test_config_setter(self):
        self.main.config['dir2']['should_run'] = 'lambda x,y,z: x*z'
        self.assertEqual(self.main.config['dir2']['should_run'](3,1,2), 6)
        for v,w in [
            (None, None),
            ('null', None),
            (1, 1),
            ('true', True),
            (True, True),
            ('false', False),
            ('False', False),
            (False, False),
            ('  ', None),
        ]:
            self.main.config['dir2']['rsync_args'] = v
            self.assertEqual(self.main.config['dir2']['rsync_args'], w)


if __name__ == '__main__':
    unittest.main()
