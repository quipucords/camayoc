"""Test utilities for quipucords' UI tests."""
import pytest

from widgetastic.browser import Browser

from camayoc.utils import get_qpc_url


@pytest.fixture
def browser(selenium):
    """Widgetastic browser fixture."""
    selenium.get(get_qpc_url())
    return Browser(selenium)
