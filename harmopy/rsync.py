from datetime import datetime
import itertools
import sh


class Rsync(object):
    def __init__(self, args, user=None):
        self.running = False
        self.args = args
        self.user = user

    def start(self):
        if self.running:
            return
        self._cmd = sh.rsync(*self.args, _bg=True)
        self.running = True

    def stop(self):
        if not self.running:
            return
        self._cmd.terminate()
        self.running = False

    @property
    def status(self):
        return {
            'speed': 42,
            'file': 'blah',
            'done': '42%',
        }


class RsyncManager(object):
    def __init__(self, targets):
        # A target is of the form ((*rsync_args), max_runtime=None, user=None)
        self.targets = itertools.cycle(targets)
        self.current = None
        self.start_time = None
        self.max_runtime = None

    def start(self):
        target = next(self.targets)
        rsync_args = targets[0]
        user = max_runtime = None
        if len(target) >= 3:
            user = target[2]
        if len(target) >= 2:
            self.max_runtime = target[1]
        self.current = Rsync(rsync_args, user)
        self.start_time = datetime.now()
        self.current.start()

    def stop(self):
        self.current.stop()
        self.start_time = None
        self.current = None
        self.max_runtime = None

    def tick(self):
        if self.current is None:
            return
        if datetime.now() - self.start_time >= self.max_runtime:
            self.stop()

    @property
    def status(self):
        if self.current is None:
            return {}
        return self.current.status
