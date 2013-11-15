#!/usr/bin/env python

from os.path import exists
from setuptools import setup, find_packages

from xylem import __version__

setup(
    name='xylem',
    version=__version__,
    # Your name & email here
    author='CarbonCulture',
    author_email='steve.pike@carbonculture.net',
    # If you had xylem.tests, you would also include that in this list
    packages=find_packages(),
    # Any executable scripts, typically in 'bin'. E.g 'bin/do-something.py'
    scripts=[],
    # REQUIRED: Your project's URL
    url='',
    # Put your license here. See LICENSE.txt for more information
    license='',
    # Put a nice one-liner description here
    description='Xylem is CarbonCulture\'s data API client library',
    long_description=open('README.rst').read() if exists("README.rst") else "",
    # Any requirements here, e.g. "Django >= 1.1.1"
    install_requires=[
        'requests == 2.0.1',
    ],
)
