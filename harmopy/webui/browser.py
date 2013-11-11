import cherrypy
import logging

from . import utils


logger = logging.getLogger(__name__)

class Page:
    def __init__(self, rsyncs, config):
        self._rsyncs = rsyncs
        self._config = config

    @utils.json_exposed
    def list(self, *args):
        if len(args) == 0:
            return [key for key, _ in self._config.files]
        else:
            if args[0] not in self._config:
                raise cherrypy.HTTPError(400, 'unknown rsync target {!r}'.format(args[0]))
            return self._rsyncs.expand(args[0], '/'.join(args[1:]))
