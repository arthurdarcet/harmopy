import datetime
import logging

from .. import logs
from . import utils


logger = logging.getLogger(__name__)

class Page:
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

    @utils.json_exposed
    def status(self):
        return dict(
            id='status',
            time=datetime.datetime.now().timestamp(),
            **self._rsyncs.status
        )

    @utils.json_exposed
    def history(self, debug=False):
        if debug:
            return self._rsyncs.history
        return [{
            'speed': h['status'].get('speed', 0),
            'time': h['time'],
        } for h in self._rsyncs.history]

    @utils.json_exposed
    def logs(self):
        return logs.get()

    @utils.json_exposed
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

    @utils.json_exposed
    def files(self, **kwargs):
        if 'config_key' in kwargs:
            return self._config_save(kwargs)
        return [dict(section.items(), id=title, editable=self._config['status']['allow_conf_edit'])
            for title, section in self._config.files + [('DEFAULT', self._config['DEFAULT'])]]

    @utils.json_exposed
    def delete(self, file_id):
        logger.info('Deleting file section %r', file_id)
        self._config.remove_section(file_id)
        self._config.save()
        return {
            'status': 200,
            'id': file_id,
        }

    @utils.json_exposed
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
