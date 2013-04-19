import unittest
import os
import sys

if __name__ == '__main__' and __package__ == '':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import harmopy
    __package__ = 'harmopy'

from . import __main__ as main

class Tests(unittest.TestCase):
    def setUp(self):
        self.main = main.Main('harmopy/tests/tests.conf')
        self.main.config['test1']['dest'] = tempfile.TemporaryDirectory()
        self.main.start()

    def test_get_config(self):
        pass

if __name__ == '__main__':
    unittest.main()
