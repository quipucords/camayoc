#!/usr/bin/env python3
# coding=utf-8
"""A setuptools-based script for installing camayoc."""
import os

from setuptools import find_packages
from setuptools import setup

_project_root = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(_project_root, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="camayoc",
    author="Quipucords Team",
    author_email="quipucords@redhat.com",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
    ],
    description=(
        "A GPL-licensed Python library that facilitates functional testing of Quipucords."
    ),
    extras_require={
        "dev": [
            # For `make docs`
            "sphinx",
            "jinja2==3.0.3",
            # For `make docs-serve`
            "sphinx-serve",
            # For `make lint`
            "flake8",
            "flake8-docstrings",
            "flake8-import-order",
            "flake8-quotes",
            # For `make package`
            "wheel",
            # For `make package-upload`
            "twine",
            # pydocstyle specific version till bug fixed
            # See here: https://gitlab.com/pycqa/flake8-docstrings/issues/36
            "pydocstyle==3.0.0",
            # For `make test-coverage`
            "pytest-cov",
            # For `make validate-docstrings`
            "testimony",
            # For `make pre-commit`
            "pre-commit",
            "black",
        ]
    },
    python_requires=">=3.9",
    install_requires=[
        "oc",
        "pexpect",
        "plumbum",
        "pytest>=3.6",
        "pyvmomi",
        "pyxdg",
        "pyyaml",
        "widgetastic.core",
        "widgetastic.patternfly",
    ],
    license="GPLv3",
    long_description=long_description,
    packages=find_packages(include=["camayoc*"]),
    url="https://github.com/quipucords/camayoc",
)
