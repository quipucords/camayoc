# coding=utf-8
"""Tests for the ``Credential`` API endpoint.

:caseautomation: automated
:casecomponent: api
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import requests

import pytest

from camayoc.constants import (
    QCS_HOST_MANAGER_TYPES,
    QCS_BECOME_METHODS,
)
from camayoc.qcs_models import Credential
from camayoc.utils import uuid4


@pytest.mark.parametrize('method', QCS_BECOME_METHODS)
@pytest.mark.parametrize('cred_type', QCS_HOST_MANAGER_TYPES)
def test_negative_create_with_become(
        cred_type, shared_client, cleanup, method):
    """Attempt to pass 'become' options to host manager credentials.

    :id: d04e3e1b-c7f1-4cc2-a4a4-a3d3317f95ce
    :description: Attempt to pass 'become' options that are only valid for
        network credentials to create host manager credentials.
    :steps: Attempt to create a host manager credential sending valid data
        along with the extra invalid become options.
    :expectedresults: An error is thrown and no new credential is created.
    """
    cred = Credential(
        cred_type=cred_type,
        client=shared_client,
        password=uuid4(),
        become_method=method,
        become_password=uuid4(),
        become_user=uuid4(),
    )
    with pytest.raises(requests.HTTPError):
        cred.create()
        cleanup.append(cred)
