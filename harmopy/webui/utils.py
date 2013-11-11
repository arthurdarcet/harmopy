import cherrypy
import datetime
import functools
import json
import logging

from .. import config


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
        except cherrypy.HTTPError as e:
            value = {'status': e.code, 'error': e._message}
        except Exception as e:
            value = {'status': 500, 'error': str(e)}
            logger.exception('View error')
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(value, cls=JSONEncoder).encode('utf8')
    wrapper.exposed = True
    return wrapper
