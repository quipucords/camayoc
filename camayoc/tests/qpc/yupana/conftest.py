"""Test utilities for quipucords' ``yupana`` tests."""

import pytest

import requests


from camayoc.config import get_config
from camayoc.exceptions import ConfigFileNotFoundError, WaitTimeError


# def yupana_configs():
#     """Return all of the yupana config values"""
#     try:
#         yupana_configs = get_config.get("yupana", [])
#     except ConfigFileNotFoundError:
#         yupana_configs = []
#     print("Yupana configs: " + str(yupana_configs))


# @pytest fixture(scope="session")
# def upload_data():
#     """Send a package up to yupana."""
#     pass
