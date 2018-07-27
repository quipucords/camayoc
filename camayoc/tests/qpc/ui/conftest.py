"""Test utilities for quipucords' UI tests."""
import pytest

from selenium import webdriver

from widgetastic.browser import Browser

from camayoc.utils import get_qpc_url, uuid4

from .utils import create_credential, delete_credential
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


@pytest.fixture(scope='module')
def browser(request):
    """Selenium instance."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--allow-insecure-localhost')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(get_qpc_url())
    driver.set_window_size(1200, 800)
    yield Browser(driver)
    driver.close()


@pytest.fixture(scope='module')
def qpc_login(browser):
    """Log the user into the dashboard."""
    login = LoginView(browser)
    login.username.fill('admin')
    login.password.fill('pass')
    login.login.click()
    assert browser.selenium.title == 'Red Hat Entitlements Reporting'


@pytest.fixture(scope='module')
def credentials(browser, qpc_login):
    """Allocate dummy credentials to be used with sources.

    Yields a dict of the name of a network, Satellite, and vCenter
    credential for use with sources.
    """
    # Credential type is a case-sensitive parameter and matches UI text
    names = {
        'Network': uuid4(),
        'Satellite': uuid4(),
        'VCenter': uuid4()
        }
    username = uuid4()
    password = uuid4()

    options = {
        'name': (names['Network']),
        'username': username,
        'password': password,
        'credential_type': 'Network'
    }
    create_credential(browser, options)
    options['name'] = names['Satellite']
    options['credential_type'] = 'Satellite'
    create_credential(browser, options)
    options['name'] = names['VCenter']
    options['credential_type'] = 'VCenter'
    create_credential(browser, options)
    yield names
    delete_credential(browser, set(names.values()))
