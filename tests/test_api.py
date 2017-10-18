# coding=utf-8
"""Unit tests for :mod:`camayoc.api`."""
import unittest
from unittest import mock

import yaml

from camayoc import config, exceptions, api
from camayoc.qcs_models import (
    HostCredential,
    NetworkProfile,
)


CAMAYOC_CONFIG = """
qcs:
    hostname: 'http://example.com'
"""

INVALID_HOST_CONFIG = """
qcs:
    hostname: 'example.com'
"""

MOCK_CREDENTIAL = {
    'id': 34,
    'name': '91311585-77b3-4352-a277-cf9507a04ffc',
    'password': '********',
    'ssh_keyfile': None,
    'sudo_password': None,
    'username': '6c71666b-df97-4d50-91bd-10003569e843'
}

MOCK_PROFILE = {
    'credentials': [{'id': 34,
                     'name': '91311585-77b3-4352-a277-cf9507a04ffc'
                     }],
    'hosts': ['localhost'],
    'id': 25,
    'name': 'e193081c-2423-4407-b9e2-05d20b6443dc',
    'ssh_port': 22
}


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
            client = api.Client()
            cfg_host = self.config['qcs']['hostname']
            self.assertEqual(cfg_host, client.url.strip('api/v1/'))

    def test_create_no_config(self):
        """If a base url is specified we use it."""
        with mock.patch.object(config, '_CONFIG', {}):
            self.assertEqual(config.get_config(), {})
            other_host = 'http://hostname.com'
            client = api.Client(url=other_host)
            cfg_host = self.config['qcs']['hostname']
            self.assertNotEqual(cfg_host, client.url.strip('/api/v1/'))
            self.assertEqual(other_host, client.url.strip('/api/v1/'))

    def test_create_override_config(self):
        """If a base url is specified, we use that instead of config file."""
        with mock.patch.object(config, '_CONFIG', self.config):
            other_host = 'http://hostname.com'
            client = api.Client(url=other_host)
            cfg_host = self.config['qcs']['hostname']
            self.assertNotEqual(cfg_host, client.url.strip('/api/v1/'))
            self.assertEqual(other_host, client.url.strip('/api/v1/'))

    def test_negative_create(self):
        """Raise an error if no config entry is found and no url specified."""
        with mock.patch.object(config, '_CONFIG', {}):
            self.assertEqual(config.get_config(), {})
            with self.assertRaises(exceptions.QCSBaseUrlNotFound):
                api.Client()

    def test_invalid_hostname(self):
        """Raise an error if no config entry is found and no url specified."""
        with mock.patch.object(config, '_CONFIG', self.invalid_config):
            self.assertEqual(config.get_config(), self.invalid_config)
            with self.assertRaises(exceptions.QCSBaseUrlNotFound):
                api.Client()


class HostCredentialTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    @classmethod
    def setUpClass(cls):
        """Create a parsed configuraton dictionary."""
        cls.config = yaml.load(CAMAYOC_CONFIG)
        cls.invalid_config = yaml.load(INVALID_HOST_CONFIG)

    def test_equivalent(self):
        """If a hostname is specified in the config file, we use it."""
        with mock.patch.object(config, '_CONFIG', self.config):
            h = HostCredential(
                username=MOCK_CREDENTIAL['username'],
                name=MOCK_CREDENTIAL['name']
            )
            h._id = MOCK_CREDENTIAL['id']
            self.assertTrue(h.equivalent(MOCK_CREDENTIAL))
            self.assertTrue(h.equivalent(h))
            with self.assertRaises(TypeError):
                h.equivalent([])


class NetworkProfileTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    @classmethod
    def setUpClass(cls):
        """Create a parsed configuraton dictionary."""
        cls.config = yaml.load(CAMAYOC_CONFIG)
        cls.invalid_config = yaml.load(INVALID_HOST_CONFIG)

    def test_equivalent(self):
        """If a hostname is specified in the config file, we use it."""
        with mock.patch.object(config, '_CONFIG', self.config):
            p = NetworkProfile(
                name=MOCK_PROFILE['name'],
                hosts=MOCK_PROFILE['hosts'],
                credential_ids=[MOCK_PROFILE['credentials'][0]['id']]
            )
            p._id = MOCK_PROFILE['id']
            self.assertTrue(p.equivalent(MOCK_PROFILE))
            self.assertTrue(p.equivalent(p))
            with self.assertRaises(TypeError):
                p.equivalent([])
