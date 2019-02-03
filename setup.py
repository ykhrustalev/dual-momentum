#!/usr/bin/env python
import os

from setuptools import find_packages
from setuptools import setup

version = os.getenv('VERSION') or '0.0.0'

setup(
    name='dual-momentum',
    version='0.1.0',
    packages=['dm'],
    entry_points={
        'console_scripts': [
            'dm = dm.main:main',
        ]
    },
)
