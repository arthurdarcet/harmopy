[![Build Status](https://travis-ci.org/arthurdarcet/harmopy.png?branch=master)](https://travis-ci.org/arthurdarcet/harmopy)
Harmopy
============

File synchronization daemon.
 * Web interface for config tweaking and status report
 * Prioritization of the job queue with a `max_runtime` parameter: each job run for at most `max_runtime` seconds before leaving the bandwidth for another job. This can be disabled for high priority jobs.



Install
-------

Python 3 is required.

`python setup.py install` will install an executable script to `/usr/bin/harmopy`, a config file to `/etc/harmopy.conf` and a systemd service file.

`systemctl start harmopy.service` to start the daemon as `root` (you might want to run the daemon as a low privileges user for now if the web interface is at any risk of being accessible on the internet…).

With the default config, the web interface is at http://127.0.0.1:5000
