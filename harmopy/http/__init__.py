import cherrypy
import os.path
import threading

from . import status

# Monkey patch to avoid getting self closing server
from cherrypy.process import servers
servers.wait_for_occupied_port = lambda h,p: None


class StatusThread(threading.Thread):
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
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
        self.status_page = status.Page(rsyncs, config)
        self.daemon = True

    def run(self):
        app = cherrypy.tree.mount(self.status_page, '/status' config=self.config)
        app.log.access_log_format = '{h} "{r}" {s}'
        logger.info('Binded http socket to %s:%d', self.host, self.port)
        cherrypy.engine.start()

    def stop(self):
        cherrypy.engine.exit()
