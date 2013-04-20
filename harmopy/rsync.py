from datetime import datetime
import itertools
import logging
import sh


logger = logging.getLogger(__name__)

class Rsync(object):
    def __init__(self, source, dest, rsync_args='', user=None, **_):
        self.running = False
        self.args = (rsync_args, source, dest)
        self.user = user

    def start(self):
        if self.running:
            return
        self._cmd = sh.rsync(*self.args, _bg=True)
        self.running = True

    def stop(self):
        self.running = False
        if not self.running or self.done:
            return
        self._cmd.terminate()

    @property
    def done(self):
        return self._cmd.process.alive

    @property
    def exit_code(self):
        return self._cmd.exit_code

    @property
    def status(self):
        return {
            'source': self.args[1],
            'destination': self.args[2],
            'speed': '442Ko/s',
            'done': 42,
            'eta': 2,
        }

    def __str__(self):
        return '<(su {}) Rsync {} {} -> {}>'.format(self.user, *self.args)


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
        logger.debug('Prepared job %s', self.current)

    def stop(self):
        self.current.stop()
        if self.current.exit_code == -15:
            logger.info('Interrupted unfinished transfer %s', self.current)
        elif self.current.exit_code > 0:
            logger.warn('Transfer %s failed with exit code %d', self.current, self.current.exit_code)
        self.start_time = None
        self.current = None

    def tick(self):
        now = datetime.now()
        if self.current is None or self.current.done:
            self.prepare()

        if not self._should_run():
            self.stop()
        elif self._ran_too_long():
            self.stop()
            return self.tick()
        else:
            self.current.start()

        while len(self.history) > 0 and (now - self.history[0]['time']).total_seconds() > self.history_length:
            del(self.history[0])
        if self.current is not None:
            self.history.append({'time': now, 'status': self.status})

    @property
    def status(self):
        if self.current is None:
            return {'running': False}
        return dict(self.current.status, running=True)

    def __getitem__(self, file_id):
        for target in self.files:
            if target['id'] == file_id:
                return target
        raise KeyError('No such file_id')

    def expand(self, file_id):
        raise NotImplementedError('TODO')
        return [self[file_id]]

    def _ran_too_long(self):
        return self.max_runtime is not None and (datetime.now() - self.start_time).total_seconds() >= self.max_runtime

    def _should_run(self):
        now = datetime.now()
        return self.should_run(now.weekday(), now.hour, now.minute)
