import cherrypy
import logging
import os.path
import threading

from . import browser
from . import status


# Monkey patch to avoid getting self closing server
from cherrypy.process import servers
servers.wait_for_occupied_port = lambda h,p: None

logger = logging.getLogger(__name__)

class Thread(threading.Thread):
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
        self.status = status.Page(rsyncs, config)
        self.browser = browser.Page(rsyncs, config)
        self.daemon = True

    def mount(self, page, point):
        config = self.config.copy()
        config.update(getattr(page, 'app_config', {}))
        app = cherrypy.tree.mount(page, point, config=config)
        app.log.access_log_format = '{h} "{r}" {s}'

    def run(self):
        self.mount(self, '/')
        self.mount(self.status, '/status')
        self.mount(self.browser, '/browser')

        logger.info('Binded http socket to %s:%d', self.host, self.port)
        cherrypy.engine.start()

    def stop(self):
        cherrypy.engine.exit()
