import configparser
import logging


logger = logging.getLogger(__name__)

class Config(configparser.ConfigParser):
    LAMBDA_TEXTS = {}
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        with open(filename, 'r') as f:
            self.read_file(f)
        self._main_sections = ('general', 'status')

    def __getitem__(self, item):
        if item in self._main_sections:
            except_keys = super().__getitem__('DEFAULT').keys()
        else:
            except_keys = set()
        return Section(super().__getitem__(item), except_keys)

    def save(self):
        with open(self.filename, 'w') as f:
            return self.write(f)

    def copy_section(self, source, dest):
        section = self[dest]
        defaults = self.defaults()
        for k,v in self[source].items():
            section.__setitem__(k, v, except_value=defaults.get(k, None))
        return section

    def move_section(self, source, dest):
        self.add_section(dest)
        if source in self:
            self.copy_section(source, dest)
            self.remove_section(source)

    @property
    def main_sections(self):
        return [(section, self[section]) for section in self._main_sections]

    @property
    def files(self):
        return [(section, self[section]) for section in self.sections()
            if section not in self._main_sections]


class Section(object):
    def __init__(self, section, except_keys=[]):
        self._section = section
        self.except_keys = set(except_keys)

    def __getitem__(self, item):
        if item in self.except_keys:
            raise KeyError
        try:
            res = eval(self._section[item])
            if hasattr(res, '__call__'):
                Config.LAMBDA_TEXTS[res] = self._section[item]
            return res
        except:
            return self._section[item]

    @staticmethod
    def _prepare_for_storage(value):
        if value is None or value == 'null' or (isinstance(value, str) and value.strip() == ''):
            value = 'None'
        if value == 'true':
            value = 'True'
        if value == 'false':
            value = 'False'
        if hasattr(value, '__call__'):
            value = Config.LAMBDA_TEXTS[value]
        return str(value)

    def __setitem__(self, item, value, except_value=None):
        value = self._prepare_for_storage(value)
        if value != except_value:
            self._section[item] = value

    def __getattr__(self, attr):
        return getattr(self._section, attr)

    def items(self):
        for key in self.keys():
            if key not in self.except_keys:
                yield (key, self[key])
