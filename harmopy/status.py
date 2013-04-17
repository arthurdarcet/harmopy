import flask
import json
import threading


class Status(threading.Thread):
    def run(self):
        self.app.run()

    def __init__(self, rsyncs):
        super(Status, self).__init__()
        self.daemon = True
        self.rsyncs = rsyncs

        self.app = flask.Flask(__name__)

        @self.app.route('/status')
        def status():
            return json.dumps(self.rsyncs.status)
