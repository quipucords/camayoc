# coding=utf-8
"""Unit tests for :mod:`camayoc.api`."""
import unittest
from unittest import mock
from unittest.mock import MagicMock

import yaml

from camayoc import config, exceptions, api
from camayoc.utils import uuid4
from camayoc.qcs_models import (
    Credential,
    Source,
)


CAMAYOC_CONFIG = """
qcs:
    hostname: example.com
    https: false
    username: admin
    password: pass
"""

INVALID_HOST_CONFIG = """
qcs:
    port: 8000
    https: true
"""

MOCK_CREDENTIAL = {
    'id': 34,
    'name': '91311585-77b3-4352-a277-cf9507a04ffc',
    'password': '********',
    'ssh_keyfile': None,
    'sudo_password': None,
    'cred_type': 'network',
    'username': '6c71666b-df97-4d50-91bd-10003569e843'
}

MOCK_SOURCE = {
    'credentials': [{'id': 34,
                     'name': '91311585-77b3-4352-a277-cf9507a04ffc'
                     }],
    'hosts': ['localhost'],
    'id': 25,
    'source_type': 'network',
    'name': 'e193081c-2423-4407-b9e2-05d20b6443dc',
    'port': 22
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
            client = api.Client(authenticate=False)
            self.assertEqual(client.url, 'http://example.com/api/v1/')

    def test_create_no_config(self):
        """If a base url is specified we use it."""
        with mock.patch.object(config, '_CONFIG', {}):
            self.assertEqual(config.get_config(), {})
            other_host = 'http://hostname.com'
            client = api.Client(url=other_host, authenticate=False)
            self.assertNotEqual('http://example.com/api/v1/', client.url)
            self.assertEqual(other_host, client.url)

    def test_create_override_config(self):
        """If a base url is specified, we use that instead of config file."""
        with mock.patch.object(config, '_CONFIG', self.config):
            other_host = 'http://hostname.com'
            client = api.Client(url=other_host, authenticate=False)
            cfg_host = self.config['qcs']['hostname']
            self.assertNotEqual(cfg_host, client.url)
            self.assertEqual(other_host, client.url)

    def test_negative_create(self):
        """Raise an error if no config entry is found and no url specified."""
        with mock.patch.object(config, '_CONFIG', {}):
            self.assertEqual(config.get_config(), {})
            with self.assertRaises(exceptions.QCSBaseUrlNotFound):
                api.Client(authenticate=False)

    def test_invalid_hostname(self):
        """Raise an error if no config entry is found and no url specified."""
        with mock.patch.object(config, '_CONFIG', self.invalid_config):
            self.assertEqual(config.get_config(), self.invalid_config)
            with self.assertRaises(exceptions.QCSBaseUrlNotFound):
                api.Client(authenticate=False)

    def test_login(self):
        """Test that when a client is created, it logs in just once."""
        with mock.patch.object(config, '_CONFIG', self.config):
            self.assertEqual(config.get_config(), self.config)
            client = api.Client
            client.login = MagicMock()
            cl = client()
            assert client.login.call_count == 1
            cl.token = uuid4()
            assert cl.default_headers() != {}

    def test_logout(self):
        """Test that when we log out, all credentials are cleared."""
        with mock.patch.object(config, '_CONFIG', self.config):
            self.assertEqual(config.get_config(), self.config)
            client = api.Client
            client.login = MagicMock()
            cl = client()
            assert client.login.call_count == 1
            cl.token = uuid4()
            assert cl.default_headers() is not {}
            cl.logout()
            assert cl.token is None
            assert cl.default_headers() == {}


class CredentialTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    @classmethod
    def setUpClass(cls):
        """Create a parsed configuraton dictionary."""
        cls.config = yaml.load(CAMAYOC_CONFIG)
        cls.invalid_config = yaml.load(INVALID_HOST_CONFIG)

    def test_equivalent(self):
        """If a hostname is specified in the config file, we use it."""
        with mock.patch.object(config, '_CONFIG', self.config):
            client = api.Client(authenticate=False)
            h = Credential(
                cred_type='network',
                username=MOCK_CREDENTIAL['username'],
                name=MOCK_CREDENTIAL['name'],
                client=client,
            )
            h._id = MOCK_CREDENTIAL['id']
            self.assertTrue(h.equivalent(MOCK_CREDENTIAL))
            self.assertTrue(h.equivalent(h))
            with self.assertRaises(TypeError):
                h.equivalent([])


class SourceTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    @classmethod
    def setUpClass(cls):
        """Create a parsed configuraton dictionary."""
        cls.config = yaml.load(CAMAYOC_CONFIG)
        cls.invalid_config = yaml.load(INVALID_HOST_CONFIG)

    def test_equivalent(self):
        """If a hostname is specified in the config file, we use it."""
        with mock.patch.object(config, '_CONFIG', self.config):
            client = api.Client(authenticate=False)
            p = Source(
                source_type='network',
                name=MOCK_SOURCE['name'],
                hosts=MOCK_SOURCE['hosts'],
                credential_ids=[MOCK_SOURCE['credentials'][0]['id']],
                client=client
            )
            p._id = MOCK_SOURCE['id']
            self.assertTrue(p.equivalent(MOCK_SOURCE))
            self.assertTrue(p.equivalent(p))
            with self.assertRaises(TypeError):
                p.equivalent([])
