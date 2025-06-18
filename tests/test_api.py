# coding=utf-8
"""Unit tests for :mod:`camayoc.api`."""

import json
import unittest
from unittest import mock
from unittest.mock import MagicMock
from urllib.parse import urljoin

import requests

from camayoc import api
from camayoc.qpc_models import Credential
from camayoc.qpc_models import Scan
from camayoc.qpc_models import ScanJob
from camayoc.qpc_models import Source
from camayoc.types.settings import QuipucordsServerOptions
from camayoc.utils import uuid4

CAMAYOC_CONFIG = QuipucordsServerOptions(
    hostname="example.com", https=False, username="admin", password="pass", ssh_keyfile_path="/tmp/"
)

MOCK_CREDENTIAL = {
    "id": 34,
    "name": "91311585-77b3-4352-a277-cf9507a04ffc",
    "password": "********",
    "ssh_key": None,
    "sudo_password": None,
    "cred_type": "network",
    "username": "6c71666b-df97-4d50-91bd-10003569e843",
}

MOCK_SOURCE = {
    "credentials": [{"id": 34, "name": "91311585-77b3-4352-a277-cf9507a04ffc"}],
    "hosts": ["localhost"],
    "id": 25,
    "source_type": "network",
    "name": "e193081c-2423-4407-b9e2-05d20b6443dc",
    "port": 22,
}

MOCK_SAT6_SOURCE = {
    "credentials": [{"id": 34, "name": "91311585-77b3-4352-a277-cf9507a04ffc"}],
    "hosts": ["example.com"],
    "id": 25,
    "source_type": "satellite",
    "name": "e193081c-2423-4407-b9e2-05d20b6443dc",
    "port": 443,
    "ssl_cert_verify": False,
}

MOCK_SCAN = {
    "id": 21,
    "name": "testscan",
    "options": {"max_concurrency": 50},
    "scan_type": "inspect",
    "sources": [{"id": 153, "name": "mock_source"}],
    "status": "created",
}


class APIClientTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    def test_create_with_config(self):
        """If a hostname is specified in the config file, we use it."""
        client = api.Client(authenticate=False, config=CAMAYOC_CONFIG)
        self.assertEqual(client.url, "http://example.com:8000/api/")

    def test_create_specific_url(self):
        """If a base url is specified we use it."""
        other_host = "http://hostname.com"
        client = api.Client(url=other_host, authenticate=False)
        self.assertNotEqual("http://example.com:8000/api/v1/", client.url)
        self.assertEqual(other_host, client.url)

    def test_login(self):
        """Test that when a client is created, it logs in just once."""
        client = api.Client
        client.login = MagicMock()
        cl = client(config=CAMAYOC_CONFIG)
        assert client.login.call_count == 1
        cl.token = uuid4()
        assert cl.default_headers() != {}

    def test_get_user(self):
        """Test that when a client is created, it logs in just once."""
        client = api.Client
        client.login = MagicMock()
        response = MagicMock(json=MagicMock(return_value={"username": "admin"}))
        client.request = MagicMock(return_value=response)
        cl = client(config=CAMAYOC_CONFIG)
        u = cl.get_user().json()["username"]
        assert u == CAMAYOC_CONFIG.username
        client.request.assert_called_once_with("GET", urljoin(cl.url, "v1/users/current/"))

    def test_logout(self):
        """Test that when we log out, all credentials are cleared."""
        client = api.Client
        client.login = MagicMock()
        cl = client(config=CAMAYOC_CONFIG)
        assert client.login.call_count == 1
        cl.token = uuid4()
        assert cl.default_headers() != {}
        client.request = MagicMock()
        cl.logout()
        assert client.request.call_count == 1
        assert cl.token is None
        assert cl.default_headers() == {}

    def test_response_handler(self):
        """Test that when we get a 4xx or 5xx response, an error is raised."""
        client = api.Client(authenticate=False, config=CAMAYOC_CONFIG)
        mock_request = mock.Mock(
            body='{"Test Body"}',
            path_url="/example/path/",
            headers='{"Test Header"}',
            text="Some text",
        )
        mock_response = mock.Mock(status_code=404)
        mock_response.request = mock_request
        mock_response.json = MagicMock(
            return_value=json.dumps('{"The resource you requested was not found"}')
        )
        with self.subTest(msg="Test code handler"):
            client.response_handler = api.code_handler
            with self.assertRaises(requests.exceptions.HTTPError):
                client.response_handler(mock_response)

        with self.subTest(msg="Test json handler"):
            client.response_handler = api.json_handler
            with self.assertRaises(requests.exceptions.HTTPError):
                client.response_handler(mock_response)

        with self.subTest(msg="Test echo handler"):
            client.response_handler = api.echo_handler
            # no error should be raised with the echo handler
            client.response_handler(mock_response)

        # not all responses have valid json
        mock_response.json = MagicMock(return_value="Not valid json")

        with self.subTest(msg="Test code handler without json available"):
            client.response_handler = api.code_handler
            with self.assertRaises(requests.exceptions.HTTPError):
                client.response_handler(mock_response)

        with self.subTest(msg="Test json handler without json available"):
            client.response_handler = api.json_handler
            with self.assertRaises(requests.exceptions.HTTPError):
                client.response_handler(mock_response)

        with self.subTest(msg="Test echo handler without json available"):
            client.response_handler = api.echo_handler
            # no error should be raised with the echo handler
            client.response_handler(mock_response)


class CredentialTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    def test_equivalent(self):
        """If a hostname is specified in the config file, we use it."""
        client = api.Client(authenticate=False, config=CAMAYOC_CONFIG)
        h = Credential(
            cred_type="network",
            username=MOCK_CREDENTIAL["username"],
            name=MOCK_CREDENTIAL["name"],
            client=client,
        )
        h._id = MOCK_CREDENTIAL["id"]
        self.assertTrue(h.equivalent(MOCK_CREDENTIAL))
        self.assertTrue(h.equivalent(h))
        with self.assertRaises(TypeError):
            h.equivalent([])


class SourceTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    def test_equivalent_network(self):
        """If a hostname is specified in the config file, we use it."""
        client = api.Client(authenticate=False, config=CAMAYOC_CONFIG)
        src = Source(
            source_type="network",
            name=MOCK_SOURCE["name"],
            hosts=MOCK_SOURCE["hosts"],
            credential_ids=[MOCK_SOURCE["credentials"][0]["id"]],
            client=client,
        )
        src._id = MOCK_SOURCE["id"]
        self.assertTrue(src.equivalent(MOCK_SOURCE))
        self.assertTrue(src.equivalent(src))
        with self.assertRaises(TypeError):
            src.equivalent([])

    def test_equivalent_satellite(self):
        """If a hostname is specified in the config file, we use it."""
        client = api.Client(authenticate=False, config=CAMAYOC_CONFIG)
        p = Source(
            source_type="satellite",
            name=MOCK_SAT6_SOURCE["name"],
            hosts=MOCK_SAT6_SOURCE["hosts"],
            credential_ids=[MOCK_SAT6_SOURCE["credentials"][0]["id"]],
            options={"ssl_cert_verify": MOCK_SAT6_SOURCE["ssl_cert_verify"]},
            port=443,
            client=client,
        )
        p._id = MOCK_SAT6_SOURCE["id"]
        self.assertTrue(p.equivalent(MOCK_SAT6_SOURCE))
        self.assertTrue(p.equivalent(p))
        with self.assertRaises(TypeError):
            p.equivalent([])


class ScanTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    def test_equivalent(self):
        """If a hostname is specified in the config file, we use it."""
        client = api.Client(authenticate=False, config=CAMAYOC_CONFIG)
        scn = Scan(source_ids=[153], scan_type="inspect", name=MOCK_SCAN["name"], client=client)
        scn._id = MOCK_SCAN["id"]
        self.assertTrue(scn.equivalent(MOCK_SCAN))
        self.assertTrue(scn.equivalent(scn))
        with self.assertRaises(TypeError):
            scn.equivalent([])


class ScanJobTestCase(unittest.TestCase):
    """Test :mod:camayoc.api."""

    def test_create(self):
        """If a hostname is specified in the config file, we use it."""
        client = api.Client(authenticate=False, config=CAMAYOC_CONFIG)
        job = ScanJob(scan_id=1, client=client)
        job._id = 1
        correct_payload = {"scan_id": 1}
        self.assertEqual(job.payload(), correct_payload)
        with self.assertRaises(NotImplementedError):
            job.equivalent({})
