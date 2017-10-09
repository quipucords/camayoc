# coding=utf-8
"""Unit tests for :mod:`camayoc.api`."""
import unittest
from unittest import mock

import yaml

from camayoc import config, exceptions, api

CAMAYOC_CONFIG = """
qcs:
    hostname: 'http://example.com'
"""

INVALID_HOST_CONFIG = """
qcs:
    hostname: 'example.com'
"""


class APIClientTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    @classmethod
    def setUpClass(cls):
        """Create a parsed configuraton dictionary."""
        cls.config = yaml.load(CAMAYOC_CONFIG)
        cls.invalid_config = yaml.load(INVALID_HOST_CONFIG)

    def test_create_with_config(self):
        """If a hostname is specified in the config file, we use it."""
        with mock.patch.object(config, '_CONFIG', self.config):
            self.assertEqual(config.get_config(), self.config)
            client = api.QCSClient()
            cfg_host = self.config['qcs']['hostname']
            self.assertEqual(cfg_host, client.url.strip('api/v1/'))

    def test_create_no_config(self):
        """If a base url is specified we use it."""
        with mock.patch.object(config, '_CONFIG', {}):
            self.assertEqual(config.get_config(), {})
            other_host = 'http://hostname.com'
            client = api.QCSClient(url=other_host)
            cfg_host = self.config['qcs']['hostname']
            self.assertNotEqual(cfg_host, client.url.strip('/api/v1/'))
            self.assertEqual(other_host, client.url.strip('/api/v1/'))

    def test_create_override_config(self):
        """If a base url is specified, we use that instead of config file."""
        with mock.patch.object(config, '_CONFIG', self.config):
            other_host = 'http://hostname.com'
            client = api.QCSClient(url=other_host)
            cfg_host = self.config['qcs']['hostname']
            self.assertNotEqual(cfg_host, client.url.strip('/api/v1/'))
            self.assertEqual(other_host, client.url.strip('/api/v1/'))

    def test_negative_create(self):
        """Raise an error if no config entry is found and no url specified."""
        with mock.patch.object(config, '_CONFIG', {}):
            self.assertEqual(config.get_config(), {})
            with self.assertRaises(exceptions.QCSBaseUrlNotFound):
                api.QCSClient()

    def test_invalid_hostname(self):
        """Raise an error if no config entry is found and no url specified."""
        with mock.patch.object(config, '_CONFIG', self.invalid_config):
            self.assertEqual(config.get_config(), self.invalid_config)
            with self.assertRaises(exceptions.QCSBaseUrlNotFound):
                api.QCSClient()
