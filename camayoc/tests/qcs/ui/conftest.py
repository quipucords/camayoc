"""Test utilities for quipucords' UI tests."""
import pytest

from widgetastic.browser import Browser

from camayoc.utils import get_qcs_url


@pytest.fixture
def browser(selenium):
    """Widgetastic browser fixture."""
    selenium.get(get_qcs_url())
    return Browser(selenium)
