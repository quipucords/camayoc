# coding=utf-8
"""Unit tests for :mod:`camayoc.utils`."""
from unittest import mock

import pytest

from camayoc import exceptions, utils


def test_get_qcs_url():
    """Test ``camayoc.utils.get_qcs_url``."""
    with mock.patch('camayoc.utils.get_config') as get_config:
        get_config.return_value = {
            'qcs': {
                'hostname': 'server.example.com',
                'https': True,
                'port': 443,
            }
        }
        assert utils.get_qcs_url() == 'https://server.example.com:443'


def test_get_qcs_url_no_hostname():
    """Test ``camayoc.utils.get_qcs_url`` when no hostname is present."""
    with mock.patch('camayoc.utils.get_config') as get_config:
        get_config.return_value = {
            'qcs': {
                'https': True,
                'port': 443,
            }
        }
        with pytest.raises(exceptions.QCSBaseUrlNotFound) as err:
            utils.get_qcs_url()
        assert (
            'Make sure you have a "qcs" section and `hostname`is specified in '
            'the camayoc config file'
        ) in str(err)
