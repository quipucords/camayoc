# coding=utf-8
"""Utility class for UI tests."""

from selenium.common.exceptions import NoSuchElementException, \
        StaleElementReferenceException

from smartloc import Locator

from widgetastic.widget import GenericLocatorWidget, TextInput


def fill(view, xpath_locator, text):
    """Fill in a textbox using a xpath locator."""
    TextInput(view, locator=Locator(xpath=xpath_locator)).fill(text)


def field_xpath(label, textarea=False):
    """Build an xpath for selecting a form field based on its label."""
    if textarea:
        return '//textarea[ancestor::node()[2]/label[text() = "' + \
                label + '"]]'
    else:
        return '//input[ancestor::node()[2]/label[text() = "' + label + '"]]'


def radio_xpath(label):
    """Build an xpath for selecting a radio button based on its label."""
    return '//label[text()="' + label + '"]'


def clear_toasts(view, count=20):
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
