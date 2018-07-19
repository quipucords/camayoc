# coding=utf-8
"""Utility class for UI tests."""

from smartloc import Locator


from widgetastic.widget import TextInput


def fill(view, css_locator, text):
    """Fill in text with a CSS locator."""
    TextInput(view, locator=Locator(css=css_locator)).fill(text)
