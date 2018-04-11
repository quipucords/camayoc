"""Test utilities for quipucords' UI tests."""
import pytest

from widgetastic.browser import Browser

from camayoc.utils import get_qpc_url


def pytest_collection_modifyitems(config, items):
    """Check for presence of driver for selenium.

    If no driver option is present then UI test should be skipped.
    UI tests should be marked with @pytest.mark.ui
    """
    if not config.getoption('--driver', None):
        skip_ui = pytest.mark.skip(
            reason='need --driver option to run UI tests')
        for item in items:
            if 'ui' in item.fspath.strpath:
                item.add_marker(skip_ui)


@pytest.fixture
def browser(selenium):
    """Widgetastic browser fixture."""
    selenium.get(get_qpc_url())
    return Browser(selenium)
