#!/usr/bin/env python
# coding: utf-8

import setuptools


setuptools.setup(
    name='harmopy',
    version='0.1',
    author='Arthur Darcet',
    author_email='arthur@darcet.fr',
    description="A file synchronisation deamon controlled by a web interface.",
    license='MIT',
    keywords=['file', 'synchronisation', 'daemon', 'webui'],
    url='http://github.com/arthurdarcet/harmopy',
    download_url='http://pypi.python.org/pypi/harmopy/',
    packages=['harmopy'],
    package_data={'harmopy': ['static/*']},
    install_requires=[
        'cherrypy>=3.2',
        'distribute',
        'sh',
    ],
    scripts=[
        'bin/harmopy',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
    ],
    test_suite='harmopy.tests',
    include_package_data=True,
)
