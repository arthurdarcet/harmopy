import logging
import logging.config
import logging.handlers


class MemoryHandler(logging.handlers.BufferingHandler):
    def emit(self, record):
        self.buffer.append(self.format(record))
        if len(self.buffer) > self.capacity:
            self.acquire()
            try:
                del(self.buffer[0])
            finally:
                self.release()


def get():
    return [h for h in logging.getLogger('harmopy').handlers if isinstance(h, MemoryHandler)][0].buffer[::-1]

def config(debug, info):
    logging.config.dictConfig({
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'clean',
            },
            'memory': {
                '()': MemoryHandler,
                'capacity': 1000,
                'formatter': 'short',
            },
        },
        'formatters': {
            'clean': {
                'format' : '%(asctime)s | %(name)-31s | %(levelname)-8s | %(message)s',
                'datefmt' : '%Y-%m-%d %H:%M:%S',
            },
            'short': {
                'format' : '%(asctime)s | %(levelname)-8s | %(message)s',
                'datefmt' : '%H:%M:%S',
            },
        },
        'loggers': {
            'harmopy': {
                'level': logging.DEBUG if debug else logging.INFO if info else logging.WARNING,
                'handlers': ['memory'],
            },
            'cherrypy': {
                'level': logging.INFO if info or debug else logging.WARNING,
            },
            'cherrypy.error': {
                'level': logging.WARNING
            },
        },
        'root': {
            'handlers': ['console'],
        }
    })
