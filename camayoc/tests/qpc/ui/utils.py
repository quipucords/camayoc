# coding=utf-8
"""Utility class for UI tests."""

from selenium.common.exceptions import NoSuchElementException, \
        StaleElementReferenceException

from smartloc import Locator

from widgetastic.widget import GenericLocatorWidget, TextInput


def fill(view, xpath_locator, text):
    """Fill in a textbox using a xpath locator."""
    TextInput(view, locator=Locator(xpath=xpath_locator)).fill(text)


def clear_toasts(view, count=1):
    """Attempt to flush any confirmation dialogs that may have appeared.

    Use this function to clear out dialogs that may be preventing buttons
    from being clicked properly. Sometimes it might need to be
    used in succession.
    """
    for i in range(count):
        try:
            view.wait_for_element(locator=Locator(css='.close'))
            GenericLocatorWidget(view, locator=Locator(css='.close')).click()
        except (NoSuchElementException, StaleElementReferenceException):
            break
