"""Test utilities for quipucords' UI tests."""
import pytest

from widgetastic.browser import Browser

from camayoc.utils import get_qpc_url


def pytest_configure(config):
    """Check for presence of driver for selenium."""
    if not config.option.driver:
        setattr(config.option, 'markexpr', 'not driver')


@pytest.mark.driver
@pytest.fixture
def browser(selenium):
    """Widgetastic browser fixture."""
    selenium.get(get_qpc_url())
    return Browser(selenium)
