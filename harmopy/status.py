import cherrypy
import datetime
import functools
import json
import logging
import os.path
import threading

from . import config
from . import logs

# Monkey patch to avoid getting self closing server
from cherrypy.process import servers
servers.wait_for_occupied_port = lambda h,p: None

logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M')
        if hasattr(obj, '__call__'):
            return config.Config.LAMBDA_TEXTS[obj]
        return json.JSONEncoder.default(self, obj)

def json_exposed(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        try:
            value = func(*args, **kw)
        except Exception as e:
            value = {'status': 500, 'error': str(e)}
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(value, cls=JSONEncoder).encode('utf8')
    wrapper.exposed = True
    return wrapper


class StatusPage(object):
    def __init__(self, rsyncs, config):
        self._rsyncs = rsyncs
        self._config = config

    def _config_changed(self):
        logger.info('Applying new config')
        self._rsyncs.init(self._config)

    def _config_save(self, data):
        if not self._config['status']['allow_conf_edit']:
            return {'status': 403, 'error': 'Conf edit forbidden'}
        logger.info('Config update: %r', data)

        config_key = data.pop('config_key')
        res = {'status': 200}

        if 'id' in data:
            new_id = data.pop('id')
            res['id'] = new_id

            if new_id != config_key:
                self._config.move_section(config_key, new_id)
                config_key = new_id
        section = self._config[config_key]
        for k,v in data.items():
            if v != '':
                section[k] = v
                res[k] = v
        self._config.save()
        self._config_changed()
        return res

    @json_exposed
    def status(self):
        return dict(
            id='status',
            time=datetime.datetime.now().timestamp(),
            **self._rsyncs.status
        )

    @json_exposed
    def history(self, debug=False):
        if debug:
            return self._rsyncs.history
        return [{
            'speed': h['status'].get('speed', 0),
            'time': h['time'],
        } for h in self._rsyncs.history]

    @json_exposed
    def logs(self):
        return logs.get()

    @json_exposed
    def config(self, **kwargs):
        if 'config_key' in kwargs:
            return self._config_save(kwargs)
        return [{
            'title': title.replace('_', ' ').capitalize(),
            'id': title,
            'items': [{
                'title': k.replace('_', ' ').capitalize(),
                'id': k,
                'value': v,
                'editable': self._config['status']['allow_conf_edit'],
            } for k, v in section.items()],
        } for title, section in self._config.main_sections]

    @json_exposed
    def files(self, **kwargs):
        if 'config_key' in kwargs:
            return self._config_save(kwargs)
        return [dict(section.items(), id=title, editable=self._config['status']['allow_conf_edit'])
            for title, section in self._config.files + [('DEFAULT', self._config['DEFAULT'])]]

    @json_exposed
    def delete(self, file_id):
        logger.info('Deleting file section %r', file_id)
        self._config.remove_section(file_id)
        self._config.save()
        return {
            'status': 200,
            'id': file_id,
        }

    @json_exposed
    def expand(self, file_id):
        files = self._rsyncs.expand(file_id)
        conf = self._config[file_id]
        if conf['source'][-1] != '/':
            conf['source'] += '/'
        if conf['dest'][-1] != '/':
            conf['dest'] += '/'
        next_id = 1
        for is_dir, new_file in files:
            while '{}_{}'.format(file_id, next_id) in self._config:
                next_id += 1
            new_id = '{}_{}'.format(file_id, next_id)
            self._config.add_section(new_id)
            section = self._config.copy_section(file_id, new_id)
            section['source'] += new_file
            section['dest'] += new_file
            if is_dir:
                section['source'] += '/'
                section['dest'] += '/'
        self._config.remove_section(file_id)
        self._config.save()
        self._config_changed()
        return {'status': 200}


class StatusThread(threading.Thread):
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    config = {
        '/': {'log.screen': False},
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': static_dir,
        },
        '/index': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(static_dir, 'index.html'),
        },
    }
    def __init__(self, config, rsyncs):
        super().__init__()
        self.host = config['status']['host']
        self.port = config['status']['port']
        cherrypy.config.update({
            'server.socket_host': self.host,
            'server.socket_port': self.port,
        })
        self.page = StatusPage(rsyncs, config)
        self.daemon = True

    def run(self):
        app = cherrypy.tree.mount(self.page, config=self.config)
        app.log.access_log_format = '{h} "{r}" {s}'
        logger.info('Binded status page socket to %s:%d', self.host, self.port)
        cherrypy.engine.start()

    def stop(self):
        cherrypy.engine.exit()
