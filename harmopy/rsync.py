from datetime import datetime
import itertools
import logging
import sh


class Rsync(object):
    def __init__(self, source, dest, rsync_args='', user=None):
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
            'speed': 42,
            'file': 'blah',
            'done': '42%',
        }

    def __str__(self):
        return '<({})Rsync {} {} -> {}>'.format(self.user, *self.args)


class RsyncManager(object):
    def __init__(self, targets, history_length):
        self.targets = itertools.cycle(targets)
        self.history_length = history_length
        self.current = None

    def start(self):
        target = next(self.targets)
        self.max_runtime = int(target.pop('max_runtime', -1))
        self.should_run = eval(target.pop('should_run', 'lambda w,h,m: True'))
        self.current = Rsync(**target)
        self.start_time = datetime.now()
        self.current.start()

    def stop(self):
        if self.current is None:
            return
        self.current.stop()
        if self.current.exit_code == -15:
            logging.info('Interrupted unfinished transfer %s', self.current)
        elif self.current.exit_code > 0:
            logging.warn('Transfer %s failed with exit code %d', self.current, self.current.exit_code)
        self.current = None

    def tick(self):
        now = datetime.now()
        should_run = self.should_run(now.weekday(), now.hour, now.minute)
        if self.current is not None and (not should_run or self._ran_too_long()):
            self.stop()
        if (self.current is None or self.current.done) and should_run:
            self.start()
        while now - self.history[0]['time'] > self.history_length:
            del(self.history[0])
        if self.current is not None
            self.history.append({'time': now, 'status': self.status})

    @property
    def status(self):
        self.tick()
        if self.current is None:
            return {'running': False}
        return dict(self.current.status, running=True)

    def _ran_too_long(self):
        return self.max_runtime > 0 and (datetime.now() - self.start_time).total_seconds() >= self.max_runtime
