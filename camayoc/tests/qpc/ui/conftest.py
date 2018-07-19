"""Test utilities for quipucords' UI tests."""
import pytest

from widgetastic.browser import Browser

from camayoc.utils import get_qpc_url

from .views import LoginView


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
def selenium(selenium):
    """Override pytest-selenium default by changing the browser window size."""
    selenium.set_window_size(1200, 800)
    return selenium


@pytest.fixture
def browser(selenium):
    """Widgetastic browser fixture."""
    selenium.get(get_qpc_url())
    return Browser(selenium)


@pytest.fixture
def chrome_options(chrome_options):
    """Set options if using a chrome webdriver.

    By default testing is done in headless mode.
    """
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--allow-insecure-localhost')
    return chrome_options


@pytest.fixture
def qpc_login(browser):
    """Log the user into the dashboard."""
    login = LoginView(browser)
    login.username.fill('admin')
    login.password.fill('pass')
    login.login.click()

    assert browser.selenium.title == 'Red Hat Entitlements Reporting'
