import cherrypy
import functools
import json
import threading

from . import logs

# Monkey patch to avoid getting self closing server
from cherrypy.process import servers
def fake_wait_for_occupied_port(host, port): return
servers.wait_for_occupied_port = fake_wait_for_occupied_port


cherrypy.log.access_log_format = '{h} "{r}" {s}'
def json_exposed(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        value = func(*args, **kw)
        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps(value).encode('utf8')
    wrapper.exposed = True
    return wrapper

class StatusPage(object):
    def __init__(self, rsyncs, config):
        self._rsyncs = rsyncs
        self._config = config

    @json_exposed
    def status(self):
        return self._rsyncs.status

    @json_exposed
    def history(self):
        return self._rsyncs.history

    @json_exposed
    def logs(self):
        return logs.get()

    @json_exposed
    def config(self, **kwargs):
        return dict((k, dict(v)) for k,v in dict(self._config).items())



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
        app = cherrypy.tree.mount(self.page, config={'/':{}})
        app.log.access_log_format = '{h} "{r}" {s}'
        cherrypy.engine.start()

    def stop(self):
        cherrypy.engine.exit()
