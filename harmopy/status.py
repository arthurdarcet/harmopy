import cherrypy
import json
import threading

# Monkey patch to avoid getting self closing server
from cherrypy.process import servers
def fake_wait_for_occupied_port(host, port): return
servers.wait_for_occupied_port = fake_wait_for_occupied_port


class StatusPage(object):
    def __init__(self, rsyncs, config):
        self._rsyncs = rsyncs
        self._config = config

    @cherrypy.expose
    def status(self):
        return json.dumps(self._rsyncs.status)

    @cherrypy.expose
    def history(self):
        return json.dumps(self._rsyncs.history)

    @cherrypy.expose
    def config(self, **kwargs):
        return json.dumps(kwargs)
        return json.dumps(dict((k, dict(v)) for k,v in dict(self._config).items()))


class StatusThread(threading.Thread):
    def __init__(self, debug, config, rsyncs, *args, **kwargs):
        super(StatusThread, self).__init__(*args, **kwargs)
        cherrypy.config.update({
            'server.socket_host': config['status']['host'],
            'server.socket_port': int(config['status']['port']),
        })
        self.page = StatusPage(rsyncs, config)
        self.daemon = True

    def run(self):
        cherrypy.quickstart(self.page)
