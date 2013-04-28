import copy
import datetime
import itertools
import logging
import re
import sh
import threading


logger = logging.getLogger(__name__)

class Rsync(threading.Thread):
    STATUS_LINE = re.compile(r'^ +(?P<done_bits>[0-9]+) +(?P<current_done>[0-9]{1,3})% +(?P<speed>[.0-9]+)(?P<speed_unit>.?)B/s +(?P<current_eta>[0-9:]+)$')
    FILE_DONE_LINE = re.compile(r'^ +(?P<done_bits>[0-9]+) +(?P<current_done>100)% +(?P<speed>[.0-9]+)(?P<speed_unit>.?)B/s +(?P<time_taken>[0-9:]+) +\(xfer#(?P<current_id>[0-9]+), to-check=[0-9]+/(?P<num_file>[0-9]+)\)$')
    START_LINE = 'receiving incremental file list'
    IGNORE_LINE = [re.compile(r'^total size is [0-9]+ speedup is [.0-9]+')]

    def __init__(self, source, dest, rsync_args='', user=None, **_):
        super().__init__()
        self.user = user
        self.args = (rsync_args, source, dest)
        if user is not None:
            self.rsync = sh.sudo.bake('-u', user, 'rsync')
        else:
            self.rsync = sh.rsync
        self.rsync = self.rsync.bake(source, dest, *rsync_args.split())
        self.daemon = True
        self.running = threading.Event()
        self._buffer = ''
        self._status = {
            'running': False,
            'source': source,
            'dest': dest,
        }
        self._status_lock = threading.RLock

    def run(self):
        self._cmd = self.rsync(progress=True, _out_bufsize=0, _out=self._buffer_output)

    def _parse_stdout(self, line):
        logger.debug('Got line from rsync: %r', line)
        def update_status(d):
            logger.debug('Parsed it as %r', d)
            if d['speed'] != '0':
                d['speed'] = float(d['speed'])
                if d['speed_unit'] == 'M' or d['speed_unit'] == 'G':
                    d['speed'] *= 1000
                if d['speed_unit'] == 'G':
                    d['speed'] *= 1000
                if d['speed_unit'] == '':
                    d['speed'] /= 1000
                with self._status_lock():
                    self._status.update(d)

        if not self._status['running']:
            if line == self.START_LINE:
                with self._status_lock():
                    self._status['running'] = True
            return

        m1 = self.STATUS_LINE.match(line)
        if m1 is not None:
            return update_status(m1.groupdict())

        m2 = self.FILE_DONE_LINE.match(line)
        if m2 is not None:
            d = m2.groupdict()
            d['done'] = int(int(d['current_id'])/int(d['num_file']))
            return update_status(d)

        for ign in self.IGNORE_LINE:
            if ign.match(line):
                logger.debug('Ignored')
                return

        logger.debug('Parsed it as a file line')
        with self._status_lock():
            self._status['current_file'] = line

    def _parse_stderr(self, line):
        logger.warn('Rsync error %r', line)
        with self._status_lock():
            self._status.update({
                'running': False,
                'error': line,
            })

    def _buffer_output(self, char):
        if char == '\r' or char == '\n':
            self._parse_stdout(self._buffer)
            self._buffer = ''
        else:
            self._buffer += char

    def start(self):
        if self.running.is_set():
            return
        self.running.set()
        super().start()

    def stop(self):
        if not self.running.is_set():
            return
        self.running.clear()
        if self.done:
            return
        self._cmd.terminate()

    @property
    def status(self):
        with self._status_lock():
            return copy.copy(self._status)

    @property
    def done(self):
        if not self.running.is_set():
            return False
        return not self._cmd.process.alive

    @property
    def exit_code(self):
        if not self.running.is_set():
            return 0
        return self._cmd.exit_code

    def __str__(self):
        res = 'Rsync {} {} -> {}'.format(*self.args)
        if self.user is not None:
            res = '(su {}) '.format(self.user) + res
        if self.running.is_set() and self.done:
            res = res + ' [done {}]'.format(self.exit_code)
        return '<' + res + '>'


class RsyncManager(object):
    def __init__(self, targets, history_length):
        self.files = [dict(target, id=i, last_synced=None) for i, target in targets]
        self.targets = itertools.cycle(self.files)
        self.history_length = history_length
        self.history = []
        self.current = None

    def prepare(self):
        target = next(self.targets)
        self.max_runtime = target.get('max_runtime', None)
        self.should_run = target.get('should_run', lambda *_: True)
        self.current = Rsync(**target)
        logger.info('Prepared job %s', self.current)

    def stop(self):
        logger.info('Stopping transfer %s', self.current)
        self.current.stop()
        if self.current.exit_code == -15:
            logger.info('Interrupted unfinished transfer %s', self.current)
        elif self.current.exit_code > 0:
            logger.warn('Transfer %s failed with exit code %d', self.current, self.current.exit_code)
        self.start_time = None
        self.current = None

    def tick(self):
        logger.info('Tick %s', self)
        if self.current is None or self.current.done:
            self.prepare()

        if not self._should_run():
            self.stop()
        elif self._ran_too_long():
            self.stop()
            return self.tick()
        else:
            self.current.start()

        now = datetime.datetime.now().timestamp()
        while len(self.history) > 0 and now - self.history[0]['time'] > self.history_length:
            del(self.history[0])
        if self.current is not None:
            self.history.append({'time': int(now), 'status': self.status})

    @property
    def status(self):
        if self.current is None:
            return {'running': False}
        return self.current.status

    def __getitem__(self, file_id):
        for target in self.files:
            if target['id'] == file_id:
                return target
        raise KeyError('No such file_id')

    def expand(self, file_id):
        raise NotImplementedError('TODO')
        return [self[file_id]]

    def _ran_too_long(self):
        return self.max_runtime is not None and \
            (datetime.datetime.now() - self.start_time).total_seconds() >= self.max_runtime

    def _should_run(self):
        now = datetime.datetime.now()
        return self.should_run(now.weekday(), now.hour, now.minute)

    def __str__(self):
        return '<RsyncManager {} {}kB/s>'.format(self.current, self.status.get('speed', 0))
