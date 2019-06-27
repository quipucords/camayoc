"""Starting tests for configs"""

import requests

from camayoc.tests.qpc.yupana.utils import yupana_configs, get_api_url


EXPECTED_CONFIGS = ("app_name", "openshift_project", "openshift_app_domain", "api_path")


def test_config():
    """test load configurations"""
    config = yupana_configs()
    assert config != []
    assert sorted(set(config.keys())) == sorted(EXPECTED_CONFIGS)


def test_connect():
    """Test the connection to the desired cluster."""
    request = requests.get(get_api_url() + "status/")
    assert request.status_code == 200
