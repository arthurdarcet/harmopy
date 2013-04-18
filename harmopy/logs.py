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
    return [h for h in logging.root.handlers if isinstance(h, MemoryHandler)][0].buffer

def config(level):
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
                'formatter': 'clean',
            },
        },
        'formatters': {
            'clean': {
                'format' : '%(asctime)s | %(levelname)-8s | %(name)-10s | %(message)s',
                'datefmt' : '%Y-%m-%d %H:%M:%S',
            },
        },
        'loggers': {
            '': {
                'level': level,
                'handlers': ['console', 'memory'],
            },
            'cherrypy': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
            }
        },
    })
