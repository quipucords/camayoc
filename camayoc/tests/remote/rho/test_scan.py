# coding=utf-8
"""Tests for ``rho scan`` commands.

These tests are parametrized on the profiles listed in the config file. If scan
is successful, all facts will be validated before test fails, and then all
failed facts will be reported with associated host.

:caseautomation: automated
:casecomponent: cli
:caseimportance: high
:caselevel: integration
:requirement: Rho
:testtype: functional
:upstream: yes
"""

import pytest

from camayoc import config
from camayoc.exceptions import ConfigFileNotFoundError
from camayoc.constants import RHO_PRIVILEGED_FACTS


def profiles():
    """Gather profiles from config file."""
    try:
        profs = config.get_config()['rho']['profiles']
    except ConfigFileNotFoundError:
        profs = []
    return profs


@pytest.mark.facts_needed
@pytest.mark.parametrize('fact', profiles())
def test_facts(fact):
    """Test each fact from the scan reports.

    :id: d9eb29bd-1b61-421a-b680-f494e868b11e
    :description: Test the facts from a scan report
    :steps: For each fact collected, assert it is as expected
    :expectedresults:
        The fact will contain expected data based on privilege level of
        credentials used to acquire it.
    """
    if fact['fact'] not in RHO_PRIVILEGED_FACTS:
        assert fact['expected'] == fact['actual']

    if fact['privileged'] and fact['fact'] in RHO_PRIVILEGED_FACTS:
        assert fact['expected'] == fact['actual']

    if fact['fact'] in RHO_PRIVILEGED_FACTS and not fact['privileged']:
        assert fact['actual'] in RHO_PRIVILEGED_FACTS[fact['fact']]['denials']
