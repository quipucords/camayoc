# coding=utf-8
"""Tests for UI login and logout.

:caseautomation: automated
:casecomponent: ui
:caseimportance: high
:caselevel: integration
:requirement: Sonar
:testtype: functional
:upstream: yes
"""
import pytest

from .views import DashboardView, LoginView


@pytest.mark.driver
def test_login_logout(browser):
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
    login = LoginView(browser)
    login.username.fill('admin')
    login.password.fill('pass')
    login.login.click()

    assert browser.selenium.title == 'Red Hat Entitlements Reporting'

    dashboard = DashboardView(browser)
    dashboard.user_dropdown.select_item('Logout')

    login.login.wait_displayed()
