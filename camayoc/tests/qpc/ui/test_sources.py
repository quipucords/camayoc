# coding=utf-8
"""Test for handling sources in the UI.

:caseautomation: automated
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

    :id: b1f64fd6-0421-4650-aa6d-149cb3099012
    :description: Creates a source in the UI.
    :steps: TODO
    :expectedresults: TODO
    """
    dash = DashboardView(browser)
    dash.nav.select('Sources')
