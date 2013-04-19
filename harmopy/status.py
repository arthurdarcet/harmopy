import cherrypy
import datetime
import functools
import json
import os.path
import threading

from . import logs

# Monkey patch to avoid getting self closing server
from cherrypy.process import servers
def fake_wait_for_occupied_port(host, port): return
servers.wait_for_occupied_port = fake_wait_for_occupied_port


cherrypy.log.access_log_format = '{h} "{r}" {s}'

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M')
        return json.JSONEncoder.default(self, obj)

def json_exposed(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        value = func(*args, **kw)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(value, cls=JSONEncoder).encode('utf8')
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
        return [{
            'title': section,
            'items': [{
                'title': k,
                'id': k,
                'value': v,
                'editable': self._config['status']['allow_conf_edit'] == 'True',
            } for k, v in values.items()
            if k not in self._config['DEFAULT'].keys()],
        } for section, values in self._config.items()
        if section in self._config.main_sections]

    @json_exposed
    def files(self):
        return self._rsyncs.files


class StatusThread(threading.Thread):
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    config = {
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': static_dir,
        },
        '/index': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(static_dir, 'index.html'),
        },
    }
    def __init__(self, debug, config, rsyncs, *args, **kwargs):
        super(StatusThread, self).__init__(*args, **kwargs)
        cherrypy.config.update({
            'server.socket_host': config['status']['host'],
            'server.socket_port': int(config['status']['port']),
        })
        self.page = StatusPage(rsyncs, config)
        self.daemon = True

    def run(self):
        app = cherrypy.tree.mount(self.page, config=self.config)
        app.log.access_log_format = '{h} "{r}" {s}'
        cherrypy.engine.start()

    def stop(self):
        cherrypy.engine.exit()
