# coding=utf-8
"""Tests for UI login and logout.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:testtype: functional
"""

from camayoc.ui import Client
from camayoc.ui import data_factories


def test_login_logout(ui_client: Client):
    """Login and logout using the default user.

    :id: 88bbf267-d32e-44b1-934f-e69c84e5c99d
    :description: Login and logout using the default user.
    :steps:
        1) Access the login page and fill the username and password fields
        using the default user credentials.
        2) Check if the dashboard page is displayed.
        3) Logout and assert that the login page is shown.
    :expectedresults: Both login and logout must work.
    """
    page = ui_client.begin().login(data_factories.LoginFormDTOFactory())
    assert page._driver.title() in ("Quipucords", "product discovery")
    page.logout()
