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
                'level': logging.DEBUG if debug else logging.INFO if info else logging.WARNING,
            },
            'memory': {
                '()': MemoryHandler,
                'capacity': 100,
                'formatter': 'short',
                'level': logging.DEBUG if debug else logging.INFO,
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
                'handlers': ['memory'],
                'level': logging.DEBUG,
            },
            'cherrypy': {
                'level': logging.INFO if info or debug else logging.WARNING,
            },
        },
        'root': {
            'handlers': ['console'],
        }
    })
