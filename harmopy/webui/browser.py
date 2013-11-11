import logging

from . import utils


logger = logging.getLogger(__name__)

class Page:
    def __init__(self, rsyncs, config):
        self._rsyncs = rsyncs
        self._config = config

    @utils.json_exposed
    def test(self):
        return {1:2}

    @utils.json_exposed
    def list(self, file_id, path='/'):
        return self._rsyncs.expand(file_id, path)
