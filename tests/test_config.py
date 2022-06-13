# coding=utf-8
"""Unit tests for :mod:`camayoc.config`."""
import os
import unittest
from unittest import mock

import xdg

import yaml

from camayoc import config, exceptions, utils


CAMAYOC_CONFIG = """
vcenter:
    hostname: example1.com
qpc:
    hostname: example2.com
    port: 8000
    https: false
"""


class GetConfigTestCase(unittest.TestCase):
    """Test :func:`camayoc.config.get_config`."""

    @classmethod
    def setUpClass(cls):
        """Create a parsed configuraton dictionary."""
        cls.config = yaml.load(CAMAYOC_CONFIG, Loader=yaml.FullLoader)

    def test_cache_full(self):
        """No config is read from disk if the cache is populated."""
        with mock.patch.object(config, "_CONFIG", self.config):
            with mock.patch("camayoc.config.yaml.load") as load:
                self.assertEqual(config.get_config(), self.config)
        self.assertEqual(load.call_count, 0)

    def test_cache_empty(self):
        """A config is read from disk if the cache is empty."""
        with mock.patch.object(config, "_CONFIG", None), mock.patch(
            "camayoc.config.yaml.load"
        ) as load, mock.patch("camayoc.config._get_config_file_path"):
            load.return_value = self.config
            self.assertEqual(config.get_config(), self.config)
        self.assertEqual(load.call_count, 1)


class GetConfigFilePathTestCase(unittest.TestCase):
    """Test ``camayoc.config._get_config_file_path``."""

    def test_success(self):
        """Assert the method returns a path when a config file is found."""
        with mock.patch.object(xdg.BaseDirectory, "load_config_paths") as lcp:
            lcp.return_value = ("an_iterable", "of_xdg", "config_paths")
            with mock.patch.object(os.path, "isfile") as isfile:
                isfile.return_value = True
                # pylint:disable=protected-access
                config._get_config_file_path(utils.uuid4(), utils.uuid4())
        self.assertGreater(isfile.call_count, 0)

    def test_failures(self):
        """Assert the  method raises an exception when no config is found."""
        with mock.patch.object(xdg.BaseDirectory, "load_config_paths") as lcp:
            lcp.return_value = ("an_iterable", "of_xdg", "config_paths")
            with mock.patch.object(os.path, "isfile") as isfile:
                isfile.return_value = False
                with self.assertRaises(exceptions.ConfigFileNotFoundError):
                    # pylint:disable=protected-access
                    config._get_config_file_path(utils.uuid4(), utils.uuid4())
        self.assertGreater(isfile.call_count, 0)
