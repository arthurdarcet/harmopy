import cherrypy
import copy
import datetime
import itertools
import logging
import os
import re
import sh
import sys
import threading


logger = logging.getLogger(__name__)

class Rsync(threading.Thread):
    STATUS_LINE = re.compile(r'^(?P<done_bits>[0-9,]+) +(?P<current_done>[0-9]{1,3})% +(?P<speed>[.0-9]+)(?P<speed_unit>.?)B/s +(?P<current_eta>[0-9:]+)$')
    FILE_DONE_LINE = re.compile(r'^(?P<done_bits>[0-9,]+) +(?P<current_done>100)% +(?P<speed>[.0-9]+)(?P<speed_unit>.?)B/s +(?P<time_taken>[0-9:]+) +\(xfe?r#(?P<current_id>[0-9]+), (?:ir|to)-ch(?:ec)?k=[0-9]+/(?P<num_file>[0-9]+)\)$')
    START_LINE = 'receiving incremental file list'
    IGNORE_LINE = [re.compile(r'^total size is [0-9]+ speedup is [.0-9]+')]

    SPEED_UNITS_TO_KB = {
        'T': 1e9,
        'G': 1e6,
        'M': 1e3,
        'k': 1,
        '': 1e-3,
    }

    def __init__(self, source, dest, rsync_args='', user=None, **_):
        super().__init__()
        self.user = user
        self.args = (rsync_args, source, dest)

        dest_dir = os.path.split(dest)[0]
        if not os.path.isdir(dest_dir):
            if os.path.exists(dest_dir):
                logger.critical('Destination %s isn\'t valid because a file exists at %s', dest, dest_dir)
                sys.exit(1)
            sh.mkdir('-p', dest_dir)
            if user is not None:
                sh.chown('{}:'.format(user), dest_dir)

        if user is not None:
            self.rsync = sh.sudo.bake('-u', user, 'rsync')
        else:
            self.rsync = sh.rsync
        self.rsync = self.rsync.bake(source, dest, '--no-h', *rsync_args.split(), progress=True)
        self.daemon = True
        self.running = threading.Event()
        self._buffer = ''
        self._status = {
            'running': False,
            'source': source,
            'dest': dest,
        }
        self._status_lock = threading.Lock()

    def run(self):
        self._cmd = self.rsync(_out_bufsize=0, _out=self._buffer_output)

    def _parse_stdout(self, line):
        logger.debug('Got line from rsync: %r', line)
        def update_status(d):
            logger.debug('Parsed it as %r', d)
            if d['speed'] != '0':
                d['speed'] = float(d['speed']) * self.SPEED_UNITS_TO_KB[d['speed_unit']]
                with self._status_lock:
                    self._status.update(d)

        if not self._status['running']:
            if line == self.START_LINE:
                with self._status_lock:
                    self._status['running'] = True
            return

        line = line.strip(' ')

        if line == '':
            return

        m1 = self.STATUS_LINE.match(line)
        if m1 is not None:
            return update_status(m1.groupdict())

        m2 = self.FILE_DONE_LINE.match(line)
        if m2 is not None:
            d = m2.groupdict()
            d['done'] = int(d['current_id'])/int(d['num_file'])
            return update_status(d)

        for ign in self.IGNORE_LINE:
            if ign.match(line):
                logger.debug('Ignored')
                return

        logger.debug('Parsed it as a file line')
        with self._status_lock:
            self._status['current_file'] = line

    def _parse_stderr(self, line):
        logger.warn('Rsync error %r', line)
        with self._status_lock:
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
            return False
        self.running.clear()
        if not self.done:
            self._cmd.terminate()
        return True

    @property
    def status(self):
        with self._status_lock:
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
    LISTING_LINE = re.compile(r'^(?P<directory>d|-)[rwx-]{9} +(?P<size>[0-9]+) [0-9/]+ [0-9:]+ (?P<file>.*)$')

    def __init__(self, config):
        self.working = threading.Lock()
        self.current = None
        self.stop_until = None
        self.init(config)

    def init(self, config):
        with self.working:
            self._stop()
            self._config = config
            self.start_time = None
            self.files = [dict(target, id=i, last_synced=None) for i, target in config.files]
            self.targets = itertools.cycle(self.files)
            self.history_length = config['general']['history_length']
            self.history = []

    def prepare(self):
        target = next(self.targets)
        self.max_runtime = target.get('max_runtime', None)
        self.should_run = target.get('should_run', lambda *_: True)
        self.current = Rsync(**target)
        self.start_time = None
        logger.debug('Prepared job %s', self.current)

    def _stop(self):
        if self.current is None:
            return
        if self.current.stop():
            logger.info('Stopped transfer %s', self.current)
        if self.current.exit_code == -15:
            logger.info('Interrupted unfinished transfer %s', self.current)
        elif self.current.exit_code > 0:
            logger.warn('Transfer %s failed with exit code %d', self.current, self.current.exit_code)
        self.start_time = None
        self.current = None

    def tick(self):
        if not self.working.acquire(False):
            return
        logger.debug('Tick %s', self)
        if self.current is None:
            self.prepare()
        elif self.current.done:
            logger.info('Finnished transfer %s', self.current)
            self.prepare()

        if not self._should_run():
            self._stop()
        elif self._ran_too_long():
            self._stop()
            self.working.release()
            return self.tick()
        elif self.start_time is None:
            logger.info('Started transfer %s', self.current)
            self.current.start()
            self.start_time = datetime.datetime.now()

        now = datetime.datetime.now().timestamp()
        while len(self.history) > 0 and now - self.history[0]['time'] > self.history_length:
            del(self.history[0])
        if self.current is not None:
            self.history.append({'time': int(now), 'status': self.status})
        self.working.release()

    @property
    def status(self):
        if self.current is None:
            status = {'running': False}
        else:
            status = self.current.status

        if self.stop_until is not None:
            status['stopped_until'] = str(self.stop_until)
        return status

    def expand(self, file_id, path=''):
        logger.info('Expanding %s', file_id)
        if path:
            path += '/'
        with self.working:
            self._stop()
            conf = self._config[file_id]
            try:
                out = sh.rsync('--no-motd', '--no-h', conf['source'] + '/' + path + '/').split('\n')
            except sh.ErrorReturnCode_23:
                raise cherrypy.HTTPError(400, 'The path {!r} in the rsync target {} is not a directory'.format(path, file_id))

            files = []
            for line in out:
                line = line.strip(' ')
                if line is '':
                    continue
                match = self.LISTING_LINE.match(line)
                if match is None:
                    logger.critical('Error parsing rsync listing (line %r)', line)
                else:
                    data = match.groupdict()
                    if data['file'] != '.':
                        files.append((data['directory'] == 'd', data['file']))

            logger.info('Retrieved a list of %d files', len(files))
            return files

    def _ran_too_long(self):
        return self.max_runtime is not None and self.start_time is not None and \
            (datetime.datetime.now() - self.start_time).total_seconds() >= self.max_runtime

    def _should_run(self):
        if self.stop_until is not None:
            if self.stop_until < datetime.datetime.now():
                self.stop_until = None
            else:
                return False
        now = datetime.datetime.now()
        return self.should_run(now.weekday(), now.hour, now.minute)

    def __str__(self):
        return '<RsyncManager {} {}kB/s>'.format(self.current, self.status.get('speed', 0))
