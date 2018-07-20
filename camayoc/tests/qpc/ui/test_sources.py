# coding=utf-8
"""Test for handling sources in the UI.

caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import pytest

from .views import DashboardView


@pytest.mark.skip(reason='Test stub')
def test_create_source(browser):
    """Create a source through the UI.

    :id:
    :description:
    :steps:
    :expectedresults:
    """
    dash = DashboardView(browser)
    dash.nav.select('Sources')
