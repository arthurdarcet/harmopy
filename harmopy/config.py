import configparser

class Config(configparser.ConfigParser):
    def __init__(self, filename):
        super().__init__()
        with open(filename, 'r') as f:
            self.read_file(f)
        self._main_sections = ('general', 'status')

    def __getitem__(self, item):
        if item not in self._main_sections:
            return Section(super().__getitem__(item))
        else:
            # super() wouldn't work
            return Section(dict(
                (k,v) for k,v in super().__getitem__(item).items()
                if k not in super(Config, self).__getitem__('DEFAULT').keys()
            ))

    @property
    def main_sections(self):
        return [(section, self[section]) for section in self._main_sections]

    @property
    def files(self):
        return [(section, self[section]) for section in self.sections()
            if section not in self._main_sections]


class Section(object):
    def __init__(self, section):
        self._section = section

    def __getitem__(self, item, text_lambda=False):
        try:
            res = eval(self._section[item])
            if text_lambda and hasattr(res, '__call__'):
                raise Exception
            return res
        except:
            return self._section[item]

    def __setitem__(self, item, value):
        if value is None or value == 'null' or (isinstance(value, str) and value.strip() == ''):
            value = 'None'
        if value == 'true':
            value = 'True'
        if value == 'false':
            value = 'False'
        self._section[item] = str(value)

    def __getattr__(self, attr):
        return getattr(self._section, attr)

    def items(self, text_lambda=False):
        return [(k, self.__getitem__(k, text_lambda)) for k in self.keys()]
