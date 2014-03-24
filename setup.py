#!/usr/bin/env python
# =============================================================================
# @file   setup.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   23.03.2014
# =============================================================================
"""Installer for pythonhtpc."""

from distutils.core import setup

setup(
    name='PythonHTPC',
    version='0.1.0',
    author='Albert Puig',
    author_email='djkarras@gmail.com',
    packages=['pythonhtpc',],
    license='LICENSE.txt',
    description='Library for managing an HTPC from Python.',
    #long_description=open('README.txt').read(),
    install_requires=[
        "pebble >= 1.0.0",
        "APScheduler >= 2.1.2",
        "symmetricjsonrpc >= 0.1.0",
        "validictory >= 0.9.3"
    ],
)

# EOF
