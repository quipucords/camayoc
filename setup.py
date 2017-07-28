#!/usr/bin/env python3
# coding=utf-8
"""A setuptools-based script for installing camayoc."""
import os
from setuptools import setup

_project_root = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(_project_root, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='camayoc',
    author='Quipucords Team',
    author_email='quipucords@redhat.com',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Quality Assurance'
    ],
    description=(
        'A GPL-licensed Python library that facilitates functional testing of '
        'quipucords.'
    ),
    include_package_data=True,
    license='GPLv3',
    long_description=long_description,
    package_data={'': ['LICENSE']},
    url='https://github.com/quipucords/camayoc',
)
