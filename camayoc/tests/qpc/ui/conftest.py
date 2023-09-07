"""Test utilities for quipucords' UI tests."""

import pytest

from camayoc import config
from camayoc.tests.qpc.cli.utils import clear_all_entities
from camayoc.ui import Client as UIClient
from camayoc.ui.session import BasicSession


def pytest_exception_interact(node, call, report):
    ui_client = node.funcargs.get("ui_client", None)
    if not ui_client:
        return
    print("List of previous successfull actions:")
    zeroes = len(str(len(ui_client.session.history)))
    for step, record in enumerate(ui_client.session.history):
        step_num = str(step).zfill(zeroes)
        print(f"{step_num}: {record}")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    extra_context_args = {}
    verify_ssl = config.get_config().get("qpc", {}).get("ssl-verify", False)
    if not verify_ssl:
        extra_context_args["ignore_https_errors"] = True

    return {**browser_context_args, **extra_context_args}


@pytest.fixture(scope="module")
def data_provider(data_provider):
    data_provider.cleanup()
    clear_all_entities()
    return data_provider


@pytest.fixture
def ui_client(page):
    client_session = BasicSession()
    client = UIClient(driver=page, session=client_session)
    yield client
