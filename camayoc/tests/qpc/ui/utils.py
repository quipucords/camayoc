# coding=utf-8
"""Utility class for UI tests."""

from selenium.common.exceptions import NoSuchElementException \
        as NoSuchElement, StaleElementReferenceException as StaleElement

from smartloc import Locator

from widgetastic.widget import GenericLocatorWidget as LocWidget, TextInput


def fill(view, css_locator, text):
    """Fill in text with a CSS locator."""
    TextInput(view, locator=Locator(css=css_locator)).fill(text)


def clear_toasts(view, count=1):
    """Attempt to flush any confirmation dialogs that may have appeared."""
    for i in range(count):
        try:
            view.wait_for_element(locator=Locator(css='.close'))
            LocWidget(view, locator=Locator(css='.close')).click()
        except (NoSuchElement, StaleElement) as e:
            break
