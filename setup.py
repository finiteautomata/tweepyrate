#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Tweepyrate',
    version='0.1.1',
    description='Python library to scrap huge amount of tweets',
    author='Juan Manuel Pérez',
    author_email='jmperez@dc.uba.ar',
    packages=['tweepyrate'],
    install_requires=[
        'markdown',
    ],
)
